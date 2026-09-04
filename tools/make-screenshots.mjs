#!/usr/bin/env node
// Génère screenshots/usage.png et screenshots/settings.png depuis les
// mockups HTML de tools/screenshots/, via le Playwright du dossier data
// du workflow (NP_DATA_DIR, installé par setup.sh).
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '..', 'screenshots');
const DATA_DIR =
  process.env.NP_DATA_DIR ||
  path.join(
    process.env.HOME,
    'Library/Application Support/Alfred/Workflow Data/com.damiencuvillier.alfred.nounproject'
  );
const { chromium } = createRequire(path.join(DATA_DIR, 'package.json'))('playwright');

const SHOTS = [
  { file: 'usage.html', out: 'usage.png', width: 1600, height: 912 },
  { file: 'settings.html', out: 'settings.png', width: 1190, height: 640 },
];

const browser = await chromium.launch();
for (const shot of SHOTS) {
  const page = await browser.newPage({
    viewport: { width: shot.width, height: shot.height },
  });
  await page.goto('file://' + path.join(HERE, 'screenshots', shot.file));
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(OUT, shot.out) });
  await page.close();
  console.log(shot.out + ' OK');
}
await browser.close();
