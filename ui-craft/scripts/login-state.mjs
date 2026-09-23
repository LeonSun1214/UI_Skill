#!/usr/bin/env node
/**
 * ui-craft login-state — capture a logged-in session for render.mjs.
 *
 *   node login-state.mjs https://app.example.com/login --out .ui-craft/state.json [--seconds 180]
 *
 * Opens a visible browser window at the URL. Log in by hand. When the window is closed
 * (or the time is up) the cookies and localStorage of every origin are written to the
 * file, which `render.mjs --storage-state <file>` then replays. The file holds live
 * session tokens: keep it out of git (.ui-craft/ is already ignored).
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { launchChromium, loadPlaywright } from './lib/browser.mjs';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log('usage: node login-state.mjs <login-url> [--out .ui-craft/state.json] [--seconds 180]');
  process.exit(argv.length ? 0 : 1);
}
let url = null, out = '.ui-craft/state.json', seconds = 180;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out') out = argv[++i];
  else if (a === '--seconds') seconds = Number(argv[++i]) || 180;
  else url = a;
}
let pw;
try { pw = await loadPlaywright(); } catch (e) { console.error(e.message); process.exit(2); }
const { browser, via } = await launchChromium(pw, { headless: false });
console.log(`browser: ${via}\nLog in in the window, then close it (or wait ${seconds}s). Saving to ${out}.`);
const context = await browser.newContext();
const page = await context.newPage();
await page.goto(url).catch((e) => console.error(`could not open ${url}: ${String(e.message).split('\n')[0]}`));
await new Promise((resolve) => {
  const t = setTimeout(resolve, seconds * 1000);
  page.on('close', () => { clearTimeout(t); resolve(); });
  browser.on('disconnected', () => { clearTimeout(t); resolve(); });
});
let state;
try { state = await context.storageState(); }
catch (e) { console.error(`could not read storage state: ${e.message}`); process.exit(1); }
await mkdir(dirname(out), { recursive: true });
await writeFile(out, JSON.stringify(state, null, 2));
console.log(`saved ${state.cookies.length} cookies and ${state.origins.length} origins → ${out}`);
await browser.close().catch(() => {});
