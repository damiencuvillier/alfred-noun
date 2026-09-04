#!/usr/bin/env python3
"""Action Alfred : exécute un « plan » d'actions sur une icône The Noun Project.

Un plan est une séquence d'étapes « verbe:cible » jointes par « + » :
  verbe  : save (fichier dans le dossier) ou clip (presse-papiers)
  cible  : def (format par défaut), alt (l'autre format), svg, png,
           txt (la mention d'attribution)
Exemples — ⏎ « save:def » ; ⌘⌥⌃⏎ « save:def+save:alt+save:txt » ;
⌘⌥⇧⌃⏎ « clip:txt+clip:alt+clip:def » (copies successives : l'historique du
presse-papiers les garde toutes, la dernière reste active).

Le plan vient des utilitaires Arg&Vars du workflow (un par combinaison de
modificateurs) ; le flux « Options… » (choix format/taille/dossier) pose
filetype/action à l'ancienne et est converti en plan d'une étape.

Backend « browser » (démon Playwright, session du compte) ou « api »
(API officielle v2). Le stdout alimente la notification macOS (i18n).
"""

import base64
import binascii
import os
import re
import struct
import subprocess
import sys
import time
import zlib

import browser
import nplib
from i18n import t

WORKFLOW_DIR = os.path.dirname(os.path.abspath(__file__))


def default_format():
    fmt = (os.environ.get("np_default_format") or "svg").strip().lower()
    return fmt if fmt in ("svg", "png") else "svg"


def alt_format():
    return "png" if default_format() == "svg" else "svg"


def resolve_target(target):
    """def/alt/svg/png/txt → svg/png/txt."""
    target = (target or "").strip().lower()
    if target == "def":
        return default_format()
    if target == "alt":
        return alt_format()
    if target in ("svg", "png", "txt"):
        return target
    return default_format()


def slugify(text):
    slug = re.sub(r"[^\w\-]+", "-", text, flags=re.UNICODE).strip("-").lower()
    # Le term vient du site : borner pour rester sous la limite de nom APFS
    return slug[:100] or "icone"


def unique_path(directory, stem, extension):
    candidate = os.path.join(directory, "%s.%s" % (stem, extension))
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, "%s-%d.%s" % (stem, counter, extension))
        counter += 1
    return candidate


def pbcopy(data):
    """pbcopy avec locale UTF-8 forcée : l'environnement d'Alfred n'a pas de
    LANG et pbcopy interpréterait les octets UTF-8 en MacRoman (mojibake)."""
    env = dict(os.environ, LANG="en_US.UTF-8")
    return subprocess.run(["pbcopy"], input=data, env=env).returncode == 0


def strip_enabled():
    return (os.environ.get("np_strip_attribution") or "1") == "1"


def _format_number(value):
    return "%d" % value if float(value).is_integer() else "%s" % value


def strip_svg_attribution(blob):
    """Nettoie la bande d'attribution des SVG Noun Project.

    Deux variantes servies par le site :
    - fichiers gratuits : <text>Created by …</text> incrusté + zone agrandie ;
    - fichiers de compte abonné : pas de texte, mais la zone reste agrandie
      de 25 % en bas (viewBox H = 1,25 × hauteur réelle, que trahit
      l'attribut style enable-background:new 0 0 W H).
    """
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        return blob
    cleaned, removed = re.subn(
        r"<text\b[^>]*>.*?</text>", "", text, flags=re.DOTALL | re.IGNORECASE
    )

    background = re.search(
        r"enable-background\s*:\s*new\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
        cleaned,
    )
    viewbox = re.search(r'(viewBox=["\'])([^"\']+)(["\'])', cleaned)
    target_height = None
    dims = None
    if viewbox:
        numbers = viewbox.group(2).replace(",", " ").split()
        try:
            dims = tuple(float(n) for n in numbers)
        except ValueError:
            dims = None
    if dims and len(dims) == 4:
        x, y, width, height = dims
        if background:
            bg_width = float(background.group(3))
            bg_height = float(background.group(4))
            if (
                bg_width > 0
                and abs(width - bg_width) <= 0.02 * max(width, 1)
                and abs(height - 1.25 * bg_height) <= 0.02 * max(bg_height, 1)
            ):
                target_height = bg_height
        if (
            target_height is None
            and removed
            and width > 0
            and abs(height - 1.25 * width) <= 0.02 * width
        ):
            # Icône carrée : sans indice enable-background, on ne referme la
            # zone que si un texte a bien été retiré (preuve de la bande).
            target_height = width

    if target_height is not None:
        replacement = "%s%s %s %s %s%s" % (
            viewbox.group(1),
            _format_number(x),
            _format_number(y),
            _format_number(width),
            _format_number(target_height),
            viewbox.group(3),
        )
        cleaned = cleaned[: viewbox.start()] + replacement + cleaned[viewbox.end():]

        svg_tag = re.search(r"<svg\b[^>]*>", cleaned, flags=re.IGNORECASE)
        if svg_tag:
            tag = svg_tag.group(0)
            width_attr = re.search(r'width=["\']([\d.]+)(?:px)?["\']', tag)
            height_attr = re.search(r'height=["\']([\d.]+)(?:px)?["\']', tag)
            if width_attr and height_attr and width > 0:
                attr_width = float(width_attr.group(1))
                attr_height = float(height_attr.group(1))
                old_ratio_height = attr_width * height / width
                # N'ajuste l'attribut height que s'il suivait l'ancien viewBox
                if abs(attr_height - old_ratio_height) <= 0.02 * max(attr_height, 1):
                    new_height = attr_width * target_height / width
                    tag = (
                        tag[: height_attr.start(1)]
                        + _format_number(round(new_height, 2))
                        + tag[height_attr.end(1):]
                    )
                    cleaned = (
                        cleaned[: svg_tag.start()] + tag + cleaned[svg_tag.end():]
                    )

    if not removed and target_height is None:
        return blob
    return cleaned.encode("utf-8")


