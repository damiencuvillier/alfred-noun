#!/usr/bin/env python3
"""Étape 3 du flux de téléchargement PNG : choix de la taille.

Tailles prédéfinies (la valeur de configuration np_png_size est marquée
« défaut ») ; taper un nombre propose une taille personnalisée (20-1200 px,
bornes de l'export du site).
"""

import json
import os
import re
import sys

from i18n import t

PRESETS = ["128", "256", "512", "1024", "1200"]


def size_item(size, subtitle, uid=None):
    item = {
        "title": "%s px" % size,
        "subtitle": subtitle,
        "arg": str(size),
        "valid": True,
        "variables": {"png_size_override": str(size)},
    }
    if uid:
        item["uid"] = uid
    return item


def main():
    query = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    term = os.environ.get("icon_term") or "?"
    default = (os.environ.get("np_png_size") or "512").strip()

    items = []
    digits = re.sub(r"\D", "", query)
    custom = None
    if digits:
        custom = str(max(20, min(1200, int(digits[:4]))))
        items.append(size_item(custom, t("ui_size_custom_sub", term)))
    for preset in PRESETS:
        if preset == custom:
            continue
        label = t("ui_size_preset_sub", preset, term)
        if preset == default:
            label += t("ui_size_default_suffix")
        items.append(size_item(preset, label, uid="size-%s" % preset))
    json.dump({"items": items}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
