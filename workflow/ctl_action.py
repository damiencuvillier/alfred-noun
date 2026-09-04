#!/usr/bin/env python3
"""Actions du panneau « nounctl ». Le stdout alimente la notification,
traduit dans la langue du système (voir i18n.py)."""

import os
import shutil
import subprocess
import sys
import time

import browser
from i18n import t

WORKFLOW_DIR = os.path.dirname(os.path.abspath(__file__))


def wait_ready(seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            return browser.call("/status", timeout=1.5)
        except (browser.DaemonDown, browser.DaemonError):
            time.sleep(1)
    return None


def do_login():
    state, _ = browser.ensure(WORKFLOW_DIR)
    if state == "no-node":
        print(t("node_required"))
        sys.exit(1)
    if state in ("installing", "setup-failed"):
        print(t("installing"))
        sys.exit(1)
    if state in ("starting", "failed") and wait_ready(30) is None:
        print(t("daemon_no_start"))
        sys.exit(1)
    try:
        result = browser.call("/login", timeout=360)
    except (browser.DaemonDown, browser.DaemonError) as err:
        print(t("login_failed", err))
        sys.exit(1)
    if result.get("loggedIn"):
        print(t("login_ok"))
    else:
        print(t("login_aborted"))
        sys.exit(1)


def do_stop():
    try:
        browser.call("/quit", timeout=5)
        print(t("stopped"))
    except (browser.DaemonDown, browser.DaemonError):
        print(t("already_stopped"))


def do_restart():
    try:
        browser.call("/quit", timeout=5)
        time.sleep(1)
    except (browser.DaemonDown, browser.DaemonError):
        pass
    browser.reset_start_guards()
    browser.start_daemon(WORKFLOW_DIR)
    if wait_ready(20):
        print(t("restarted"))
    else:
        print(t("restart_failed"))
        sys.exit(1)


def do_setup():
    if browser.setup_running():
        print(t("setup_already"))
        sys.exit(1)
    base = browser.data_dir()
    for name in (".setup-done", ".setup-failed", "setup.pid"):
        try:
            os.remove(os.path.join(base, name))
        except OSError:
            pass
    shutil.rmtree(os.path.join(base, "node_modules"), ignore_errors=True)
    browser.start_setup(WORKFLOW_DIR)
    print(t("setup_started"))


def do_logs():
    base = browser.data_dir()
    opened = 0
    for name in ("daemon.log", "setup.log"):
        path = os.path.join(base, name)
        if os.path.exists(path):
            subprocess.run(["open", path])
            opened += 1
    if opened:
        print(t("logs_opened", base))
    else:
        subprocess.run(["open", base])
        print(t("logs_none", base))


def main():
    action = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    handlers = {
        "login": do_login,
        "stop": do_stop,
        "restart": do_restart,
        "setup": do_setup,
        "logs": do_logs,
    }
    handler = handlers.get(action)
    if handler is None:
        print(t("unknown_action", action))
        sys.exit(1)
    handler()


if __name__ == "__main__":
    main()
