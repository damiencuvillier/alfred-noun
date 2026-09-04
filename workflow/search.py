#!/usr/bin/env python3
"""Script Filter Alfred : recherche d'icônes The Noun Project.

Deux backends, choisis par la variable de configuration np_backend :
- « browser » (défaut) : démon Playwright local (server.mjs) qui utilise la
  session thenounproject.com de l'utilisateur — catalogue complet.
- « api » : API officielle v2 (clé/secret OAuth requis, téléchargements
  limités au domaine public en accès gratuit).
"""

import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

import browser
import nplib
from i18n import t

THUMB_SIZE = 200          # valeurs acceptées par l'API : 42, 84, 200
SEARCH_CACHE_TTL = 600    # secondes — économise le quota en re-navigation
WORKFLOW_DIR = os.path.dirname(os.path.abspath(__file__))
MARKER = "▸"              # préfixe de requête du sous-menu ⇥ d'une icône


PUBLIC_DOMAIN_VALUES = ("License.PUBLICDOMAIN", "public-domain")


def license_label(value):
    if value in PUBLIC_DOMAIN_VALUES:
        return t("ui_pd")
    if value in ("License.CREATIVECOMMONS", "creative-commons-attribution"):
        return "CC BY"
    return ""


def is_public_domain(value):
    return value in PUBLIC_DOMAIN_VALUES


def default_format():
    fmt = (os.environ.get("np_default_format") or "svg").strip().lower()
    return fmt if fmt in ("svg", "png") else "svg"


def alt_format():
    return "png" if default_format() == "svg" else "svg"


def alfred_output(items, cacheable=False, cache_seconds=600, rerun=None):
    payload = {"items": items}
    if cacheable:
        # Cache natif Alfred (5.5+) : évite même de relancer le script,
        # et préserve l'ordre de pertinence du site.
        payload["cache"] = {"seconds": cache_seconds, "loosereload": True}
        payload["skipknowledge"] = True
    if rerun:
        payload["rerun"] = rerun
    json.dump(payload, sys.stdout, ensure_ascii=False)


def message_item(title, subtitle=""):
    return {"title": title, "subtitle": subtitle, "valid": False}


def default_png_size():
    size = (os.environ.get("np_png_size") or "512").strip()
    return size if size.isdigit() else "512"


def default_dir_display():
    directory = os.environ.get("np_download_dir") or "~/Downloads"
    home = os.path.expanduser("~")
    return directory.replace(home, "~", 1) if directory.startswith(home) else directory


def write_meta(entry):
    """Mémorise les métadonnées d'une icône pour le sous-menu ⇥ (qui n'a que
    la requête Alfred comme contexte)."""
    meta_dir = os.path.join(nplib.cache_dir(), "meta")
    os.makedirs(meta_dir, exist_ok=True)
    path = os.path.join(meta_dir, "%s.json" % entry["id"])
    tmp = "%s.%d.tmp" % (path, os.getpid())
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(entry, handle, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass


def read_meta(icon_id):
    try:
        path = os.path.join(nplib.cache_dir(), "meta", "%s.json" % icon_id)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def cached_thumb(icon_id):
    thumbs = os.path.join(nplib.cache_dir(), "thumbs")
    for extension in ("jpg", "png"):
        path = os.path.join(thumbs, "%s.%s" % (icon_id, extension))
        if os.path.exists(path):
            return path
    return None


def fetch_thumbnail(icon_id, url):
    """Télécharge la vignette dans le cache ; retourne le chemin ou None.

    Les vignettes Noun Project sont des glyphes noirs sur fond transparent,
    invisibles sur un thème Alfred sombre : on les aplatit sur fond blanc
    (conversion JPEG via sips). Écritures atomiques (os.replace) car Alfred
    peut tuer le script en pleine frappe.
    """
    if not url:
        return None
    thumbs = os.path.join(nplib.cache_dir(), "thumbs")
    os.makedirs(thumbs, exist_ok=True)
    path = os.path.join(thumbs, "%s.jpg" % icon_id)
    if os.path.exists(path):
        return path
    tmp_png = os.path.join(thumbs, "%s.%d.tmp.png" % (icon_id, os.getpid()))
    tmp_jpg = os.path.join(thumbs, "%s.%d.tmp.jpg" % (icon_id, os.getpid()))
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "alfred-noun-project/2.0"}
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            blob = response.read()
        with open(tmp_png, "wb") as handle:
            handle.write(blob)
        converted = subprocess.run(
            ["/usr/bin/sips", "-s", "format", "jpeg", tmp_png, "--out", tmp_jpg],
            capture_output=True,
            timeout=10,
        )
        if converted.returncode == 0 and os.path.exists(tmp_jpg):
            os.replace(tmp_jpg, path)
        else:
            # Repli : vignette PNG d'origine, transparente mais fonctionnelle
            path = os.path.join(thumbs, "%s.png" % icon_id)
            os.replace(tmp_png, path)
        return path
    except Exception:
        return None
    finally:
        for leftover in (tmp_png, tmp_jpg):
            try:
                os.remove(leftover)
            except OSError:
                pass


