#!/usr/bin/env python3
"""Script Filter « nounctl » : pilotage du backend navigateur.
Interface traduite dans la langue du système (voir i18n.py)."""

import json
import sys

import browser
from i18n import t


def item(title, subtitle, arg, valid=True):
    return {"title": title, "subtitle": subtitle, "arg": arg, "valid": valid}


def main():
    try:
        status = browser.call("/status", timeout=1.5)
    except (browser.DaemonDown, browser.DaemonError):
        status = None

    items = []
    if status is None:
        items.append(item(
            t("ui_ctl_daemon_stopped"),
            t("ui_ctl_daemon_stopped_sub"),
            "restart",
        ))
        items.append(item(
            t("ui_login_title"),
            t("ui_ctl_login_start_sub"),
            "login",
        ))
    else:
        if status.get("loggedIn"):
            items.append(item(
                t("ui_ctl_connected", status.get("port", "?")),
                t("ui_ctl_connected_sub"),
                "status",
                valid=False,
            ))
            items.append(item(
                t("ui_ctl_relogin"),
                t("ui_ctl_relogin_sub"),
                "login",
            ))
        else:
            items.append(item(
                t("ui_login_title"),
                t("ui_ctl_login_window_sub"),
                "login",
            ))
        items.append(item(
            t("ui_ctl_stop"),
            t("ui_ctl_stop_sub"),
            "stop",
        ))
        items.append(item(
            t("ui_ctl_restart"),
            t("ui_ctl_restart_sub"),
            "restart",
        ))
    items.append(item(
        t("ui_ctl_reinstall"),
        t("ui_ctl_reinstall_sub"),
        "setup",
    ))
    items.append(item(
        t("ui_ctl_logs"),
        t("ui_ctl_logs_sub"),
        "logs",
    ))
    json.dump({"items": items}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
