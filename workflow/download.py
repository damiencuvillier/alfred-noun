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
import subprocess
import sys
import time

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


def clip_dir():
    """Sous-dossier de cache pour les fichiers posés sur le presse-papiers :
    doit rester sur disque (une référence fichier, pas son contenu, y est
    copiée), donc purgé plutôt que supprimé aussitôt comme un tmp classique."""
    path = os.path.join(nplib.cache_dir(), "clip")
    os.makedirs(path, exist_ok=True)
    cutoff = time.time() - 86400
    try:
        for name in os.listdir(path):
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate) and os.path.getmtime(candidate) < cutoff:
                os.remove(candidate)
    except OSError:
        pass
    return path


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


def rasterize_svg(svg_bytes, size):
    """Convertit un SVG (déjà nettoyé) en PNG via sips, à la taille cible.
    Rendu vectoriel natif : remplace le recadrage par pixels du PNG brut du
    site — plus fiable, la bande d'attribution n'existe simplement plus
    dans la source plutôt que d'être devinée sur l'image finale."""
    tmp_svg = os.path.join(nplib.cache_dir(), "raster-%d.svg" % os.getpid())
    tmp_png = os.path.join(nplib.cache_dir(), "raster-%d.png" % os.getpid())
    try:
        with open(tmp_svg, "wb") as handle:
            handle.write(svg_bytes)
        subprocess.run(
            [
                "/usr/bin/sips",
                "-s", "format", "png",
                "-Z", str(size),
                tmp_svg,
                "--out", tmp_png,
            ],
            capture_output=True,
            timeout=30,
        )
        with open(tmp_png, "rb") as handle:
            return handle.read()
    finally:
        for path in (tmp_svg, tmp_png):
            try:
                os.remove(path)
            except OSError:
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


def copy_file_to_clipboard(path):
    """Place une référence fichier — pas son contenu — dans le presse-papiers :
    coller ailleurs (Finder, Figma, Slack…) donne le fichier lui-même."""
    result = subprocess.run(
        [
            "osascript",
            "-e",
            "set the clipboard to (POSIX file %s)" % _applescript_string(path),
        ],
        capture_output=True,
        timeout=15,
    )
    return result.returncode == 0


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


def process_png_file(path):
    """Ajuste le PNG à la taille cible (no-op si le nettoyage via SVG l'a
    déjà rasterisé à la bonne taille) ; appelé identiquement par save et par
    clip pour garantir un résultat identique entre les deux."""
    resize_png_file(path, png_size())


def copy_svg_blob(blob, stem):
    """Écrit le SVG (nettoyé) dans le cache et place une référence fichier
    dans le presse-papiers — coller ailleurs donne un vrai fichier .svg, pas
    son code source."""
    path = unique_path(clip_dir(), stem, "svg")
    with open(path, "wb") as handle:
        handle.write(blob)
    return copy_file_to_clipboard(path)


def copy_png_blob(blob, term):
    """Place l'image PNG (nettoyée/redimensionnée) dans le presse-papiers."""
    tmp = os.path.join(nplib.cache_dir(), "clip-%d.png" % os.getpid())
    try:
        with open(tmp, "wb") as handle:
            handle.write(blob)
        process_png_file(tmp)
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
                if fmt == "png" and strip_enabled():
                    # Repart du SVG (nettoyage fiable, structurel) plutôt que
                    # de deviner la bande d'attribution sur les pixels du PNG.
                    if "svg" not in image_cache:
                        image_cache["svg"] = strip_svg_attribution(
                            fetch_image(icon_id, "svg")
                        )
                    image_cache["png"] = rasterize_svg(
                        image_cache["svg"], png_size()
                    )
                else:
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
                    if copy_svg_blob(blob, stem_base):
                        messages.append(t("svg_copied", term))
                    else:
                        print(t("copy_failed"))
                        sys.exit(1)
            else:
                if directory is None:
                    directory = target_directory()
                path = save_bytes(blob, directory, stem_base, fmt)
                if fmt == "png":
                    process_png_file(path)
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
