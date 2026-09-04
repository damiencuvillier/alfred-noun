#!/usr/bin/env python3
"""Étape 4 du flux « Options de téléchargement » : choix du dossier.

Sans saisie : dossier par défaut, définition d'un nouveau défaut (boîte de
dialogue), et invite à taper pour chercher. Avec saisie : recherche Spotlight
de dossiers dans le répertoire personnel.
"""

import json
import os
import re
import subprocess
import sys

from i18n import t

HOME = os.path.expanduser("~")


def display(path):
    return path.replace(HOME, "~", 1) if path.startswith(HOME) else path


def folder_item(title, subtitle, variables, icon_path=None, valid=True):
    item = {
        "title": title,
        "subtitle": subtitle,
        "arg": "",
        "valid": valid,
    }
    if variables is not None:
        item["variables"] = variables
    if icon_path:
        item["icon"] = {"type": "fileicon", "path": icon_path}
    return item


def spotlight_folders(query):
    sanitized = re.sub(r"[\"'\\\\]", "", query).strip()
    if not sanitized:
        return []
    try:
        result = subprocess.run(
            [
                "mdfind",
                "-onlyin",
                HOME,
                "kMDItemContentType == 'public.folder' && "
                "kMDItemFSName == '*%s*'c" % sanitized,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    folders = []
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path or "/." in path or "/Library/" in path:
            continue
        folders.append(path)
        if len(folders) >= 8:
            break
    return folders


def main():
    query = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    default_dir = os.path.expanduser(
        os.environ.get("np_download_dir") or "~/Downloads"
    )

    items = []
    if query:
        for path in spotlight_folders(query):
            items.append(folder_item(
                os.path.basename(path) or path,
                t("ui_dir_here", display(path)),
                {"dir_override": path},
                icon_path=path,
            ))
        if not items:
            items.append(folder_item(
                t("ui_dir_none"),
                t("ui_dir_none_sub", query, display(HOME)),
                None,
                valid=False,
            ))

    items.append(folder_item(
        t("ui_dir_default"),
        t("ui_dir_here", display(default_dir)),
        {},
        icon_path=default_dir,
    ))
    items.append(folder_item(
        t("ui_dir_set_default"),
        t("ui_dir_set_default_sub"),
        {"dir_setup": "1"},
    ))
    if not query:
        items.append(folder_item(
            t("ui_dir_type_hint"),
            t("ui_dir_search_sub", display(HOME)),
            None,
            valid=False,
        ))
    json.dump({"items": items}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
