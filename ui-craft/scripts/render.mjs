#!/usr/bin/env node
/**
 * ui-craft render — the skill's eyes and instruments.
 *
 * Renders a page at several viewports, saves screenshots for visual review, and
 * measures what can be measured from the live DOM:
 *   text contrast (against the composited background), tap-target size,
 *   horizontal overflow, keyboard focus visibility + obscuring, reduced-motion
 *   support, font loading, images without alt, heading structure, unnamed
 *   controls, viewport/zoom, console errors.
 *
 * Usage:
 *   node render.mjs <url | path/to/page.html> [--out DIR] [--viewports 375,768,1440]
 *                   [--wait MS] [--no-fold] [--strict]
 *
 * Writes  DIR/<width>-fold.png   above-the-fold (first impression)
 *         DIR/<width>-full.png   full page
 *         DIR/report.json        every measurement, per viewport
 * Prints  a one-line verdict per viewport plus the top offenders.
 *
 * Needs `playwright` (npm install in this folder) and one Chromium: the bundled
 * one (npx playwright install chromium), the machine's Chrome/Edge, or the binary
 * named by UI_CRAFT_CHROME.
 */
import { existsSync, readdirSync } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { isAbsolute, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const USAGE = `usage: node render.mjs <url | path/to/page.html> [options]
  --out DIR            output folder (default .ui-craft/latest)
  --viewports A,B,C    widths in CSS px (default 375,768,1440)
  --wait MS            extra settle time after load (default 500)
  --no-fold            skip the above-the-fold screenshots
  --strict             exit 1 when any viewport FAILs
env  UI_CRAFT_CHROME   path to a Chrome/Chromium binary to use`;

// ---------------------------------------------------------------- arguments
const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log(USAGE);
  process.exit(argv.length ? 0 : 1);
}
const opt = { out: '.ui-craft/latest', viewports: [375, 768, 1440], wait: 500, fold: true, strict: false };
let target = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out') opt.out = argv[++i];
  else if (a === '--viewports') opt.viewports = argv[++i].split(',').map(Number).filter((n) => n > 0);
  else if (a === '--wait') opt.wait = Number(argv[++i]) || 0;
  else if (a === '--no-fold') opt.fold = false;
  else if (a === '--strict') opt.strict = true;
  else if (a.startsWith('--')) { console.error(`unknown option ${a}\n${USAGE}`); process.exit(1); }
  else target = a;
}
if (!target || !opt.viewports.length) { console.error(USAGE); process.exit(1); }
const url = /^https?:\/\//i.test(target)
  ? target
  : pathToFileURL(isAbsolute(target) ? target : resolve(target)).href;

let pw;
try { pw = await import('playwright'); }
catch {
  console.error("playwright is not installed. In the skill's scripts folder run: npm install");
  process.exit(2);
}

/** Chromium builds left by other Playwright versions, or a system Chromium. */
function discoverChromium() {
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
  for (const p of ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/snap/bin/chromium']) {
    if (existsSync(p)) found.push(p);
  }
  return found;
}

async function launch() {
  const attempts = [];
  if (process.env.UI_CRAFT_CHROME) attempts.push(['UI_CRAFT_CHROME', { executablePath: process.env.UI_CRAFT_CHROME }]);
  attempts.push(['bundled chromium', {}]);
  for (const p of discoverChromium()) attempts.push([`found ${p}`, { executablePath: p }]);
  attempts.push(['Google Chrome', { channel: 'chrome' }], ['Microsoft Edge', { channel: 'msedge' }]);
  const errors = [];
  for (const [name, o] of attempts) {
    try { return await pw.chromium.launch(o); }
    catch (e) { errors.push(`  ${name}: ${String(e.message).split('\n')[0]}`); }
  }
  throw new Error(`no Chromium could be launched:\n${errors.join('\n')}\n` +
    'fix: run "npx playwright install chromium" in the scripts folder, or set UI_CRAFT_CHROME=/path/to/chrome');
}

const INTERACTIVE_SELECTOR = [
  'a[href]', 'button', 'input:not([type=hidden])', 'select', 'textarea', 'summary',
  '[role=button]', '[role=link]', '[role=checkbox]', '[role=radio]', '[role=switch]',
  '[role=tab]', '[role=menuitem]', '[role=option]',
].join(',');

