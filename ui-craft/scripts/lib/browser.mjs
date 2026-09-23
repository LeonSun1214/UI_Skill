/**
 * Shared browser discovery for ui-craft scripts: bundled Chromium, a cached build from
 * another Playwright version, the machine's Chrome/Edge, or UI_CRAFT_CHROME.
 */
import { existsSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export async function loadPlaywright() {
  try { return await import('playwright'); }
  catch {
    const err = new Error("playwright is not installed. In the skill's scripts folder run: npm install");
    err.code = 'NO_PLAYWRIGHT';
    throw err;
  }
}

/** Chromium builds left by other Playwright versions, or a system Chromium. */
export function discoverChromium() {
  const roots = [
    process.env.PLAYWRIGHT_BROWSERS_PATH,
    join(homedir(), '.cache', 'ms-playwright'),
    join(homedir(), 'Library', 'Caches', 'ms-playwright'),
    process.env.LOCALAPPDATA ? join(process.env.LOCALAPPDATA, 'ms-playwright') : null,
  ].filter(Boolean);
  const found = [];
  for (const root of roots) {
    let entries = [];
    try { entries = readdirSync(root); } catch { continue; }
    for (const dir of entries.filter((n) => /^chromium-\d+$/.test(n)).sort().reverse()) {
      for (const tail of ['chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium',
        'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium', 'chrome-win/chrome.exe']) {
        const p = join(root, dir, tail);
        if (existsSync(p)) found.push(p);
      }
    }
  }
  for (const p of ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/snap/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium']) {
    if (existsSync(p)) found.push(p);
  }
  return found;
}

/** The launch attempts in order; each is [label, launchOptions]. */
export function launchAttempts(extra = {}) {
  const attempts = [];
  if (process.env.UI_CRAFT_CHROME) attempts.push(['UI_CRAFT_CHROME', { executablePath: process.env.UI_CRAFT_CHROME, ...extra }]);
  attempts.push(['bundled chromium', { ...extra }]);
  for (const p of discoverChromium()) attempts.push([`found ${p}`, { executablePath: p, ...extra }]);
  attempts.push(['Google Chrome', { channel: 'chrome', ...extra }], ['Microsoft Edge', { channel: 'msedge', ...extra }]);
  return attempts;
}

/** Launch the first Chromium that works. Returns { browser, via }. */
export async function launchChromium(pw, extra = {}) {
  const errors = [];
  for (const [name, o] of launchAttempts(extra)) {
    try { return { browser: await pw.chromium.launch(o), via: name }; }
    catch (e) { errors.push(`  ${name}: ${String(e.message).split('\n')[0]}`); }
  }
  throw new Error(`no Chromium could be launched:\n${errors.join('\n')}\n` +
    'fix: run "npx playwright install chromium" in the scripts folder, or set UI_CRAFT_CHROME=/path/to/chrome');
}