def _png_alpha_rows(blob):
    """Décode un PNG 8 bits non entrelacé avec canal alpha (RGBA ou gris+alpha)
    et retourne (fraction de pixels opaques par ligne, largeur, hauteur).
    (None, w, h) si le format n'est pas géré — on ne rogne alors pas."""
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        return None, 0, 0
    pos = 8
    width = height = 0
    bit_depth = color_type = interlace = None
    idat = b""
    while pos + 8 <= len(blob):
        (length,) = struct.unpack(">I", blob[pos:pos + 4])
        tag = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", data
            )
        elif tag == b"IDAT":
            idat += data
        elif tag == b"IEND":
            break
        pos += 12 + length
    if not width or bit_depth != 8 or interlace != 0 or color_type not in (4, 6):
        return None, width, height
    channels = 2 if color_type == 4 else 4
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        return None, width, height
    stride = width * channels
    if len(raw) < height * (stride + 1):
        return None, width, height
    sample_step = max(1, width // 64)
    fractions = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        line = bytearray(raw[offset:offset + stride])
        offset += stride
        if filter_type == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = prev[i]
                corner = prev[i - channels] if i >= channels else 0
                p = left + up - corner
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - corner)
                if pa <= pb and pa <= pc:
                    pred = left
                elif pb <= pc:
                    pred = up
                else:
                    pred = corner
                line[i] = (line[i] + pred) & 0xFF
        prev = line
        alphas = line[channels - 1::channels][::sample_step]
        opaque = sum(1 for value in alphas if value > 15)
        fractions.append(opaque / max(1, len(alphas)))
    return fractions, width, height


def _png_keep_height(blob):
    """Hauteur à conserver pour retirer la bande d'attribution, 0 = ne pas
    toucher. Deux motifs Noun Project :
    - carré + bande (H ≈ 1,25 × L) : texte clairsemé ou bande vide en bas ;
    - non carré (abonné) : bande basse transparente, H ≈ 1,25 × contenu.
    Garde-fou : une bande dense (> 20 % opaque) est du vrai contenu."""
    rows, width, height = _png_alpha_rows(blob)
    if not rows:
        return 0
    if round(width * 1.18) <= height <= round(width * 1.32):
        band = rows[width:]
        if band and sum(band) / len(band) <= 0.2:
            return width
        return 0
    y = height - 1
    while y >= 0 and rows[y] == 0:
        y -= 1
    content = y + 1
    if (
        content
        and height - content >= 0.1 * height
        and abs(height - 1.25 * content) <= 0.04 * height
    ):
        return content
    return 0


def crop_png_file(path):
    """Rogne la bande d'attribution d'un PNG (analyse Python, rognage
    CoreGraphics via crop-image.js). Silencieux : un échec laisse le fichier
    d'origine."""
    if not strip_enabled():
        return
    try:
        with open(path, "rb") as handle:
            blob = handle.read()
        keep = _png_keep_height(blob)
    except Exception:
        return
    if not keep:
        return
    script = os.path.join(WORKFLOW_DIR, "crop-image.js")
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", script, path, str(keep)],
            capture_output=True,
            timeout=30,
        )
    except Exception:
        pass