// ------------------------------------------------------------ in-page audit
// Serialized into the page: no closures over module scope, only the argument.
function domAudit(INTERACTIVE) {
  const short = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) return `${s}#${el.id}`;
    const cls = [...el.classList].filter((c) => !c.includes(':') && !c.includes('[') && c.length < 24).slice(0, 2).join('.');
    if (cls) s += `.${cls}`;
    const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28);
    return t ? `${s} "${t}"` : s;
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 1 && r.height <= 1) return false; // sr-only / visually-hidden: clipped to 1px
    return r.width > 0 && r.height > 0;
  };

  // --- colors: parse legacy rgb()/rgba(); anything else (oklch, color(), hsl)
  //     goes through a 1×1 canvas so Tailwind v4's oklch palette measures correctly.
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const parseRgb = (str) => {
    const m = /rgba?\(([^)]+)\)/.exec(str || '');
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    if (p.length < 3 || p.some((n) => Number.isNaN(n))) return null;
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const toRGBA = (str) => {
    if (!str || str === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
    const direct = parseRgb(str);
    if (direct) return direct;
    try {
      ctx.fillStyle = '#010203';
      ctx.fillStyle = str;
      if (ctx.fillStyle === '#010203' && !/010203/i.test(str)) return null; // unparseable
      ctx.clearRect(0, 0, 1, 1);
      ctx.fillRect(0, 0, 1, 1);
      const d = ctx.getImageData(0, 0, 1, 1).data;
      return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 };
    } catch { return null; }
  };
  const lum = ({ r, g, b }) => {
    const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
  const over = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1,
  });
  const rgbStr = (c) => `rgb(${Math.round(c.r)}, ${Math.round(c.g)}, ${Math.round(c.b)})`;

  function effectiveBackground(el) {
    const layers = [];
    let node = el, opaque = null;
    while (node && node.nodeType === 1) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return { unverifiable: `background-image on ${short(node)}` };
      const c = toRGBA(cs.backgroundColor);
      if (c && c.a > 0) { if (c.a >= 0.999) { opaque = c; break; } layers.push(c); }
      node = node.parentElement;
    }
    let bg = opaque || { r: 255, g: 255, b: 255, a: 1 }; // canvas default
    for (let i = layers.length - 1; i >= 0; i--) bg = over(layers[i], bg);
    return bg;
  }

  const all = [...document.body.querySelectorAll('*')];

  // --- contrast on every element that directly contains text
  const contrast = { checked: 0, unverifiable: 0, failures: [] };
  for (const el of all) {
    const tag = el.tagName.toUpperCase();
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEMPLATE' || el.closest('svg')) continue;
    let hasText = false;
    for (const n of el.childNodes) { if (n.nodeType === 3 && n.textContent.trim()) { hasText = true; break; } }
    if (!hasText || !visible(el)) continue;
    const cs = getComputedStyle(el);
    const fg0 = toRGBA(cs.color);
    if (!fg0) continue;
    const bg = effectiveBackground(el);
    if (bg.unverifiable) { contrast.unverifiable++; continue; }
    const fg = fg0.a < 1 ? over(fg0, bg) : fg0;
    const size = parseFloat(cs.fontSize) || 16;
    const weight = parseInt(cs.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const required = large ? 3 : 4.5;
    const r = ratio(fg, bg);
    contrast.checked++;
    if (r < required) {
      contrast.failures.push({ selector: short(el), ratio: +r.toFixed(2), required, fontSize: +size.toFixed(1), color: rgbStr(fg), background: rgbStr(bg) });
    }
  }
  contrast.failures.sort((a, b) => a.ratio - b.ratio);
  contrast.failures = contrast.failures.slice(0, 40);

  // --- interactive elements: size, names
  const interactive = [...document.querySelectorAll(INTERACTIVE)].filter(visible);
  const targets = { checked: interactive.length, below24: [], between24and44: [] };
  for (const el of interactive) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const inlineText = cs.display === 'inline' && !!el.closest('p,li,dd,td,th,blockquote,figcaption,small');
    const w = Math.round(r.width), h = Math.round(r.height);
    const item = { selector: short(el), size: `${w}×${h}`, inlineText };
    if (w < 24 || h < 24) targets.below24.push(item);
    else if (w < 44 || h < 44) targets.between24and44.push(item);
  }
  targets.below24 = targets.below24.slice(0, 30);
  targets.between24and44 = targets.between24and44.slice(0, 30);

  const unnamedControls = interactive.filter((el) => {
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title')) return false;
    const tag = el.tagName.toUpperCase();
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
      const type = (el.getAttribute('type') || '').toLowerCase();
      if (['submit', 'button', 'reset', 'image'].includes(type)) return !(el.value || el.getAttribute('alt'));
      return !(el.labels && el.labels.length); // placeholder is not a label
    }
    if ((el.textContent || '').trim()) return false;
    const img = el.querySelector('img[alt]');
    if (img && img.getAttribute('alt').trim()) return false;
    if (el.querySelector('svg title, svg[aria-label]')) return false;
    return true;
  }).map(short).slice(0, 20);

  // --- horizontal overflow
  const vw = document.documentElement.clientWidth;
  const sw = document.documentElement.scrollWidth;
  const overflow = { horizontal: sw > vw + 1, scrollWidth: sw, viewportWidth: vw, offenders: [] };
  if (overflow.horizontal) {
    for (const el of all) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.right > vw + 1) {
        overflow.offenders.push({ selector: short(el), right: Math.round(r.right), width: Math.round(r.width) });
        if (overflow.offenders.length >= 10) break;
      }
    }
  }

  // --- motion
  let reducedMotionRule = false;
  const scan = (rules) => {
    for (const rule of rules) {
      if (rule.media && /prefers-reduced-motion/i.test(rule.media.mediaText)) reducedMotionRule = true;
      if (rule.cssRules && rule.cssRules.length) scan(rule.cssRules);
    }
  };
  for (const ss of document.styleSheets) { try { scan(ss.cssRules); } catch { /* cross-origin sheet */ } }
  let animatedElements = 0;
  for (const el of all) { const cs = getComputedStyle(el); if (cs.animationName && cs.animationName !== 'none') animatedElements++; }
  const motion = { reducedMotionRule, animatedElements };

  // --- fonts
  const fontMap = new Map();
  document.fonts.forEach((f) => {
    const family = f.family.replace(/["']/g, '');
    const key = `${family}|${f.status}`;
    if (!fontMap.has(key)) fontMap.set(key, { family, status: f.status });
  });
  const usedFamilies = [...new Set(['body', 'h1', 'h2', 'p', 'button']
    .map((s) => document.querySelector(s)).filter(Boolean)
    .map((el) => getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim()))];
  const fonts = { declared: [...fontMap.values()], used: usedFamilies };

  // --- images, headings, landmarks, viewport
  const imagesMissingAlt = [...document.images].filter((i) => !i.hasAttribute('alt') && visible(i)).map(short).slice(0, 20);

  const headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible)
    .map((h) => ({ level: +h.tagName[1], text: (h.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60) }));
  const skippedLevels = [];
  let prev = 0;
  for (const h of headings) { if (prev && h.level > prev + 1) skippedLevels.push(`h${prev} → h${h.level} "${h.text}"`); prev = h.level; }
  const structure = {
    h1Count: headings.filter((h) => h.level === 1).length,
    headings: headings.slice(0, 40),
    skippedLevels,
    main: !!document.querySelector('main,[role=main]'),
    nav: !!document.querySelector('nav,[role=navigation]'),
    skipLink: [...document.querySelectorAll('a[href^="#"]')].some((a) => /skip|跳/i.test(a.textContent || '')),
  };

  const vmeta = document.querySelector('meta[name="viewport"]');
  const content = vmeta ? (vmeta.getAttribute('content') || '') : '';
  const viewportMeta = {
    present: !!vmeta,
    blocksZoom: /user-scalable\s*=\s*(no|0)\b|maximum-scale\s*=\s*1(\.0+)?\s*(,|$)/i.test(content),
    content,
  };

  return { contrast, targets, unnamedControls, overflow, motion, fonts, imagesMissingAlt, structure, viewportMeta };
}

