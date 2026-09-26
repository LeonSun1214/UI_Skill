#!/usr/bin/env node
/**
 * ui-craft self-test: renders the pages in ./selftest through render.mjs and checks that the
 * instruments report exactly the defects those pages plant, and that the real-project
 * options (--cookie, --header, --storage-state, --init-script, --mock, --wait-for, --compare)
 * do what they say. `npm test` here. Needs a launchable Chromium (see doctor.mjs).
 */
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const pages = join(here, 'selftest');
const work = mkdtempSync(join(tmpdir(), 'ui-craft-selftest-'));

// A tiny server: static pages plus /api/items, which needs a bearer header or a session cookie.
const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css' };
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/api/items') {
    const authed = /^Bearer\s+\S+/.test(req.headers.authorization || '') || /(^|;\s*)session=ok(;|$)/.test(req.headers.cookie || '');
    res.writeHead(authed ? 200 : 401, { 'content-type': 'application/json' });
    res.end(JSON.stringify(authed ? { items: ['Server item'] } : { items: null }));
    return;
  }
  const file = join(pages, url.pathname.replace(/^\/+/, ''));
  if (!file.startsWith(pages) || !existsSync(file)) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'content-type': MIME[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

// Asynchronous on purpose: the test server lives in this process, so a blocking spawnSync
// would starve it and every http case would time out.
function render(target, out, ...extra) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [join(here, 'render.mjs'), target, '--out', out, '--viewports', '600', ...extra]);
    let err = '', log = '';
    child.stdout.on('data', (d) => { log += d; });
    child.stderr.on('data', (d) => { err += d; });
    const timer = setTimeout(() => child.kill('SIGKILL'), 180000);
    child.on('close', () => {
      clearTimeout(timer);
      const rp = join(out, 'report.json');
      if (!existsSync(rp)) return reject(new Error(`no report for ${target}: ${(err || log).trim().split('\n').slice(-3).join(' | ')}`));
      // The report, with what render.mjs printed alongside (a check on the console lines reads it).
      resolve(Object.defineProperty(JSON.parse(readFileSync(rp, 'utf8')), 'stdout', { value: log, enumerable: false }));
    });
  });
}
const v = (rep) => rep.viewports['600'];
const h1 = (rep) => (v(rep).audit.structure.headings.find((h) => h.level === 1) || {}).text || '';

const results = [];
async function check(name, fn) {
  try { const detail = await fn(); results.push(['ok', name, detail || '']); }
  catch (e) { results.push(['FAIL', name, String(e.message).split('\n')[0]]); }
}
const expect = (cond, msg) => { if (!cond) throw new Error(msg); };

