#!/usr/bin/env node
// Démon Playwright du workflow Alfred « The Noun Project ».
//
// Tourne en arrière-plan (headless, profil Chrome persistant) et expose une
// petite API HTTP locale pour les scripts Alfred :
//   GET /search?q=&limit=     recherche via l'API interne du site (sans compte)
//   GET /download?id=&format=SVG|PNG&size=&color=
//                             mutation GraphQL downloadIcon avec la session
//   GET /login                ouvre une fenêtre VISIBLE : l'utilisateur se
//                             connecte lui-même ; la session persiste ensuite
//   GET /status               état du démon et de la session
//   GET /quit                 arrêt propre
//
// Aucun identifiant ne transite par ce démon : la connexion se fait à la main
// dans la fenêtre Chrome, le profil persistant garde les cookies.

import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

const VERSION = '2.3.1'; // doit suivre la version d'info.plist (handshake client)
const HOME = process.env.HOME || '';
const DATA_DIR =
  process.env.NP_DATA_DIR ||
  path.join(
    HOME,
    'Library/Application Support/Alfred/Workflow Data/com.damiencuvillier.alfred.nounproject'
  );
const PROFILE_DIR = path.join(DATA_DIR, 'chrome-profile');
const PORT = parseInt(process.env.NP_PORT || '48223', 10);
const IDLE_MINUTES = parseInt(process.env.NP_IDLE_MINUTES || '180', 10);
const SITE = 'https://thenounproject.com';
const LOGIN_URL = SITE + '/accounts/login/';
const UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

// playwright est installé par setup.sh dans le dossier data du workflow
const requireFromData = createRequire(path.join(DATA_DIR, 'package.json'));
let chromium;
try {
  ({ chromium } = requireFromData('playwright'));
} catch (err) {
  console.error('playwright introuvable dans ' + DATA_DIR + ' — lance setup.sh (' + err.message + ')');
  process.exit(3);
}

let context = null;
let page = null;
let lifecycle = Promise.resolve(); // sérialise launch/close/login
let lastUse = Date.now();

function log(msg) {
  console.log(new Date().toISOString() + ' ' + msg);
}

function serialized(fn) {
  const run = lifecycle.then(fn, fn);
  lifecycle = run.catch(() => {});
  return run;
}