// ------------------------------------------------- keyboard focus (real Tabs)
async function focusAudit(page, max = 30) {
  const baseline = await page.evaluate((selector) => {
    const visible = (el) => { const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const short = (el) => { let s = el.tagName.toLowerCase(); if (el.id) return `${s}#${el.id}`; const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28); return t ? `${s} "${t}"` : s; };
    const snap = (el) => { const cs = getComputedStyle(el); return { outline: `${cs.outlineStyle} ${cs.outlineWidth}`, boxShadow: cs.boxShadow, borderColor: cs.borderColor, background: cs.backgroundColor, color: cs.color }; };
    if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    window.scrollTo(0, 0);
    const els = [...document.querySelectorAll(selector)].filter(visible);
    els.forEach((el, i) => el.setAttribute('data-uic-idx', String(i)));
    return els.map((el) => ({ selector: short(el), ...snap(el) }));
  }, INTERACTIVE_SELECTOR);

  const results = [];
  const seen = new Set();
  for (let i = 0; i < Math.min(max, baseline.length); i++) {
    await page.keyboard.press('Tab');
    const cur = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body || !el.hasAttribute('data-uic-idx')) return null;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const onTop = (cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight) ? document.elementFromPoint(cx, cy) : null;
      const obscured = !!onTop && onTop !== el && !el.contains(onTop) && !onTop.contains(el);
      return {
        idx: +el.getAttribute('data-uic-idx'), obscured, obscuredBy: obscured ? (onTop.tagName.toLowerCase() + (onTop.id ? '#' + onTop.id : '')) : null,
        outline: `${cs.outlineStyle} ${cs.outlineWidth}`, boxShadow: cs.boxShadow, borderColor: cs.borderColor, background: cs.backgroundColor, color: cs.color,
      };
    });
    if (!cur) continue;
    if (seen.has(cur.idx)) break; // cycled back to the start
    seen.add(cur.idx);
    const b = baseline[cur.idx];
    const outlineVisible = !/^none/.test(cur.outline) && !/\b0px$/.test(cur.outline);
    const changed = cur.outline !== b.outline || ['boxShadow', 'borderColor', 'background', 'color'].some((k) => cur[k] !== b[k]);
    results.push({ selector: b.selector, visible: outlineVisible || changed, obscured: cur.obscured, obscuredBy: cur.obscuredBy });
  }
  await page.evaluate(() => { document.querySelectorAll('[data-uic-idx]').forEach((el) => el.removeAttribute('data-uic-idx')); });
  return {
    tabbed: results.length,
    invisible: results.filter((r) => !r.visible).map((r) => r.selector).slice(0, 20),
    obscured: results.filter((r) => r.obscured).map((r) => `${r.selector} (behind ${r.obscuredBy})`).slice(0, 20),
  };
}

