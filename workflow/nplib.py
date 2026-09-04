#!/usr/bin/env python3
"""Bibliothèque partagée du workflow Alfred « The Noun Project ».

Signature OAuth 1.0a two-legged (HMAC-SHA1, consumer key/secret uniquement,
sans access token), transmise via le header Authorization — seule méthode
exemplifiée par la doc officielle. Stdlib Python 3.9 uniquement.
"""

import base64
import hashlib
import hmac
import http.client
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.thenounproject.com"


class NounProjectError(Exception):
    """Erreur API avec message présentable à l'utilisateur."""


def _pct(value):
    # Encodage strict RFC 3986 exigé par OAuth 1.0a (unreserved: A-Z a-z 0-9 - . _ ~)
    return urllib.parse.quote(str(value), safe="-._~")


def oauth_authorization(method, url, params, key, secret, timestamp=None, nonce=None):
    """Retourne la valeur du header Authorization pour une requête signée.

    `params` : paramètres de query string (non-oauth) participant à la signature.
    `timestamp` et `nonce` sont injectables pour les tests.
    """
    oauth_params = {
        "oauth_consumer_key": key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(timestamp or int(time.time())),
        "oauth_version": "1.0",
    }
    all_params = {**params, **oauth_params}
    # Base string : paires encodées, triées par clé encodée puis valeur encodée
    encoded = sorted((_pct(k), _pct(v)) for k, v in all_params.items())
    param_string = "&".join("%s=%s" % pair for pair in encoded)
    base_string = "&".join([method.upper(), _pct(url), _pct(param_string)])
    # Two-legged : pas de token secret, la clé de signature se termine par '&'
    signing_key = _pct(secret) + "&"
    digest = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    oauth_params["oauth_signature"] = base64.b64encode(digest).decode()
    return "OAuth " + ", ".join(
        '%s="%s"' % (_pct(name), _pct(value))
        for name, value in sorted(oauth_params.items())
    )


def api_get(path, params, key, secret, timeout=15):
    """GET signé sur l'API ; retourne le JSON décodé ou lève NounProjectError."""
    url = API_BASE + path
    authorization = oauth_authorization("GET", url, params, key, secret)
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    request = urllib.request.Request(
        url + ("?" + query if query else ""),
        headers={
            "Authorization": authorization,
            "User-Agent": "alfred-noun-project/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise NounProjectError(_http_error_message(err)) from err
    except urllib.error.URLError as err:
        raise NounProjectError("Réseau indisponible : %s" % err.reason) from err
    except json.JSONDecodeError as err:
        raise NounProjectError("Réponse illisible de l'API") from err
    except (http.client.HTTPException, OSError) as err:
        # socket.timeout et RemoteDisconnected ne sont pas des URLError
        raise NounProjectError(
            "Réseau indisponible ou délai dépassé : %s" % err
        ) from err


def _http_error_message(err):
    detail = ""
    try:
        body = json.loads(err.read().decode("utf-8"))
        for field in ("message", "detail", "error"):
            if isinstance(body, dict) and body.get(field):
                detail = str(body[field])
                break
    except Exception:
        pass
    if err.code == 401:
        base = "Authentification refusée (401) — vérifie ta clé et ton secret API"
    elif err.code == 403:
        base = (
            "Accès refusé (403) — l'accès API gratuit ne permet de télécharger "
            "que les icônes du domaine public"
        )
    elif err.code == 404:
        base = "Introuvable (404)"
    elif err.code == 429:
        base = "Quota API dépassé (429) — réessaie plus tard"
    else:
        base = "Erreur API %d" % err.code
    return "%s%s" % (base, " : " + detail if detail else "")


def get_credentials():
    key = (os.environ.get("np_api_key") or "").strip()
    secret = (os.environ.get("np_api_secret") or "").strip()
    return key, secret


def cache_dir():
    # Alfred ne crée PAS ce dossier lui-même : à créer avant toute écriture.
    path = os.environ.get("alfred_workflow_cache") or os.path.expanduser(
        "~/Library/Caches/alfred-noun-project"
    )
    os.makedirs(path, exist_ok=True)
    return path


def cache_days():
    """Durée du cache disque (recherches, téléchargements), en jours —
    réglable dans la configuration du workflow. 0 = désactivé."""
    raw = (os.environ.get("np_cache_days") or "2").strip()
    try:
        days = int(raw)
    except ValueError:
        days = 2
    return max(0, days)


def cached(namespace, fingerprint_parts, fetch, binary=False):
    """Cache disque générique, partagé par la recherche et le téléchargement.
    `fetch` est rappelé (et son résultat mis en cache) si l'entrée est
    absente, périmée ou illisible ; désactivé si cache_days() vaut 0."""
    days = cache_days()
    if days <= 0:
        return fetch()
    cache_root = os.path.join(cache_dir(), namespace)
    os.makedirs(cache_root, exist_ok=True)
    fingerprint = hashlib.sha1(
        json.dumps(fingerprint_parts, sort_keys=True).encode()
    ).hexdigest()
    cache_file = os.path.join(cache_root, fingerprint)
    try:
        if time.time() - os.path.getmtime(cache_file) < days * 86400:
            if binary:
                with open(cache_file, "rb") as handle:
                    return handle.read()
            with open(cache_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except (OSError, ValueError):
        # Fichier absent, illisible ou tronqué (Alfred tue le run précédent
        # pendant la frappe) : on repart de la source.
        pass
    data = fetch()
    tmp_file = "%s.%d.tmp" % (cache_file, os.getpid())
    if binary:
        with open(tmp_file, "wb") as handle:
            handle.write(data)
    else:
        with open(tmp_file, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
    os.replace(tmp_file, cache_file)
    return data