try {
  // 1. planted defects on the instruments page (file://)
  const inst = await render(join(pages, 'instruments.html'), join(work, 'inst'));
  await check('instruments: planted FAILs', () => {
    const f = v(inst).fails.join(' | '), w = v(inst).warns.join(' | ');
    expect(/non-text contrast 1/.test(f), `expected 1 non-text failure: ${f}`);
    expect(/focus ring <3:1 1/.test(f), `expected 1 faint ring: ${f}`);
    expect(/dark contrast 1/.test(f), `expected 1 dark text failure: ${f}`);
    expect(/no hover feedback 1/.test(w), `expected 1 no-hover warn: ${w}`);
    expect(/cursor not pointer 1/.test(w), `expected 1 cursor warn: ${w}`);
    expect(!/contrast \d/.test(f.replace(/non-text contrast \d|dark contrast \d/g, '')), `light text contrast should be clean: ${f}`);
    return `${f} · warn: ${w}`;
  });
  await check('findings printed once across viewports', async () => {
    const r = await render(join(pages, 'instruments.html'), join(work, 'inst-merged'), '--viewports', '375,600');
    const lines = r.stdout.split('\n');
    expect(lines.some((l) => /^\s*findings at 375 \/ 600 \(an untagged line holds at every viewport\)/.test(l)), 'no merged findings header');
    const ring = lines.filter((l) => /^ {4}focus ring <3:1:$/.test(l)); // the light section; 'dark focus ring' is its own
    expect(ring.length === 1, `the focus-ring section should appear once, appeared ${ring.length} times`);
    expect(!lines.some((l) => /^\s*(375|600):\s*$/.test(l)), 'a per-viewport block was printed');
    return `${lines.filter((l) => /^\s{6}\S/.test(l)).length} finding lines, one block`;
  });
  await check('viewports side by side agree with --serial', async () => {
    const vps = ['--viewports', '375,600,1024'];
    const par = await render(join(pages, 'instruments.html'), join(work, 'inst-par'), ...vps);
    const ser = await render(join(pages, 'instruments.html'), join(work, 'inst-ser'), ...vps, '--serial');
    const sig = (r) => JSON.stringify(Object.entries(r.viewports).map(([k, x]) => [k, x.fails, x.warns, x.focus && x.focus.tabbed, x.hover && x.hover.noHoverFeedback]));
    expect(sig(par) === sig(ser), `side by side and serial differ:\n${sig(par)}\n${sig(ser)}`);
    expect(par.timings && par.viewports['375'].timings && par.viewports['375'].timings.total > 0, 'timings missing from report.json');
    return `3 viewports, same findings · ${(par.timings.viewports / 1000).toFixed(1)} s side by side, ${(ser.timings.viewports / 1000).toFixed(1)} s serial`;
  });
  await check('instruments: clean button stays clean', () => {
    const names = [...v(inst).audit.nonText.failures, ...v(inst).focus.lowContrastRing.map((s) => ({ selector: s }))].map((x) => x.selector).join(' ');
    expect(!/OK button/.test(names), `the OK button was flagged: ${names}`);
  });

  // 2. class-based dark mode
  const dk = await render(join(pages, 'dark-class.html'), join(work, 'dark'));
  await check('dark mode via .dark class', () => {
    const d = v(dk).dark;
    expect(d && d.mode === 'class' && d.themeChanged, `dark pass missing or unchanged: ${JSON.stringify(d && { mode: d.mode, themeChanged: d.themeChanged })}`);
    expect(d.nonText.failures.length === 1, `expected the input border to fail in dark: ${JSON.stringify(d.nonText.failures)}`);
    return `mode=${d.mode}, bg ${v(dk).audit.pageColors.background} → ${d.pageColors.background}`;
  });

  // 2b. patterns met in a real project (see evals/notes/trial-sunnotice.md)
  const rp = await render(join(pages, 'real-project.html'), join(work, 'real'));
  await check('boot-script theme gets a dark pass', () => {
    const d = v(rp).dark;
    expect(d && d.themeChanged, `dark pass missing or unchanged: ${JSON.stringify(d && { mode: d.mode, themeChanged: d.themeChanged, bg: d.pageColors && d.pageColors.background })}`);
    expect(d.mode === 'attribute', `expected mode=attribute, got ${d.mode}`);
    return `mode=${d.mode}, bg ${v(rp).audit.pageColors.background} → ${d.pageColors.background}`;
  });
  await check('gradient-filled control is unverifiable', () => {
    const n = v(rp).audit.nonText;
    expect(n.failures.length === 0, `gradient button should not FAIL: ${JSON.stringify(n.failures)}`);
    expect(n.unverifiable === 1, `expected 1 unverifiable boundary, got ${n.unverifiable}`);
    return `${n.checked} checked · ${n.unverifiable} unverifiable · ${n.failures.length} failures`;
  });
  await check('browser default ring is visible, not faint', () => {
    const f = v(rp).focus, d = v(rp).dark.focus;
    expect(f.invisible.length === 0, `default ring counted invisible: ${JSON.stringify(f.invisible)}`);
    expect(f.lowContrastRing.length === 0 && d.lowContrastRing.length === 0, `default ring measured faint: ${JSON.stringify([f.lowContrastRing, d.lowContrastRing])}`);
    return `${f.tabbed} tabbed, 0 faint (light and dark)`;
  });
  await check('pressed segment owes no hover feedback', () => {
    const h = v(rp).hover;
    expect(h && h.noHoverFeedback.length === 0, `pressed segment flagged: ${JSON.stringify(h && h.noHoverFeedback)}`);
    expect(h.checked === 3, `the dev overlay's shadow button was probed: ${h.checked} hovered`);
    expect(v(rp).audit.devOverlay === 'nextjs-portal', `dev overlay not reported: ${v(rp).audit.devOverlay}`);
    return `${h.checked} hovered, 0 without feedback · <nextjs-portal> hidden`;
  });

  // 3. gated page: no auth → sign-in; each auth option → dashboard
  await check('gated: no auth shows sign-in', async () => { const r = await render(`${base}/gated.html`, join(work, 'g0')); expect(h1(r) === 'Sign in', `h1=${h1(r)}`); });
  await check('--cookie', async () => { const r = await render(`${base}/gated.html`, join(work, 'g1'), '--cookie', 'session=ok'); expect(/^Dashboard/.test(h1(r)), `h1=${h1(r)}`); return h1(r); });
  await check('--header', async () => { const r = await render(`${base}/gated.html`, join(work, 'g2'), '--header', 'Authorization: Bearer selftest'); expect(/^Dashboard/.test(h1(r)), `h1=${h1(r)}`); return h1(r); });
  await check('--init-script', async () => { const r = await render(`${base}/gated.html`, join(work, 'g3'), '--init-script', join(pages, 'init-token.js')); expect(/^Dashboard/.test(h1(r)), `h1=${h1(r)}`); return h1(r); });
  await check('--storage-state', async () => {
    const state = { cookies: [], origins: [{ origin: base, localStorage: [{ name: 'token', value: 'from-state' }] }] };
    const sp = join(work, 'state.json'); writeFileSync(sp, JSON.stringify(state));
    const r = await render(`${base}/gated.html`, join(work, 'g4'), '--storage-state', sp);
    expect(/^Dashboard/.test(h1(r)), `h1=${h1(r)}`); return h1(r);
  });
  await check('--mock', async () => {
    const r = await render(`${base}/gated.html`, join(work, 'g5'), '--mock', `**/api/items=${join(pages, 'mock-items.json')}`);
    expect(/3 items/.test(h1(r)), `h1=${h1(r)}`); return h1(r);
  });

  // 3b. --mock with an inline body and with a bare status; the requests line
  await check('--mock inline JSON', async () => {
    const r = await render(`${base}/gated.html`, join(work, 'g6'), '--mock', '**/api/items={"items":["x","y"]}');
    expect(/2 items/.test(h1(r)), `h1=${h1(r)}`);
    const q = (v(r).requests || []).find((x) => /\/api\/items/.test(x.url));
    expect(q && q.status === 200, `requests line missing the mocked call: ${JSON.stringify(v(r).requests)}`);
    return `${h1(r)} · requests: ${(v(r).requests || []).map((x) => `${x.status} ${x.method} ${x.url}`).join(', ')}`;
  });
  await check('--mock bare status overrides the server', async () => {
    const r = await render(`${base}/gated.html`, join(work, 'g7'), '--header', 'Authorization: Bearer selftest', '--mock', '**/api/items=401');
    expect(h1(r) === 'Sign in', `expected the 401 mock to win over the header: h1=${h1(r)}`);
    const q = (v(r).requests || []).find((x) => /\/api\/items/.test(x.url));
    expect(q && q.status === 401, `requests line should show 401: ${JSON.stringify(v(r).requests)}`);
    return `h1=${h1(r)} · ${q.status} ${q.method} ${q.url}`;
  });
  await check('requests line counts a repeated call once', async () => {
    const r = await render(`${base}/twice.html`, join(work, 'g8'));
    const line = (r.stdout.split('\n').find((l) => /^\s*requests \(xhr\/fetch/.test(l)) || '').trim();
    expect(/\(xhr\/fetch, 2, 1 distinct\)/.test(line) && /401 GET \/api\/items ×2/.test(line), `line was: ${line || '(none)'}`);
    return line.replace(/\s+←.*$/, '');
  });

  // 3c. --dismiss lifts a splash that a key press removes
  // 3d. --act: a dialog that follows the pattern, one that does not, a form's error state, a step that finds nothing
  await check('--act opens a dialog that behaves', async () => {
    const r = await render(`${base}/dialog.html`, join(work, 'dlg-good'), '--act', 'click:#open-good');
    const d = v(r).dialog;
    expect(d && d.name === 'Delete project?', `dialog not found or unnamed: ${JSON.stringify(d)}`);
    expect(d.focusInside && d.trapped && d.escapeCloses && d.fits && d.modal && d.closeControl, `good dialog flagged: ${JSON.stringify(d)}`);
    expect(!v(r).fails.some((f) => /^dialog/.test(f)) && !v(r).warns.some((w) => /^dialog|^act/.test(w)), `unexpected: ${v(r).fails.join(' | ')} · ${v(r).warns.join(' | ')}`);
    return `"${d.name}" · focus inside · ${d.focusables} controls, Tab stays · Escape closes`;
  });
  await check('--act opens a dialog that does not', async () => {
    const r = await render(`${base}/dialog.html`, join(work, 'dlg-bad'), '--act', 'click:#open-bad');
    const d = v(r).dialog, f = v(r).fails.join(' | '), w = v(r).warns.join(' | ');
    expect(d && !d.focusInside && !d.trapped && !d.name, `bad dialog not caught: ${JSON.stringify(d)}`);
    expect(/dialog: focus did not move/.test(f) && /dialog: no accessible name/.test(f) && !/Tab leaves/.test(f), `expected two dialog FAILs: ${f}`);
    expect(/dialog: not modal .*Tab leaves it after 1 Tab/.test(w) && /Escape does not close/.test(w) && /no close or cancel/.test(w), `expected three dialog warns: ${w}`);
    return f.split(' | ').filter((x) => x.startsWith('dialog')).join(' | ');
  });
  await check('--act type + press shows the form error', async () => {
    const r = await render(`${base}/dialog.html`, join(work, 'dlg-form'), '--act', 'type:input[name=email]=nope', '--act', 'press:Enter');
    const a = v(r).audit.alerts || [];
    expect(a.some((t) => /Email is required/.test(t)), `no alert text: ${JSON.stringify(a)}`);
    expect(v(r).audit.invalidFields === 1, `invalid field count ${v(r).audit.invalidFields}`);
    expect(!v(r).dialog, 'a dialog was reported where none opened');
    return `alert "${a[0]}" · 1 invalid field`;
  });
  await check('--act reports a step that finds nothing', async () => {
    const r = await render(`${base}/dialog.html`, join(work, 'dlg-miss'), '--act', 'click:#nope');
    expect(v(r).actErrors.length === 1 && v(r).warns.some((x) => /^act failed/.test(x)), `missing step not reported: ${JSON.stringify(v(r).actErrors)} · ${v(r).warns.join(' | ')}`);
    return v(r).actErrors[0].slice(0, 70);
  });

  // 3e. a grid whose last row is short is reported; a full one is not
  await check('ragged grid: three cards in two columns', async () => {
    const r = await render(`${base}/grid.html`, join(work, 'grid'));
    const g = v(r).audit.ragged || [];
    expect(g.length === 1 && g[0].selector.includes('three') && g[0].columns === 2 && g[0].lastRow === 1, `expected the three-card grid alone: ${JSON.stringify(g)}`);
    expect(v(r).warns.some((w) => /^ragged grid 1$/.test(w)), `warn missing: ${v(r).warns.join(' | ')}`);
    return `${g[0].items} items in ${g[0].columns} columns, ${g[0].lastRow} alone · the four-card grid not flagged`;
  });

  // 3f. what is drawn in layers: text on a positioned indicator, rings on ::before, shadow rings
  // stacked the way Tailwind stacks them, fields outlined by an inset ring or recoloured on focus
  await check('layers: backdrops and rings read as drawn', async () => {
    const r = await render(`${base}/layers.html`, join(work, 'layers'));
    const a = v(r).audit, f = v(r).focus;
    const text = a.contrast.failures.map((x) => x.selector).sort();
    expect(text.length === 2 && /covered/.test(text[0]) && /faint-caption/.test(text[1]), `expected the faint caption and the text under the veil: ${JSON.stringify(text)}`);
    expect(a.contrast.positionedBackdrop >= 1, 'the tab on the indicator was not read against it');
    expect(a.contrast.unverifiable === 1, `the text on the photo should be unverifiable: ${a.contrast.unverifiable}`);
    const fields = a.nonText.failures;
    expect(fields.length === 1 && /field-ringed$/.test(fields[0].selector) && fields[0].via === 'ring', `expected the faint ring field alone, via its ring: ${JSON.stringify(fields)}`);
    const faint = f.lowContrastRing.join(' | ');
    expect(f.invisible.length === 0, `rings counted invisible: ${JSON.stringify(f.invisible)}`);
    expect(f.lowContrastRing.length === 2 && /nav-faint \(outline on ::before/.test(faint) && /ring-faint \(box-shadow/.test(faint), `expected the faint ::before ring and the faint shadow ring: ${faint}`);
    return `${text.join(' and ')} fail, the tab on the indicator passes, the photo is unverifiable · ${fields[0].selector} via ring · faint rings: ${faint}`;
  });

  await check('--dismiss Escape lifts the splash', async () => {
    const a = await render(`${base}/splash.html`, join(work, 's0'));
    const b = await render(`${base}/splash.html`, join(work, 's1'), '--dismiss', 'Escape');
    expect(v(a).audit.pageTitle === 'Splash test' && v(a).focus.obscured.length >= 1, `without: title=${v(a).audit.pageTitle}, obscured=${JSON.stringify(v(a).focus.obscured)}`);
    expect(v(b).audit.pageTitle === 'Splash lifted' && v(b).focus.obscured.length === 0, `with: title=${v(b).audit.pageTitle}, obscured=${JSON.stringify(v(b).focus.obscured)}`);
    return `without: ${v(a).focus.obscured.length} obscured · with: title "${v(b).audit.pageTitle}", 0 obscured`;
  });

  // 4. late content: --wait-for
  await check('--wait-for', async () => {
    const a = await render(`${base}/hydrate.html`, join(work, 'h0'), '--wait', '100');
    const b = await render(`${base}/hydrate.html`, join(work, 'h1'), '--wait-for', '#app[data-hydrated]');
    expect(h1(b) === 'Hydrated', `after wait-for h1=${h1(b)}`);
    expect(v(b).audit.contrast.failures.length === 1, `expected the faint link to fail after hydration: ${JSON.stringify(v(b).audit.contrast.failures)}`);
    return `without: h1=${h1(a)} · with: h1=${h1(b)}, ${v(b).audit.contrast.failures.length} contrast failure`;
  });

  // 5. --compare
  await check('--compare identical / changed', async () => {
    const again = await render(join(pages, 'instruments.html'), join(work, 'inst2'), '--compare', join(work, 'inst'));
    const same = Object.values(again.compare.files);
    expect(same.length > 0 && same.every((f) => f.status === 'identical'), `re-render should be identical: ${JSON.stringify(again.compare.files)}`);
    const other = await render(join(pages, 'dark-class.html'), join(work, 'dark2'), '--compare', join(work, 'inst'));
    const changed = Object.entries(other.compare.files).filter(([, f]) => f.status === 'changed');
    expect(changed.length > 0 && changed.every(([, f]) => f.diff), `different page should differ and write diff images: ${JSON.stringify(other.compare.files)}`);
    const full = other.compare.files['600-full.png'];
    expect(full && typeof full.heightDelta === 'number', `full-page entry should carry heightDelta: ${JSON.stringify(full)}`);
    expect(changed.every(([, f]) => /^(within|spread over the page|at y)/.test(f.where || '')), `changed entries should say where: ${JSON.stringify(changed.map(([n, f]) => [n, f.where]))}`);
    return `${same.length} identical on re-render; ${changed.length} changed vs another page (${changed[0][1].changedPct}%, full page ${full.heightDelta >= 0 ? '+' : ''}${full.heightDelta} px, ${full.where})`;
  });
} finally {
  server.close();
}

const pad = (s, n) => String(s).padEnd(n);
for (const [st, name, detail] of results) console.log(`${pad(st, 5)} ${pad(name, 36)} ${detail}`);
const failed = results.filter((r) => r[0] === 'FAIL').length;
console.log(failed ? `\n${failed} of ${results.length} checks failed (outputs kept in ${work})` : `\nall ${results.length} checks passed`);
if (!failed) rmSync(work, { recursive: true, force: true });
process.exit(failed ? 1 : 0);
