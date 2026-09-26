#!/usr/bin/env node
/**
 * ui-craft doctor — is this machine ready for the render loop?
 * Checks Node, playwright, a launchable Chromium, Python 3, and renders the built-in
 * test page once. Prints one line per check and exits 1 if anything essential is missing.
 */
import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, readFileSync, rmSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const rows = [];
const ok = (name, detail) => rows.push(['ok', name, detail]);
const bad = (name, detail, fix) => rows.push(['FAIL', name, `${detail}${fix ? ` — fix: ${fix}` : ''}`]);
const warn = (name, detail) => rows.push(['warn', name, detail]);

// node
const major = Number(process.versions.node.split('.')[0]);
(major >= 18 ? ok : bad)('node', `v${process.versions.node}`, 'install Node 18 or newer');

// playwright
let pw = null;
try { pw = await import('playwright'); ok('playwright', `installed in ${join(here, 'node_modules', 'playwright')}`); }
catch { bad('playwright', 'not installed', `cd ${here} && npm install`); }

// chromium
let browserVia = null;
if (pw) {
  try {
    const { launchChromium } = await import('./lib/browser.mjs');
    const { browser, via } = await launchChromium(pw);
    browserVia = via;
    const v = browser.version();
    await browser.close();
    ok('chromium', `${via} (${v})`);
  } catch (e) {
    bad('chromium', String(e.message).split('\n')[0], `cd ${here} && npx playwright install chromium, or set UI_CRAFT_CHROME=/path/to/chrome`);
  }
}

// version: is the copy Claude loads the copy this is run from?
const versionOf = (dir) => {
  try { const m = /^\s*version:\s*([\d.]+)/m.exec(readFileSync(join(dir, 'SKILL.md'), 'utf8')); return m ? m[1] : null; } catch { return null; }
};
const newer = (a, b) => { const pa = a.split('.').map(Number), pb = b.split('.').map(Number); for (let i = 0; i < 3; i++) { if ((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) > (pb[i] || 0); } return false; };
const mine = versionOf(join(here, '..'));
const installs = [join(homedir(), '.claude', 'skills', 'ui-craft'), join(process.cwd(), '.claude', 'skills', 'ui-craft')]
  .filter((d) => existsSync(join(d, 'SKILL.md')) && resolve(d) !== resolve(join(here, '..')));
const behind = installs.map((d) => [d, versionOf(d)]).filter(([, v]) => mine && v && newer(mine, v));
if (behind.length) warn('version', `${mine} here, but ${behind.map(([d, v]) => `${v} installed at ${d}`).join(' and ')} — that copy is what Claude loads; re-run install.sh`);
else ok('version', `${mine || '?'}${installs.length ? ` (installed: ${installs.map((d) => `${versionOf(d) || '?'} at ${d}`).join(', ')})` : ''}`);

// python
const py = spawnSync('python3', ['--version'], { encoding: 'utf8' });
if (py.status === 0) ok('python3', (py.stdout || py.stderr).trim());
else warn('python3', 'not found — inspect.py and contrast.py need Python 3');

// self-render
if (pw && browserVia) {
  const out = join(tmpdir(), `ui-craft-doctor-${process.pid}`);
  const r = spawnSync(process.execPath, [join(here, 'render.mjs'), join(here, 'selftest', 'instruments.html'), '--out', out, '--viewports', '600'], { encoding: 'utf8', timeout: 120000 });
  const reportPath = join(out, 'report.json');
  if (r.status === 0 && existsSync(reportPath)) {
    const rep = JSON.parse(readFileSync(reportPath, 'utf8'));
    const v = rep.viewports['600'];
    const fails = v ? v.fails.length : -1;
    (fails >= 3 ? ok : bad)('render loop', `test page rendered, ${fails} FAILs found (expected ≥ 3: the page plants them)`, 'run "npm test" here for details');
  } else {
    bad('render loop', (r.stderr || r.stdout || '').trim().split('\n').slice(-2).join(' ') || `exit ${r.status}`, 'run "npm test" here for details');
  }
  try { rmSync(out, { recursive: true, force: true }); } catch { /* ignore */ }
}

const pad = (s, n) => String(s).padEnd(n);
for (const [st, name, detail] of rows) console.log(`${pad(st, 5)} ${pad(name, 12)} ${detail}`);
const failed = rows.filter((r) => r[0] === 'FAIL').length;
console.log(failed ? `\n${failed} problem(s). ui-craft's render loop will not work until they are fixed.` : '\nready: the render loop works on this machine.');
process.exit(failed ? 1 : 0);