def combo_subtitles():
    """Sous-titres des 11 combinaisons de modificateurs (le routage réel se
    fait par les utilitaires Arg&Vars du canvas, pas par ces mods)."""
    DEF = default_format().upper()
    ALT = alt_format().upper()
    return {
        "alt": t("ui_dl", ALT),
        "ctrl": t("ui_dl", "TXT"),
        "shift": t("ui_cp", DEF),
        "shift+alt": t("ui_cp", ALT),
        "shift+ctrl": t("ui_cp", "TXT"),
        "cmd": t("ui_dl", "TXT + " + DEF),
        "cmd+alt": t("ui_dl", "TXT + " + ALT),
        "cmd+shift": t("ui_cp", "TXT → " + DEF),
        "cmd+shift+alt": t("ui_cp", "TXT → " + ALT),
        "cmd+alt+ctrl": t("ui_dl", "%s + %s + TXT" % (DEF, ALT)),
        "cmd+alt+shift+ctrl": t("ui_cp", "TXT → %s → %s" % (ALT, DEF)),
    }


def build_item(entry, thumb_path):
    license_part = " · %s" % entry["license_label"] if entry["license_label"] else ""
    title = entry["term"]
    if entry.get("is_pd"):
        # Étiquette bien repérable pour le domaine public
        title = "🟢 " + title
    item = {
        "uid": entry["id"],
        "title": title,
        "subtitle": t(
            "ui_result_sub", entry["creator"], license_part, default_format().upper()
        ),
        "arg": entry["id"],
        "valid": True,
        "autocomplete": "%s%s|%s" % (MARKER, entry["id"], entry["term"]),
        "variables": {
            "quick": "1",
            "icon_id": entry["id"],
            "icon_term": entry["term"],
            "icon_attribution": entry["attribution"],
        },
        "mods": {
            combo: {"subtitle": subtitle}
            for combo, subtitle in combo_subtitles().items()
        },
        "text": {"copy": entry["attribution"], "largetype": entry["term"]},
    }
    if thumb_path:
        item["icon"] = {"path": thumb_path}
    if entry["permalink"]:
        item["quicklookurl"] = entry["permalink"]
    return item


def submenu_item(title, subtitle, variables, thumb, valid=True, autocomplete=None):
    item = {
        "title": title,
        "subtitle": subtitle,
        "arg": "",
        "valid": valid,
    }
    if variables is not None:
        item["variables"] = variables
    if autocomplete is not None:
        item["autocomplete"] = autocomplete
    if thumb:
        item["icon"] = {"path": thumb}
    return item


def submenu_items(icon_id, term, attribution, thumb):
    """Les 12 actions d'une icône (mêmes plans que les combinaisons de
    modificateurs), plus le flux « Options… » — pour le sous-menu ▸."""
    DEF = default_format().upper()
    ALT = alt_format().upper()
    base = {
        "icon_id": icon_id,
        "icon_term": term,
        "icon_attribution": attribution,
        "quick": "1",
    }

    def line(label, hint, plan):
        return submenu_item(label, t("ui_hint", hint), dict(base, plan=plan), thumb)

    return [
        line(t("ui_dl", DEF), "⏎", "save:def"),
        line(t("ui_dl", ALT), "⌥⏎", "save:alt"),
        line(t("ui_dl", "TXT"), "⌃⏎", "save:txt"),
        line(t("ui_cp", DEF), "⇧⏎", "clip:def"),
        line(t("ui_cp", ALT), "⇧⌥⏎", "clip:alt"),
        line(t("ui_cp", "TXT"), "⇧⌃⏎", "clip:txt"),
        line(t("ui_dl", "TXT + " + DEF), "⌘⏎", "save:txt+save:def"),
        line(t("ui_dl", "TXT + " + ALT), "⌘⌥⏎", "save:txt+save:alt"),
        line(t("ui_cp", "TXT → " + DEF), "⌘⇧⏎", "clip:txt+clip:def"),
        line(t("ui_cp", "TXT → " + ALT), "⌘⇧⌥⏎", "clip:txt+clip:alt"),
        line(
            t("ui_dl", "%s + %s + TXT" % (DEF, ALT)),
            "⌘⌥⌃⏎",
            "save:def+save:alt+save:txt",
        ),
        line(
            t("ui_cp", "TXT → %s → %s" % (ALT, DEF)),
            "⌘⌥⇧⌃⏎",
            "clip:txt+clip:alt+clip:def",
        ),
        submenu_item(
            t("ui_menu_options"),
            t("ui_menu_options_sub"),
            {
                "icon_id": icon_id,
                "icon_term": term,
                "icon_attribution": attribution,
                "action": "save",
                "quick": "",
                "plan": "",
            },
            thumb,
        ),
    ]