async function launch(headedMode) {
  try {
    context = await chromium.launchPersistentContext(PROFILE_DIR, {
      headless: !headedMode,
      userAgent: UA,
      viewport: { width: 1360, height: 900 },
      args: ['--disable-blink-features=AutomationControlled'],
    });
    context.on('close', () => {
      context = null;
      page = null;
    });
    page = context.pages()[0] || (await context.newPage());
    await page.goto(SITE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  } catch (err) {
    // Ne jamais laisser un contexte à moitié lancé (page sur about:blank) :
    // le prochain ensure() croirait le navigateur prêt.
    await closeBrowser();
    throw err;
  }
  log('navigateur lancé (' + (headedMode ? 'visible' : 'headless') + ')');
}

async function closeBrowser() {
  const ctx = context;
  context = null;
  page = null;
  if (ctx) {
    try {
      await ctx.close();
    } catch {
      /* déjà fermé */
    }
  }
}

function ensure() {
  return serialized(async () => {
    if (!context) await launch(false);
    if (!page || page.isClosed()) {
      page = await context.newPage();
    }
    if (!page.url().startsWith(SITE)) {
      // Page neuve ou navigation résiduelle : les fetch relatifs exigent
      // l'origine du site.
      await page.goto(SITE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    }
  });
}

async function isLoggedIn() {
  if (!context) return false;
  try {
    const cookies = await context.cookies(SITE);
    return cookies.some((c) => /session/i.test(c.name) && c.value);
  } catch {
    return false;
  }
}

async function doSearch(q, limit) {
  await ensure();
  const raw = await page.evaluate(async ({ q }) => {
    const r = await fetch(
      '/api/next/browse-tab-data/?term=' + encodeURIComponent(q) + '&type=icons&pageType=search',
      { headers: { accept: 'application/json' } }
    );
    if (!r.ok) return { httpError: r.status };
    try {
      return await r.json();
    } catch {
      return { httpError: r.status, notJson: true };
    }
  }, { q });
  if (raw.httpError) throw new Error('le site a répondu HTTP ' + raw.httpError);
  if (!('iconItems' in raw)) {
    // Un vrai « zéro résultat » a iconItems: [] ; l'absence de la clé signale
    // un changement du format interne du site.
    log('format de recherche inattendu, clés reçues : ' + Object.keys(raw).join(','));
    throw new Error(
      'format de réponse inattendu — le site a peut-être changé, cherche une mise à jour du workflow'
    );
  }
  const icons = (raw.iconItems || [])
    .filter((it) => it && it.id)
    .slice(0, limit)
    .map((it) => ({
      id: String(it.id),
      term: it.title || 'sans titre',
      permalink: it.url ? SITE + it.url : SITE,
      thumbnail_url:
        (it.thumbnails && (it.thumbnails.thumbnail200 || it.thumbnails.thumbnail512)) || '',
      creator: (it.creator && it.creator.name) || '?',
      license: it.license || '',
    }));
  return { total: raw.iconsTotal || icons.length, icons, loggedIn: await isLoggedIn() };
}

const DOWNLOAD_MUTATION = `mutation downloadIcon($iconId: ID!, $exportSize: Int, $imageFormat: IconFileType, $foregroundColor: String, $clientApp: ClientAppType = WEB) {
  downloadIcon(iconId: $iconId, exportSize: $exportSize, imageFormat: $imageFormat, foregroundColor: $foregroundColor, clientApp: $clientApp) {
    ok
    errors
    base64Stream
    termSlug
    creatorDisplayName
  }
}`;

function gqlDownload(variables) {
  return page.evaluate(
    async ({ query, variables }) => {
      const getCookie = (n) =>
        (document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)')) || [])[1];
      const r = await fetch('/graphql/', {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-csrftoken': getCookie('csrftoken') || '',
        },
        body: JSON.stringify({ operationName: 'downloadIcon', query, variables }),
      });
      const text = await r.text();
      try {
        return { status: r.status, body: JSON.parse(text) };
      } catch {
        return { status: r.status, raw: text.slice(0, 300) };
      }
    },
    { query: DOWNLOAD_MUTATION, variables }
  );
}

async function doDownload({ id, format, size, color }) {
  await ensure();
  const base = { iconId: String(id), imageFormat: format };
  if (format === 'PNG' && size) base.exportSize = size;
  // Format de couleur non documenté (hex nu ou #hex, accepté ou non selon le
  // format demandé) : on tente en dégradé, la dernière tentative sans couleur.
  const attempts = color
    ? [{ ...base, foregroundColor: color }, { ...base, foregroundColor: '#' + color }, base]
    : [base];
  let res = null;
  for (const variables of attempts) {
    res = await gqlDownload(variables);
    const hasGqlError = res.body && res.body.errors;
    if (!hasGqlError) break;
  }
  if (res.raw && res.raw.trim().startsWith('<')) {
    throw new Error(
      'le site a renvoyé une page HTML (vérification anti-robot ou session ' +
        'expirée) — reconnecte-toi via nounctl'
    );
  }
  const payload = res.body && res.body.data && res.body.data.downloadIcon;
  if (!payload) {
    const detail = res.raw || JSON.stringify((res.body && res.body.errors) || res.body);
    const err = new Error('réponse GraphQL inattendue : ' + String(detail).slice(0, 200));
    // Sans session, la cause de fond est presque toujours l'authentification :
    // guider le client vers la connexion plutôt que d'afficher le dump.
    if (!(await isLoggedIn())) err.authRequired = true;
    throw err;
  }
  if (!payload.ok) {
    const err = new Error(payload.errors || 'téléchargement refusé par le site');
    err.authRequired = /authentication/i.test(payload.errors || '');
    throw err;
  }
  return {
    base64: payload.base64Stream,
    term: payload.termSlug || '',
    creator: payload.creatorDisplayName || '',
  };
}

async function sessionFingerprint() {
  if (!context) return '';
  try {
    const cookies = await context.cookies(SITE);
    return cookies
      .filter((c) => /session/i.test(c.name) && c.value)
      .map((c) => c.name + '=' + c.value)
      .sort()
      .join(';');
  } catch {
    return '';
  }
}

function doLogin() {
  return serialized(async () => {
    await closeBrowser();
    await launch(true);
    // Un cookie « session » anonyme peut exister avant toute identification :
    // on attend un CHANGEMENT de session, pas sa simple présence.
    const before = await sessionFingerprint();
    let changed = false;
    try {
      await page.goto(LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    } catch {
      /* la page d'accueil reste utilisable pour se connecter */
    }
    const deadline = Date.now() + 5 * 60 * 1000;
    while (Date.now() < deadline) {
      lastUse = Date.now(); // pas d'arrêt d'inactivité pendant la connexion
      const now = await sessionFingerprint();
      if (now && now !== before) {
        changed = true;
        break;
      }
      if (!context || context.pages().length === 0) break; // fenêtre fermée
      await new Promise((r) => setTimeout(r, 1500));
    }
    await closeBrowser();
    let relaunched = true;
    try {
      await launch(false);
    } catch {
      // La session est déjà sur disque ; le prochain ensure() relancera.
      relaunched = false;
    }
    // L'état qui compte est la session PERSISTÉE, relue après relance —
    // couvre aussi le cas « connecté puis fenêtre fermée aussitôt ».
    const loggedIn = relaunched ? await isLoggedIn() : changed || !!before;
    log('login ' + (loggedIn ? 'réussi' : 'abandonné'));
    return { changed, loggedIn };
  });
}

const server = http.createServer(async (req, res) => {
  const send = (code, obj) => {
    res.writeHead(code, { 'content-type': 'application/json' });
    res.end(JSON.stringify(obj));
  };
  lastUse = Date.now();
  // Anti DNS-rebinding : seuls les clients qui nous nomment en local passent.
  const host = String(req.headers.host || '').split(':')[0];
  if (host !== '127.0.0.1' && host !== 'localhost' && host !== '') {
    return send(403, { error: 'hôte non autorisé' });
  }
  let u;
  try {
    // Un request-target malformé (« GET http://[ ») ferait lever URL hors de
    // tout try et tuerait le process via unhandled rejection.
    u = new URL(req.url, 'http://127.0.0.1');
  } catch {
    return send(400, { error: 'requête malformée' });
  }
  try {
    if (u.pathname === '/status') {
      send(200, {
        running: true,
        version: VERSION,
        pid: process.pid,
        port: PORT,
        browser: !!context,
        loggedIn: await isLoggedIn(),
      });
    } else if (u.pathname === '/search') {
      const q = (u.searchParams.get('q') || '').trim();
      if (!q) return send(400, { error: 'paramètre q manquant' });
      const limit =
        Math.max(1, Math.min(100, parseInt(u.searchParams.get('limit') || '30', 10) || 30));
      send(200, await doSearch(q, limit));
    } else if (u.pathname === '/download') {
      const id = (u.searchParams.get('id') || '').trim();
      if (!id) return send(400, { error: 'paramètre id manquant' });
      const format =
        (u.searchParams.get('format') || 'SVG').toUpperCase() === 'PNG' ? 'PNG' : 'SVG';
      const size = parseInt(u.searchParams.get('size') || '0', 10) || 0;
      const color = (u.searchParams.get('color') || '').trim();
      send(200, { ok: true, ...(await doDownload({ id, format, size, color })) });
    } else if (u.pathname === '/login') {
      const result = await doLogin();
      send(200, { ok: result.loggedIn, loggedIn: result.loggedIn, changed: result.changed });
    } else if (u.pathname === '/quit') {
      send(200, { ok: true });
      log('arrêt demandé');
      await closeBrowser();
      server.close(() => process.exit(0));
      setTimeout(() => process.exit(0), 1500).unref();
    } else {
      send(404, { error: 'route inconnue' });
    }
  } catch (err) {
    send(err.authRequired ? 401 : 500, {
      error: String((err && err.message) || err),
      authRequired: !!(err && err.authRequired),
    });
  }
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    log('port ' + PORT + ' déjà pris — un démon tourne déjà, sortie');
    process.exit(0);
  }
  throw err;
});

server.listen(PORT, '127.0.0.1', () => {
  log('démon v' + VERSION + ' en écoute sur 127.0.0.1:' + PORT + ' (profil ' + PROFILE_DIR + ')');
  // Permet aux clients de retrouver un démon resté sur un ancien port
  try {
    fs.writeFileSync(path.join(DATA_DIR, 'daemon.port'), String(PORT));
  } catch {
    /* non bloquant */
  }
});

setInterval(async () => {
  if (Date.now() - lastUse > IDLE_MINUTES * 60 * 1000) {
    log('inactif depuis ' + IDLE_MINUTES + ' min — arrêt');
    await closeBrowser();
    process.exit(0);
  }
}, 60 * 1000).unref();

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, async () => {
    await closeBrowser();
    process.exit(0);
  });
}