def resize_png_file(path, target):
    """Ramène le PNG à la taille demandée (plus grand côté = target).
    Le site ignore exportSize et sert un master (~700 px) : c'est ici que la
    promesse de taille de l'interface est tenue."""
    if not target:
        return
    try:
        probe = subprocess.run(
            ["/usr/bin/sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        dims = [int(v) for v in re.findall(r"pixel(?:Width|Height): (\d+)", probe.stdout)]
        if dims and max(dims) == target:
            return
        subprocess.run(
            ["/usr/bin/sips", "-Z", str(target), path],
            capture_output=True,
            timeout=20,
        )
    except Exception:
        pass


def _applescript_string(value):
    return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')


def pick_and_store_default_dir():
    """Boîte de dialogue « choisir un dossier », persisté comme défaut du
    workflow via l'API AppleScript d'Alfred. Retourne le chemin, ou None."""
    try:
        picked = subprocess.run(
            [
                "osascript",
                "-e",
                'POSIX path of (choose folder with prompt '
                '"Dossier de téléchargement The Noun Project")',
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except Exception:
        return None
    if picked.returncode != 0:
        return None
    path = picked.stdout.strip().rstrip("/")
    if not path:
        return None
    bundle = (
        os.environ.get("alfred_workflow_bundleid")
        or "com.damiencuvillier.alfred.nounproject"
    )
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application id "com.runningwithcrayons.Alfred" to '
            "set configuration %s to value %s in workflow %s exportable true"
            % (
                _applescript_string("np_download_dir"),
                _applescript_string(path),
                _applescript_string(bundle),
            ),
        ],
        capture_output=True,
        timeout=15,
    )
    return path


def decode_base64(encoded):
    try:
        blob = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        blob = b""
    if not blob:
        print(t("corrupt"))
        sys.exit(1)
    return blob


def png_size():
    # png_size_override vient du menu de choix de taille (choose_size.py) ;
    # np_png_size est la valeur par défaut de la configuration.
    for source in (os.environ.get("png_size_override"), os.environ.get("np_png_size")):
        size = (source or "").strip()
        if size.isdigit():
            # Bornes de l'API officielle : 20 à 1200 px ; le site accepte pareil
            return max(20, min(1200, int(size)))
    return 512


def color_param():
    color = (os.environ.get("np_color") or "").strip().lstrip("#")
    if color and re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        return color.upper()
    return ""


# ------------------------------------------------------------- récupération


def fetch_image(icon_id, fmt):
    """Récupère le SVG/PNG (octets bruts) via le backend actif.
    Imprime un message et sort en cas d'échec."""
    backend = (os.environ.get("np_backend") or "browser").strip()
    if backend == "api":
        key, secret = nplib.get_credentials()
        if not key or not secret:
            print(t("api_no_key"))
            sys.exit(1)
        params = {"filetype": fmt}
        if fmt == "png":
            params["size"] = png_size()
        color = color_param()
        if color:
            params["color"] = color
        try:
            data = nplib.api_get(
                "/v2/icon/%s/download" % icon_id, params, key, secret, timeout=30
            )
        except nplib.NounProjectError as err:
            print(t("download_failed", err))
            sys.exit(1)
        encoded = data.get("base64_encoded_file")
        if not encoded:
            print(t("api_no_file"))
            sys.exit(1)
        return decode_base64(encoded)

    state, _ = browser.ensure(WORKFLOW_DIR)
    if state != "ready":
        print(t("daemon_not_ready"))
        sys.exit(1)
    params = {"id": icon_id, "format": fmt.upper()}
    if fmt == "png":
        params["size"] = png_size()
    color = color_param()
    if color:
        params["color"] = color
    try:
        data = browser.call("/download", params, timeout=90)
    except browser.DaemonDown:
        print(t("daemon_gone"))
        sys.exit(1)
    except browser.DaemonError as err:
        if err.auth_required:
            print(t("not_logged_in"))
        else:
            print(t("download_failed", err))
        sys.exit(1)
    encoded = data.get("base64")
    if not encoded:
        print(t("no_file"))
        sys.exit(1)
    return decode_base64(encoded)


# ------------------------------------------------------------------- étapes


def target_directory():
    if os.environ.get("dir_setup") == "1":
        directory = pick_and_store_default_dir()
        if directory is None:
            print(t("cancelled"))
            sys.exit(1)
        return directory
    directory = (os.environ.get("dir_override") or "").strip() or (
        os.environ.get("np_download_dir") or "~/Downloads"
    )
    return os.path.expanduser(directory)


def save_bytes(blob, directory, stem, extension):
    """Écrit le fichier (gestion TCC) et retourne son chemin."""
    try:
        os.makedirs(directory, exist_ok=True)
        path = unique_path(directory, stem, extension)
        with open(path, "wb") as handle:
            handle.write(blob)
        return path
    except OSError as err:
        # Typiquement un refus TCC (Réglages > Confidentialité) sur le dossier
        print(t("write_denied", directory, err.strerror or err))
        sys.exit(1)


def copy_png_blob(blob, term):
    """Place l'image PNG (nettoyée/redimensionnée) dans le presse-papiers."""
    tmp = os.path.join(nplib.cache_dir(), "clip-%d.png" % os.getpid())
    try:
        with open(tmp, "wb") as handle:
            handle.write(blob)
        crop_png_file(tmp)
        resize_png_file(tmp, png_size())
        result = subprocess.run(
            [
                "osascript",
                "-e",
                "set the clipboard to "
                "(read (POSIX file %s) as «class PNGf»)" % _applescript_string(tmp),
            ],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def execute_plan(plan, icon_id, term, attribution):
    """Exécute les étapes du plan ; imprime le récapitulatif final."""
    steps = [step for step in plan.split("+") if step.strip()]
    if not steps:
        steps = ["save:def"]
    directory = None
    stem_base = slugify(term) + ("-%s" % icon_id if icon_id else "")
    image_cache = {}
    messages = []
    saved_paths = []

    for index, step in enumerate(steps):
        verb, _, target = step.partition(":")
        verb = verb.strip().lower()
        fmt = resolve_target(target)

        if fmt == "txt":
            data = attribution.encode("utf-8")
            if verb == "clip":
                if pbcopy(data):
                    messages.append(t("attribution_copied", term))
                else:
                    print(t("copy_failed"))
                    sys.exit(1)
            else:
                if directory is None:
                    directory = target_directory()
                path = save_bytes(data, directory, stem_base, "txt")
                saved_paths.append(path)
                messages.append(t("saved", "TXT", os.path.basename(path)))
        else:
            if fmt not in image_cache:
                blob = fetch_image(icon_id, fmt)
                if fmt == "svg" and strip_enabled():
                    blob = strip_svg_attribution(blob)
                image_cache[fmt] = blob
            blob = image_cache[fmt]
            if verb == "clip":
                if fmt == "png":
                    if copy_png_blob(blob, term):
                        messages.append(t("png_copied", term))
                    else:
                        print(t("copy_failed"))
                        sys.exit(1)
                else:
                    if pbcopy(blob):
                        messages.append(t("svg_copied", term))
                    else:
                        print(t("copy_failed"))
                        sys.exit(1)
            else:
                if directory is None:
                    directory = target_directory()
                path = save_bytes(blob, directory, stem_base, fmt)
                if fmt == "png":
                    crop_png_file(path)
                    resize_png_file(path, png_size())
                saved_paths.append(path)
                messages.append(t("saved", fmt.upper(), os.path.basename(path)))

        # Laisser l'historique du presse-papiers capter chaque copie successive
        if verb == "clip" and index < len(steps) - 1:
            time.sleep(0.8)

    if saved_paths and os.environ.get("np_reveal") == "1":
        subprocess.run(["open", "-R", saved_paths[-1]])
    print(" · ".join(messages))


# -------------------------------------------------------------------- login


def run_login():
    state, _ = browser.ensure(WORKFLOW_DIR)
    if state == "no-node":
        print(t("node_required"))
        sys.exit(1)
    if state in ("installing", "setup-failed"):
        print(t("installing"))
        sys.exit(1)
    if state in ("starting", "failed"):
        print(t("starting_retry"))
        sys.exit(1)
    try:
        # La fenêtre reste ouverte jusqu'à 5 min : timeout client plus large
        result = browser.call("/login", timeout=360)
    except (browser.DaemonDown, browser.DaemonError) as err:
        print(t("login_failed", err))
        sys.exit(1)
    if result.get("loggedIn"):
        print(t("login_ok"))
    else:
        print(t("login_aborted"))
        sys.exit(1)


# --------------------------------------------------------------------- main


def main():
    argument = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    action = os.environ.get("action") or ""

    if action == "login" or argument == "login":
        run_login()
        return

    icon_id = (os.environ.get("icon_id") or "").strip() or argument
    if not icon_id:
        print(t("no_icon"))
        return

    term = os.environ.get("icon_term") or "icone"
    attribution = os.environ.get("icon_attribution") or term

    plan = (os.environ.get("plan") or "").strip()
    if not plan:
        filetype = (os.environ.get("filetype") or "").strip().lower()
        if action == "copyright":
            plan = "clip:txt"
        elif action == "clipboard":
            plan = "clip:%s" % (filetype if filetype in ("svg", "png") else "def")
        elif filetype in ("svg", "png"):
            # Flux « Options… » : format choisi par choose_type.py
            plan = "save:%s" % filetype
        else:
            plan = (os.environ.get("plan_default") or "save:def").strip()

    execute_plan(plan, icon_id, term, attribution)


if __name__ == "__main__":
    main()