def render_submenu(icon_id, term):
    """Sous-menu ⇥ (autocomplete « ▸id|terme ») d'une icône."""
    meta = read_meta(icon_id) or {}
    term = meta.get("term") or term or "icône"
    attribution = meta.get("attribution") or term
    thumb = cached_thumb(icon_id)
    items = submenu_items(icon_id, term, attribution, thumb)
    items.append(
        submenu_item(
            t("ui_menu_back"),
            t("ui_menu_back_sub", term),
            None,
            None,
            valid=False,
            autocomplete=term,
        )
    )
    alfred_output(items)


def login_item():
    return {
        "title": t("ui_login_title"),
        "subtitle": t("ui_login_sub"),
        "arg": "login",
        "valid": True,
        "variables": {
            "action": "login",
            "filetype": "svg",
            "icon_term": "",
            "quick": "1",
        },
    }


def render(entries, prepend=None, cache_seconds=600):
    # Domaine public d'abord (tri stable : la pertinence du site est
    # conservée à l'intérieur de chaque groupe)
    entries = sorted(entries, key=lambda e: 0 if e.get("is_pd") else 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        thumbs = list(
            pool.map(
                lambda entry: fetch_thumbnail(entry["id"], entry["thumbnail_url"]),
                entries,
            )
        )
    for entry in entries:
        write_meta(entry)
    items = [
        build_item(entry, thumb)
        for entry, thumb in zip(entries, thumbs)
    ]
    if prepend:
        items = [prepend] + items
    alfred_output(items, cacheable=True, cache_seconds=cache_seconds)


# ---------------------------------------------------------------- backend API


def cached_api_search(query, params, key, secret):
    cache_root = os.path.join(nplib.cache_dir(), "searches")
    os.makedirs(cache_root, exist_ok=True)
    fingerprint = hashlib.sha1(
        json.dumps([query, params], sort_keys=True).encode()
    ).hexdigest()
    cache_file = os.path.join(cache_root, fingerprint + ".json")
    try:
        if time.time() - os.path.getmtime(cache_file) < SEARCH_CACHE_TTL:
            with open(cache_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except (OSError, ValueError):
        # Fichier absent, illisible ou tronqué (Alfred tue le run précédent
        # pendant la frappe) : on repart de l'API.
        pass
    data = nplib.api_get("/v2/icon", dict(params, query=query), key, secret)
    tmp_file = "%s.%d.tmp" % (cache_file, os.getpid())
    with open(tmp_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False)
    os.replace(tmp_file, cache_file)
    return data


def api_entry(icon):
    permalink = icon.get("permalink") or ""
    if permalink.startswith("/"):
        permalink = "https://thenounproject.com" + permalink
    term = icon.get("term") or "sans titre"
    return {
        "id": str(icon["id"]),
        "term": term,
        "creator": (icon.get("creator") or {}).get("name") or "?",
        "license_label": license_label(icon.get("license_description") or ""),
        "is_pd": is_public_domain(icon.get("license_description") or ""),
        "permalink": permalink,
        "thumbnail_url": icon.get("thumbnail_url") or "",
        "attribution": icon.get("attribution") or term,
    }


def run_api(query, limit, png_size):
    key, secret = nplib.get_credentials()
    if not key or not secret:
        alfred_output([
            message_item(t("ui_api_key_missing"), t("ui_api_key_missing_sub"))
        ])
        return
    params = {"limit": limit, "thumbnail_size": THUMB_SIZE}
    if os.environ.get("np_public_domain") == "1":
        params["limit_to_public_domain"] = 1
    try:
        data = cached_api_search(query, params, key, secret)
    except nplib.NounProjectError as err:
        alfred_output([message_item(t("ui_error_title"), str(err))])
        return
    icons = [icon for icon in (data.get("icons") or []) if icon.get("id")]
    if not icons:
        alfred_output([
            message_item(t("ui_no_results"), t("ui_no_results_sub", query))
        ])
        return
    render([api_entry(icon) for icon in icons])


# ---------------------------------------------------------- backend navigateur


def browser_entry(icon):
    term = icon.get("term") or "sans titre"
    creator = icon.get("creator") or "?"
    permalink = icon.get("permalink") or ""
    return {
        "id": str(icon["id"]),
        "term": term,
        "creator": creator,
        "license_label": license_label(icon.get("license") or ""),
        "is_pd": is_public_domain(icon.get("license") or ""),
        "permalink": permalink,
        "thumbnail_url": icon.get("thumbnail_url") or "",
        # Forme canonique (anglaise) des crédits Noun Project, comme l'API
        "attribution": "%s by %s from Noun Project — %s" % (term, creator, permalink),
    }


def run_browser(query, limit, png_size):
    state, detail = browser.ensure(WORKFLOW_DIR)
    if state == "no-node":
        alfred_output([
            message_item(t("ui_no_node_title"), t("ui_no_node_sub"))
        ])
        return
    if state == "installing":
        alfred_output(
            [
                message_item(
                    t("ui_installing_title"),
                    detail or t("ui_installing_sub"),
                )
            ],
            rerun=2,
        )
        return
    if state == "setup-failed":
        alfred_output([
            message_item(
                t("ui_setup_failed_title"),
                t("ui_setup_failed_sub", detail or "setup.log"),
            )
        ])
        return
    if state == "failed":
        alfred_output([
            message_item(
                t("ui_daemon_failed_title"),
                t("ui_daemon_failed_sub", detail or "daemon.log"),
            )
        ])
        return
    if state == "starting":
        alfred_output(
            [message_item(t("ui_starting_title"), t("ui_starting_sub"))],
            rerun=1,
        )
        return

    try:
        data = browser.call("/search", {"q": query, "limit": limit}, timeout=40)
    except browser.DaemonDown:
        alfred_output(
            [message_item(t("ui_starting_title"), t("ui_starting_sub"))],
            rerun=1,
        )
        return
    except browser.DaemonError as err:
        alfred_output([message_item(t("ui_error_title"), str(err))])
        return

    icons = [icon for icon in (data.get("icons") or []) if icon.get("id")]
    unfiltered_count = len(icons)
    if os.environ.get("np_public_domain") == "1":
        # Filtre domaine public côté client (l'API interne du site n'a pas
        # de paramètre équivalent)
        icons = [icon for icon in icons if is_public_domain(icon.get("license") or "")]
    if not icons:
        if unfiltered_count:
            subtitle = t("ui_no_pd_sub", query, unfiltered_count)
        else:
            subtitle = t("ui_no_results_sub", query)
        alfred_output([message_item(t("ui_no_results"), subtitle)])
        return
    logged_in = bool(data.get("loggedIn"))
    render(
        [browser_entry(icon) for icon in icons],
        prepend=None if logged_in else login_item(),
        # Cache court tant que la session manque : juste après la connexion,
        # l'item « Se connecter » ne doit pas rester affiché 5 minutes.
        cache_seconds=300 if logged_in else 60,
    )


# ---------------------------------------------------------------------- main


def main():
    query = (sys.argv[1] if len(sys.argv) > 1 else "").strip()

    if query.startswith(MARKER):
        # Sous-menu ⇥ : la requête est « ▸<id>|<terme> » (posée par autocomplete)
        icon_id, _, term = query[len(MARKER):].partition("|")
        render_submenu(icon_id.strip(), term.strip())
        return

    if len(query) < 2:
        alfred_output([
            message_item("The Noun Project", t("ui_min_chars"))
        ])
        return

    try:
        limit = max(1, min(50, int(float(os.environ.get("np_limit") or 12))))
    except (ValueError, OverflowError):
        limit = 12
    png_size = os.environ.get("np_png_size") or "512"
    backend = (os.environ.get("np_backend") or "browser").strip()

    if backend == "api":
        run_api(query, limit, png_size)
    else:
        run_browser(query, limit, png_size)


if __name__ == "__main__":
    main()
