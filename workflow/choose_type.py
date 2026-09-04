#!/usr/bin/env python3
"""Étape 2 du flux de téléchargement : choix du format (SVG ou PNG).

L'icône choisie arrive via les variables Alfred (icon_id, icon_term) posées
par search.py ; ce menu ne fait que poser filetype pour l'objet Conditional.
"""

import json
import os
import sys

from i18n import t


def main():
    term = os.environ.get("icon_term") or "?"
    items = [
        {
            "uid": "svg",
            "title": "SVG",
            "subtitle": t("ui_type_svg_sub", term),
            "arg": "",
            "valid": True,
            "variables": {"filetype": "svg"},
        },
        {
            "uid": "png",
            "title": "PNG",
            "subtitle": t("ui_type_png_sub", term),
            "arg": "",
            "valid": True,
            "variables": {"filetype": "png"},
        },
    ]
    json.dump({"items": items}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