// -------------------------------------------------------------------- main
const browser = await launch();
await mkdir(opt.out, { recursive: true });
const report = { target: url, generatedAt: new Date().toISOString(), viewports: {}, summary: {} };
let anyFail = false;

for (const width of opt.viewports) {
  const height = width < 600 ? 812 : width < 1000 ? 1024 : 900;
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
  const consoleErrors = [];
  const failedRequests = [];
  const httpErrors = [];
  page.on('console', (m) => {
    // "Failed to load resource" carries no URL; the request/response listeners record those with one.
    if (m.type() === 'error' && !/^Failed to load resource/.test(m.text())) consoleErrors.push(m.text().slice(0, 200));
  });
  page.on('pageerror', (e) => consoleErrors.push(`pageerror: ${String(e.message).slice(0, 200)}`));
  page.on('requestfailed', (r) => failedRequests.push(`${r.failure()?.errorText || 'failed'} ${r.url().slice(0, 120)}`));
  page.on('response', (r) => {
    if (r.status() >= 400 && !/\/favicon\.ico(\?|$)/.test(r.url())) httpErrors.push(`${r.status()} ${r.url().slice(0, 120)}`);
  });

  let loadError = null;
  try {
    await page.goto(url, { waitUntil: 'load', timeout: 30000 });
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  } catch (e) { loadError = String(e.message).split('\n')[0]; }
  await page.waitForTimeout(opt.wait);

  // Scroll through once so lazy / IntersectionObserver content mounts, then back to top.
  if (!loadError) {
    await page.evaluate(async () => {
      const h = document.documentElement.scrollHeight;
      for (let y = 0; y < h; y += 600) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(150);
  }

  const key = String(width);
  const audit = loadError ? null : await page.evaluate(domAudit, INTERACTIVE_SELECTOR);
  const focus = loadError ? null : await focusAudit(page);
  if (!loadError) await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(100);
  if (opt.fold) await page.screenshot({ path: join(opt.out, `${key}-fold.png`) });
  await page.screenshot({ path: join(opt.out, `${key}-full.png`), fullPage: true });

  const fails = [], warns = [];
  if (loadError) fails.push(`load error: ${loadError}`);
  if (audit) {
    if (audit.contrast.failures.length) fails.push(`contrast ${audit.contrast.failures.length}`);
    if (audit.overflow.horizontal) fails.push(`horizontal overflow ${audit.overflow.scrollWidth}>${audit.overflow.viewportWidth}`);
    const hard24 = audit.targets.below24.filter((t) => !t.inlineText).length;
    if (hard24) fails.push(`targets<24px ${hard24}`);
    if (audit.unnamedControls.length) fails.push(`unnamed controls ${audit.unnamedControls.length}`);
    if (audit.imagesMissingAlt.length) fails.push(`img without alt ${audit.imagesMissingAlt.length}`);
    if (audit.viewportMeta.blocksZoom) fails.push('zoom blocked');
    if (audit.targets.between24and44.length) warns.push(`targets 24–44px ${audit.targets.between24and44.length}`);
    if (audit.motion.animatedElements && !audit.motion.reducedMotionRule) warns.push('animations without prefers-reduced-motion');
    if (audit.structure.h1Count !== 1) warns.push(`h1 count ${audit.structure.h1Count}`);
    if (audit.structure.skippedLevels.length) warns.push(`skipped heading levels ${audit.structure.skippedLevels.length}`);
    const fontErrors = audit.fonts.declared.filter((f) => f.status === 'error').length;
    if (fontErrors) warns.push(`font load errors ${fontErrors}`);
    if (!audit.viewportMeta.present) warns.push('no viewport meta');
  }
  if (focus) {
    if (focus.invisible.length) fails.push(`focus invisible ${focus.invisible.length}`);
    if (focus.obscured.length) fails.push(`focus obscured ${focus.obscured.length}`);
  }
  if (consoleErrors.length) warns.push(`console errors ${consoleErrors.length}`);
  if (failedRequests.length) warns.push(`failed requests ${failedRequests.length}`);
  if (httpErrors.length) warns.push(`http errors ${httpErrors.length}`);

  const status = fails.length ? 'FAIL' : 'PASS';
  if (fails.length) anyFail = true;
  report.viewports[key] = {
    width, height, status, fails, warns, loadError,
    console: consoleErrors.slice(0, 20), failedRequests: failedRequests.slice(0, 20), httpErrors: httpErrors.slice(0, 20),
    audit, focus,
    screenshots: { fold: opt.fold ? `${key}-fold.png` : null, full: `${key}-full.png` },
  };
  await page.close();
}
await browser.close();

report.summary = {
  status: anyFail ? 'FAIL' : 'PASS',
  viewports: Object.fromEntries(Object.entries(report.viewports).map(([k, v]) => [k, v.status])),
};
await writeFile(join(opt.out, 'report.json'), JSON.stringify(report, null, 2));

// ------------------------------------------------------------------ output
console.log(`ui-craft render → ${opt.out}`);
console.log(`  target: ${url}`);
for (const [k, v] of Object.entries(report.viewports)) {
  const detail = [...v.fails, ...v.warns.map((w) => `warn:${w}`)].join(' · ') || 'clean';
  console.log(`  ${k.padEnd(5)} ${v.status}  ${detail}`);
}
const first = Object.values(report.viewports).find((v) => v.audit);
if (first) {
  const fam = first.audit.fonts.declared;
  const line = fam.length ? fam.map((f) => `${f.family} (${f.status})`).join(', ') : 'none declared';
  console.log(`  fonts: ${line}; used: ${first.audit.fonts.used.join(', ')}`);
}
const top = (arr, n, fmt) => arr.slice(0, n).map(fmt).map((s) => `      ${s}`).join('\n');
for (const [k, v] of Object.entries(report.viewports)) {
  if (!v.audit) continue;
  const lines = [];
  if (v.audit.contrast.failures.length) lines.push(`    contrast:\n${top(v.audit.contrast.failures, 6, (f) => `${f.ratio}:1 (need ${f.required}) ${f.selector} — ${f.color} on ${f.background}`)}`);
  if (v.audit.overflow.horizontal) lines.push(`    overflow:\n${top(v.audit.overflow.offenders, 4, (o) => `${o.selector} right=${o.right}`)}`);
  const hard = v.audit.targets.below24.filter((t) => !t.inlineText);
  if (hard.length) lines.push(`    targets<24:\n${top(hard, 6, (t) => `${t.size} ${t.selector}`)}`);
  if (v.focus && v.focus.invisible.length) lines.push(`    focus invisible:\n${top(v.focus.invisible, 6, (s) => s)}`);
  if (v.focus && v.focus.obscured.length) lines.push(`    focus obscured:\n${top(v.focus.obscured, 4, (s) => s)}`);
  if (v.audit.unnamedControls.length) lines.push(`    unnamed:\n${top(v.audit.unnamedControls, 6, (s) => s)}`);
  if (v.audit.imagesMissingAlt.length) lines.push(`    img without alt:\n${top(v.audit.imagesMissingAlt, 4, (s) => s)}`);
  if (lines.length) console.log(`  ${k}:\n${lines.join('\n')}`);
}
console.log(`  full report: ${join(opt.out, 'report.json')}`);
process.exit(opt.strict && anyFail ? 1 : 0);
