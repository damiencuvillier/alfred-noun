#!/usr/bin/env python3
"""Client du démon Playwright (backend « navigateur ») du workflow Alfred.

Gère le cycle de vie côté client : détection de l'état (installé, lancé),
déclenchement de l'installation et du démarrage en arrière-plan, et appels
HTTP locaux. Stdlib Python 3.9 uniquement.
"""

import glob
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = "2.3.1"  # doit suivre server.mjs : un démon d'une autre version est relancé
BUNDLE = (
    os.environ.get("alfred_workflow_bundleid")
    or "com.damiencuvillier.alfred.nounproject"
)
EXTRA_PATH = "/opt/homebrew/bin:/usr/local/bin"
MAX_BOOT_FAILURES = 3


class DaemonDown(Exception):
    """Le démon ne répond pas (pas lancé, ou en cours de démarrage)."""


class DaemonError(Exception):
    """Le démon a répondu par une erreur."""

    def __init__(self, message, auth_required=False):
        super().__init__(message)
        self.auth_required = auth_required


def data_dir():
    path = os.environ.get("alfred_workflow_data") or os.path.expanduser(
        "~/Library/Application Support/Alfred/Workflow Data/%s" % BUNDLE
    )
    os.makedirs(path, exist_ok=True)
    return path


def port():
    try:
        return int(os.environ.get("np_port") or 48223)
    except ValueError:
        return 48223


def call(path, params=None, timeout=20, on_port=None):
    url = "http://127.0.0.1:%d%s" % (on_port or port(), path)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            error_body = json.loads(err.read().decode("utf-8"))
        except Exception:
            error_body = {}
        if not isinstance(error_body, dict):
            error_body = {}
        raise DaemonError(
            error_body.get("error") or "erreur démon (HTTP %d)" % err.code,
            auth_required=bool(error_body.get("authRequired")),
        ) from err
    except (urllib.error.URLError, OSError, ValueError) as err:
        raise DaemonDown(str(err)) from err
    if not isinstance(body, dict):
        # Un autre process local squattant le port peut répondre du JSON
        # valide mais imprévu : ne jamais le laisser remonter aux appelants.
        raise DaemonDown("réponse inattendue sur le port %d" % (on_port or port()))
    return body


def find_node():
    """Chemin d'un binaire node : PATH étendu, puis nvm/volta/mise/MacPorts."""
    search_path = EXTRA_PATH + ":" + os.environ.get("PATH", "/usr/bin:/bin")
    for directory in search_path.split(":"):
        candidate = os.path.join(directory, "node")
        if os.access(candidate, os.X_OK):
            return candidate
    home = os.path.expanduser("~")
    candidates = sorted(glob.glob(os.path.join(home, ".nvm/versions/node/*/bin/node")))
    candidates += [
        os.path.join(home, ".volta/bin/node"),
        os.path.join(home, ".local/share/mise/shims/node"),
        "/opt/local/bin/node",
    ]
    for candidate in reversed(candidates):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def _env():
    env = dict(os.environ)
    env["PATH"] = EXTRA_PATH + ":" + env.get("PATH", "/usr/bin:/bin")
    env["NP_DATA_DIR"] = data_dir()
    env["NP_PORT"] = str(port())
    node = find_node()
    if node:
        env["NP_NODE"] = node
        env["PATH"] = os.path.dirname(node) + ":" + env["PATH"]
    return env


def node_available():
    return find_node() is not None


def setup_done():
    base = data_dir()
    return os.path.exists(os.path.join(base, ".setup-done")) and os.path.isdir(
        os.path.join(base, "node_modules", "playwright")
    )


def setup_failed():
    return os.path.exists(os.path.join(data_dir(), ".setup-failed"))


def _pid_alive(pid_file):
    try:
        # Un pid recyclé après reboot peut correspondre à un autre process :
        # au-delà de 30 min, le fichier est considéré périmé.
        if time.time() - os.path.getmtime(pid_file) > 30 * 60:
            return False
        with open(pid_file, "r", encoding="utf-8") as handle:
            pid = int(handle.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def setup_running():
    return _pid_alive(os.path.join(data_dir(), "setup.pid"))


def _log_tail(name):
    try:
        with open(os.path.join(data_dir(), name), "r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle.readlines() if line.strip()]
        return lines[-1] if lines else ""
    except OSError:
        return ""


def setup_log_tail():
    return _log_tail("setup.log")


def daemon_log_tail():
    return _log_tail("daemon.log")


def _failures_file():
    return os.path.join(data_dir(), "daemon.failures")


def _read_failures():
    try:
        with open(_failures_file(), "r", encoding="utf-8") as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return 0


def _write_failures(count):
    try:
        with open(_failures_file(), "w", encoding="utf-8") as handle:
            handle.write(str(count))
    except OSError:
        pass


def _stored_daemon_port():
    try:
        with open(os.path.join(data_dir(), "daemon.port"), "r", encoding="utf-8") as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return None


def start_setup(workflow_dir):
    if setup_running():
        return
    for marker in (".setup-failed",):
        try:
            os.remove(os.path.join(data_dir(), marker))
        except OSError:
            pass
    process = subprocess.Popen(
        ["/bin/bash", os.path.join(workflow_dir, "setup.sh")],
        env=_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    with open(os.path.join(data_dir(), "setup.pid"), "w", encoding="utf-8") as handle:
        handle.write(str(process.pid))


def start_daemon(workflow_dir):
    """Démarre le démon, avec garde anti-rafale (Alfred relance le script
    à chaque frappe pendant le démarrage)."""
    stamp = os.path.join(data_dir(), "daemon.starting")
    try:
        if time.time() - os.path.getmtime(stamp) < 15:
            return
    except OSError:
        pass
    with open(stamp, "w", encoding="utf-8"):
        pass
    subprocess.Popen(
        ["/bin/bash", os.path.join(workflow_dir, "run-daemon.sh")],
        env=_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def reset_start_guards():
    """Autorise un redémarrage immédiat (utilisé par restart/setup)."""
    for name in ("daemon.starting", "daemon.failures"):
        try:
            os.remove(os.path.join(data_dir(), name))
        except OSError:
            pass


def ensure(workflow_dir):
    """Retourne (state, detail) :
    ready / starting / installing / no-node / failed / setup-failed."""
    try:
        status = call("/status", timeout=2)
        if status.get("version") != VERSION:
            # Démon d'une version précédente (mise à jour du workflow) :
            # on le remplace pour garder le contrat client/serveur aligné.
            try:
                call("/quit", timeout=5)
            except (DaemonDown, DaemonError):
                pass
            reset_start_guards()
            time.sleep(1)
            start_daemon(workflow_dir)
            return ("starting", None)
        _write_failures(0)
        return ("ready", status)
    except (DaemonDown, DaemonError):
        pass

    # Un démon peut tourner encore sur un ancien port (np_port modifié) et
    # tenir le verrou du profil Chrome : on l'arrête avant d'en lancer un autre.
    old_port = _stored_daemon_port()
    if old_port and old_port != port():
        try:
            call("/quit", timeout=5, on_port=old_port)
        except (DaemonDown, DaemonError):
            pass

    if not node_available():
        return ("no-node", None)
    if not setup_done():
        if setup_failed() and not setup_running():
            return ("setup-failed", setup_log_tail())
        if not setup_running():
            start_setup(workflow_dir)
        return ("installing", setup_log_tail())

    stamp = os.path.join(data_dir(), "daemon.starting")
    try:
        stamp_age = time.time() - os.path.getmtime(stamp)
    except OSError:
        stamp_age = None
    if stamp_age is not None and stamp_age < 15:
        return ("starting", None)  # tentative en cours
    # La tentative précédente n'a pas abouti : compter, plafonner, réessayer.
    failures = min(
        MAX_BOOT_FAILURES, _read_failures() + (1 if stamp_age is not None else 0)
    )
    _write_failures(failures)
    if failures >= MAX_BOOT_FAILURES:
        if stamp_age is not None and stamp_age > 600:
            _write_failures(0)  # nouvelle chance après 10 min de calme
        else:
            return ("failed", daemon_log_tail())
    start_daemon(workflow_dir)
    return ("starting", None)
