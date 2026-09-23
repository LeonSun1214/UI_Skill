#!/usr/bin/env node
/**
 * ui-craft render — the skill's eyes and instruments.
 *
 * Renders a page at several viewports, saves screenshots for visual review, and
 * measures what can be measured from the live DOM:
 *   text contrast (against the composited background), non-text contrast of control
 *   boundaries and focus rings (WCAG 1.4.11), tap-target size (label-aware),
 *   horizontal overflow, keyboard focus visibility + obscuring, hover feedback,
 *   reduced-motion support, dark-mode rendering (auto-detected) with its own
 *   contrast audit, font loading, images without alt, heading structure, unnamed
 *   controls, viewport/zoom, console errors.
 *
 * Usage:
 *   node render.mjs <url | path/to/page.html> [--out DIR] [--viewports 375,768,1440]
 *                   [--wait MS] [--wait-for SELECTOR] [--no-fold] [--dark | --no-dark] [--no-hover]
 *                   [--storage-state FILE] [--cookie k=v] [--header k:v] [--auth user:pass]
 *                   [--init-script FILE] [--mock PATTERN=FILE] [--compare DIR] [--strict]
 *
 * Writes  DIR/contact.png             all viewports above the fold, one image (look first)
 *         DIR/<width>-fold.png        above the fold      DIR/<width>-full.png   full page
 *         DIR/<width>-dark-fold.png   dark mode, when the page supports it (or --dark)
 *         DIR/contact-dark.png        dark folds side by side, when rendered
 *         DIR/report.json             every measurement, per viewport
 * Prints  a one-line verdict per viewport plus the top offenders.
 *
 * Needs `playwright` (npm install in this folder) and one Chromium: the bundled
 * one (npx playwright install chromium), a cached one from another Playwright
 * version, the machine's Chrome/Edge, or the binary named by UI_CRAFT_CHROME.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { isAbsolute, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const USAGE = `usage: node render.mjs <url | path/to/page.html> [options]
  --out DIR            output folder (default .ui-craft/latest)
  --viewports A,B,C    widths in CSS px (default 375,768,1440)
  --wait MS            extra settle time after load (default 500)
  --no-fold            skip the above-the-fold screenshots and contact sheets
  --dark / --no-dark   force or skip the dark-mode pass (default: auto — when the page has a dark rule)
  --no-hover           skip the hover-feedback probe (done at the widest viewport only)
  --wait-for SEL       wait for a CSS selector before measuring (SPA hydration, data loading)
  --storage-state F    Playwright storage state JSON (cookies + localStorage) — a logged-in session; see login-state.mjs
  --cookie k=v         add a cookie for the target's host (repeatable)
  --header k:v         extra HTTP header on every request, e.g. Authorization (repeatable)
  --auth user:pass     HTTP basic auth
  --init-script F      JS file run in every page before its scripts (seed localStorage, flags, fetch mocks)
  --mock PATTERN=F     answer requests whose URL matches PATTERN (glob or /regex/) with the file's contents (repeatable)
  --compare DIR        pixel-diff every screenshot against the same-named one in DIR (a previous run)
  --strict             exit 1 when any viewport FAILs
env  UI_CRAFT_CHROME   path to a Chrome/Chromium binary to use`;

// ---------------------------------------------------------------- arguments
const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log(USAGE);
  process.exit(argv.length ? 0 : 1);
}
const opt = { out: '.ui-craft/latest', viewports: [375, 768, 1440], wait: 500, waitFor: null, fold: true, dark: 'auto', hover: true, strict: false,
  storageState: null, cookies: [], headers: {}, auth: null, initScript: null, mocks: [], compare: null };
let target = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out') opt.out = argv[++i];
  else if (a === '--viewports') opt.viewports = argv[++i].split(',').map(Number).filter((n) => n > 0);
  else if (a === '--wait') opt.wait = Number(argv[++i]) || 0;
  else if (a === '--no-fold') opt.fold = false;
  else if (a === '--dark') opt.dark = 'force';
  else if (a === '--no-dark') opt.dark = 'skip';
  else if (a === '--no-hover') opt.hover = false;
  else if (a === '--strict') opt.strict = true;
  else if (a === '--wait-for') opt.waitFor = argv[++i];
  else if (a === '--storage-state') opt.storageState = argv[++i];
  else if (a === '--cookie') { const v = argv[++i]; const k = v.indexOf('='); if (k > 0) opt.cookies.push({ name: v.slice(0, k), value: v.slice(k + 1) }); }
  else if (a === '--header') { const v = argv[++i]; const k = v.indexOf(':'); if (k > 0) opt.headers[v.slice(0, k).trim()] = v.slice(k + 1).trim(); }
  else if (a === '--auth') { const v = argv[++i]; const k = v.indexOf(':'); if (k > 0) opt.auth = { username: v.slice(0, k), password: v.slice(k + 1) }; }
  else if (a === '--init-script') opt.initScript = argv[++i];
  else if (a === '--mock') { const v = argv[++i]; const k = v.lastIndexOf('='); if (k > 0) opt.mocks.push({ pattern: v.slice(0, k), file: v.slice(k + 1) }); }
  else if (a === '--compare') opt.compare = argv[++i];
  else if (a.startsWith('--')) { console.error(`unknown option ${a}\n${USAGE}`); process.exit(1); }
  else target = a;
}
if (!target || !opt.viewports.length) { console.error(USAGE); process.exit(1); }
const url = /^(https?|file):\/\//i.test(target)
  ? target
  : pathToFileURL(isAbsolute(target) ? target : resolve(target)).href;

import { discoverChromium, launchChromium, loadPlaywright } from './lib/browser.mjs';
let pw;
try { pw = await loadPlaywright(); }
catch (e) { console.error(e.message); process.exit(2); }
async function launch() { return (await launchChromium(pw)).browser; }
void discoverChromium;

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

  // --- page colors (what a theme switch must change)
  const bodyCs = getComputedStyle(document.body);
  const bodyBg = effectiveBackground(document.body);
  const pageColors = {
    background: bodyBg.unverifiable ? null : rgbStr(bodyBg),
    color: (() => { const c = toRGBA(bodyCs.color); return c ? rgbStr(c) : null; })(),
    colorScheme: bodyCs.colorScheme || null,
  };

  // --- contrast on every element that directly contains text
  const contrast = { checked: 0, unverifiable: 0, decorativeSkipped: 0, failures: [] };
  for (const el of all) {
    const tag = el.tagName.toUpperCase();
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEMPLATE' || el.closest('svg')) continue;
    let hasText = false;
    for (const n of el.childNodes) { if (n.nodeType === 3 && n.textContent.trim()) { hasText = true; break; } }
    if (!hasText || !visible(el)) continue;
    // WCAG 1.4.3 exempts pure decoration; an aria-hidden subtree is the author declaring exactly that.
    if (el.closest('[aria-hidden="true"]')) { contrast.decorativeSkipped++; continue; }
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

  // --- interactive elements: size, names, non-text contrast
  const interactive = [...document.querySelectorAll(INTERACTIVE)].filter(visible);
  const targets = { checked: interactive.length, below24: [], between24and44: [] };
  for (const el of interactive) {
    let r = el.getBoundingClientRect();
    // A control's target includes its <label>s (clicking the label activates it), so a
    // 16px radio inside a 44px label row is a 44px target — WCAG 2.5.8 measures the region.
    if (el.labels && el.labels.length) {
      for (const lb of el.labels) {
        const lr = lb.getBoundingClientRect();
        if (!lr.width || !lr.height) continue;
        const left = Math.min(r.left, lr.left), top = Math.min(r.top, lr.top);
        const right = Math.max(r.right, lr.right), bottom = Math.max(r.bottom, lr.bottom);
        r = { left, top, right, bottom, width: right - left, height: bottom - top };
      }
    }
    const cs = getComputedStyle(el);
    const inlineText = cs.display === 'inline' && !!el.closest('p,li,dd,td,th,blockquote,figcaption,small');
    const w = Math.round(r.width), h = Math.round(r.height);
    const item = { selector: short(el), size: `${w}×${h}`, inlineText, viaLabel: !!(el.labels && el.labels.length) };
    if (w < 24 || h < 24) targets.below24.push(item);
    else if (w < 44 || h < 44) targets.between24and44.push(item);
  }
  targets.below24 = targets.below24.slice(0, 30);
  targets.between24and44 = targets.between24and44.slice(0, 30);

  const unnamedControls = interactive.filter((el) => {
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title')) return false;
    if (el.labels && el.labels.length) return false; // <label for> names buttons, inputs, selects, textareas alike
    const tag = el.tagName.toUpperCase();
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
      const type = (el.getAttribute('type') || '').toLowerCase();
      if (['submit', 'button', 'reset', 'image'].includes(type)) return !(el.value || el.getAttribute('alt'));
      return true; // placeholder is not a label
    }
    if ((el.textContent || '').trim()) return false;
    const img = el.querySelector('img[alt]');
    if (img && img.getAttribute('alt').trim()) return false;
    if (el.querySelector('svg title, svg[aria-label]')) return false;
    return true;
  }).map(short).slice(0, 20);

  // --- non-text contrast (WCAG 1.4.11): a control's boundary — its border, or its fill
  //     when it has no border — must reach 3:1 against what surrounds it. Borderless,
  //     unfilled controls are identified by their text, which the text audit covers.
  // Non-text contrast (WCAG 1.4.11). What must reach 3:1 depends on how the control is identified:
  //   - form fields (text inputs, select, textarea): the boundary locates the field → FAIL below 3:1
  //   - controls with no visible text (icon buttons, switches, custom checkboxes): the boundary or
  //     the icon IS the control → FAIL below 3:1
  //   - buttons with a visible text label: the text identifies them, so WCAG does not require the
  //     boundary — but a 1.2:1 surface still reads as unfinished → WARN (`weak`)
  // A boundary passes if EITHER its border or its opaque fill reaches 3:1 against what surrounds it.
  const nonText = { checked: 0, skipped: 0, failures: [], weak: [] };
  const TEXT_LIKE_INPUT = /^(text|email|password|search|tel|url|number|date|datetime-local|month|week|time)$/;
  const boundaryOf = (el, outside) => {
    const cs = getComputedStyle(el);
    const fill0 = toRGBA(cs.backgroundColor);
    const fill = fill0 && fill0.a >= 0.5 ? over(fill0, outside) : null;
    const hasBorder = parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none';
    const border0 = hasBorder ? toRGBA(cs.borderTopColor) : null;
    const border = border0 && border0.a > 0 ? over(border0, fill || outside) : null;
    const cands = [];
    if (border) cands.push({ via: 'border', color: border, ratio: ratio(border, outside) });
    if (fill) cands.push({ via: 'fill', color: fill, ratio: ratio(fill, outside) });
    if (!cands.length) return null;
    return cands.sort((a, b) => b.ratio - a.ratio)[0];
  };
  for (const el of interactive) {
    const tag = el.tagName.toUpperCase();
    const role = el.getAttribute('role') || '';
    const type = (el.getAttribute('type') || 'text').toLowerCase();
    const isField = tag === 'SELECT' || tag === 'TEXTAREA' || (tag === 'INPUT' && TEXT_LIKE_INPUT.test(type));
    const isButtonLike = tag === 'BUTTON' || (tag === 'INPUT' && /^(submit|button|reset)$/.test(type))
      || /^(button|switch|checkbox|radio|tab|menuitem)$/.test(role);
    if (!isField && !isButtonLike) continue;
    if (el.closest('[aria-hidden="true"]')) continue;
    if (!el.parentElement) continue;
    const outside = effectiveBackground(el.parentElement);
    if (!outside || outside.unverifiable) { nonText.skipped++; continue; }
    const labelText = isButtonLike ? (el.innerText || el.value || '').trim() : '';
    let found = boundaryOf(el, outside);
    // A transparent wrapper (e.g. a 44px hit area around a 24px switch track): use the first
    // descendant that draws a boundary, measured against the same surroundings.
    if (!found && isButtonLike && !labelText) {
      for (const child of el.querySelectorAll('*')) {
        if (!visible(child) || child.tagName.toUpperCase() === 'SVG') continue;
        const b = boundaryOf(child, outside);
        if (b) { found = { ...b, via: `${b.via} (child)` }; break; }
      }
    }
    // Icon-only button with no drawn boundary: the icon is the control. Its colour is almost always
    // currentColor, so the button's computed `color` stands in for it.
    if (!found && isButtonLike && !labelText && el.querySelector('svg,img')) {
      const c = toRGBA(getComputedStyle(el).color);
      if (c && c.a > 0) found = { via: 'icon (currentColor)', color: over(c, outside), ratio: ratio(over(c, outside), outside) };
    }
    if (!found) { nonText.skipped++; continue; }  // text-only identification, or nothing drawn
    nonText.checked++;
    if (found.ratio >= 3) continue;
    const entry = { selector: short(el), ratio: +found.ratio.toFixed(2), via: found.via, color: rgbStr(found.color), against: rgbStr(outside) };
    if (isButtonLike && labelText) nonText.weak.push(entry);   // WCAG-exempt, design smell
    else nonText.failures.push(entry);
  }
  nonText.failures.sort((a, b) => a.ratio - b.ratio);
  nonText.failures = nonText.failures.slice(0, 20);
  nonText.weak.sort((a, b) => a.ratio - b.ratio);
  nonText.weak = nonText.weak.slice(0, 20);

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

  // --- stylesheet scan: reduced-motion rule, dark-mode support
  let reducedMotionRule = false, darkMedia = false, darkClass = false;
  const scan = (rules) => {
    for (const rule of rules) {
      if (rule.media) {
        const mt = rule.media.mediaText;
        if (/prefers-reduced-motion/i.test(mt)) reducedMotionRule = true;
        if (/prefers-color-scheme\s*:\s*dark/i.test(mt)) darkMedia = true;
      }
      if (rule.selectorText && /(^|[\s,>+~(])\.dark(\b|\\:)/.test(rule.selectorText)) darkClass = true;
      if (rule.cssRules && rule.cssRules.length) scan(rule.cssRules);
    }
  };
  for (const ss of document.styleSheets) { try { scan(ss.cssRules); } catch { /* cross-origin sheet */ } }
  let animatedElements = 0;
  for (const el of all) { const cs = getComputedStyle(el); if (cs.animationName && cs.animationName !== 'none') animatedElements++; }
  const motion = { reducedMotionRule, animatedElements };
  const darkSupport = { media: darkMedia, class: darkClass, any: darkMedia || darkClass };

  // --- fonts
  // One entry per family, best status wins (a family has one face per weight/style; "loaded"
  // beats "unloaded" — the face simply wasn't needed). next/font's metric-matched local
  // fallbacks ("X Fallback", src: local(...)) and its internal __nextjs-* faces are not
  // web fonts to load, so they never count as errors.
  const fontMap = new Map();
  const rank = { loaded: 3, loading: 2, unloaded: 1, error: 0 };
  document.fonts.forEach((f) => {
    const family = f.family.replace(/["']/g, '');
    if (/ Fallback$/i.test(family) || /^__nextjs-/.test(family)) return;
    const prev = fontMap.get(family);
    if (!prev || rank[f.status] > rank[prev.status]) fontMap.set(family, { family, status: f.status });
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

  return { pageColors, contrast, nonText, targets, unnamedControls, overflow, motion, darkSupport, fonts, imagesMissingAlt, structure, viewportMeta };
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
      // `transition-colors` also transitions outline-color, so right after focus the ring is still
      // fading in from currentColor. Jump every running CSS transition to its end state first;
      // the ring we measure is the one the user sees 150ms later.
      for (const a of el.getAnimations({ subtree: true })) {
        if (a.constructor && a.constructor.name === 'CSSTransition') { try { a.finish(); } catch { /* infinite */ } }
      }
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const onTop = (cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight) ? document.elementFromPoint(cx, cy) : null;
      const obscured = !!onTop && onTop !== el && !el.contains(onTop) && !onTop.contains(el);
      // Focus-ring contrast (WCAG 1.4.11): the indicator against the colour it is drawn over.
      const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
      const toRGBA = (str) => {
        const m = /rgba?\(([^)]+)\)/.exec(str || '');
        if (m) { const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; }
        if (!str || str === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
        try { ctx.fillStyle = '#010203'; ctx.fillStyle = str; if (ctx.fillStyle === '#010203') return null; ctx.clearRect(0, 0, 1, 1); ctx.fillRect(0, 0, 1, 1); const d = ctx.getImageData(0, 0, 1, 1).data; return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 }; } catch { return null; }
      };
      const lum = ({ r, g, b }) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
      const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
      const over = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
      const behind = (() => { // effective background of the parent: what the ring is drawn over
        let node = el.parentElement, layers = [], opaque = null;
        while (node && node.nodeType === 1) { const s = getComputedStyle(node); if (s.backgroundImage !== 'none') return null; const c = toRGBA(s.backgroundColor); if (c && c.a > 0) { if (c.a >= 0.999) { opaque = c; break; } layers.push(c); } node = node.parentElement; }
        let bg = opaque || { r: 255, g: 255, b: 255, a: 1 }; for (let k = layers.length - 1; k >= 0; k--) bg = over(layers[k], bg); return bg;
      })();
      let ringColor = null, ringVia = null;
      if (!/^none/.test(cs.outlineStyle) && parseFloat(cs.outlineWidth) > 0) { ringColor = toRGBA(cs.outlineColor); ringVia = 'outline'; }
      else if (cs.boxShadow && cs.boxShadow !== 'none') { const m = /rgba?\([^)]+\)|#[0-9a-f]{3,8}|[a-z]+\(/i.exec(cs.boxShadow); ringColor = m ? toRGBA(m[0]) : null; ringVia = 'box-shadow'; }
      let ringContrast = null;
      if (ringColor && ringColor.a > 0 && behind) ringContrast = +ratio(ringColor.a < 1 ? over(ringColor, behind) : ringColor, behind).toFixed(2);
      return {
        idx: +el.getAttribute('data-uic-idx'), obscured, obscuredBy: obscured ? (onTop.tagName.toLowerCase() + (onTop.id ? '#' + onTop.id : '')) : null,
        outline: `${cs.outlineStyle} ${cs.outlineWidth}`, boxShadow: cs.boxShadow, borderColor: cs.borderColor, background: cs.backgroundColor, color: cs.color,
        ringVia, ringContrast,
      };
    });
    if (!cur) continue;
    if (seen.has(cur.idx)) break; // cycled back to the start
    seen.add(cur.idx);
    const b = baseline[cur.idx];
    const outlineVisible = !/^none/.test(cur.outline) && !/\b0px$/.test(cur.outline);
    const changed = cur.outline !== b.outline || ['boxShadow', 'borderColor', 'background', 'color'].some((k) => cur[k] !== b[k]);
    results.push({ selector: b.selector, visible: outlineVisible || changed, obscured: cur.obscured, obscuredBy: cur.obscuredBy, ringVia: cur.ringVia, ringContrast: cur.ringContrast });
  }
  await page.evaluate(() => {
    document.querySelectorAll('[data-uic-idx]').forEach((el) => el.removeAttribute('data-uic-idx'));
    if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); // no focus ring in screenshots
  });
  return {
    tabbed: results.length,
    invisible: results.filter((r) => !r.visible).map((r) => r.selector).slice(0, 20),
    obscured: results.filter((r) => r.obscured).map((r) => `${r.selector} (behind ${r.obscuredBy})`).slice(0, 20),
    lowContrastRing: results.filter((r) => r.visible && r.ringContrast !== null && r.ringContrast < 3)
      .map((r) => `${r.selector} (${r.ringVia} ${r.ringContrast}:1)`).slice(0, 20),
  };
}

// ---------------------------------------------------- hover feedback (pointer)
// Does each button / standalone link change *anything* visible on hover? Compared
// on the element and its first descendants, so a group-hover arrow still counts.
async function hoverAudit(page, max = 20) {
  const handles = await page.$$(INTERACTIVE_SELECTOR);
  const results = [];
  let checked = 0;
  for (const h of handles) {
    if (checked >= max) break;
    const info = await h.evaluate((el) => {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (cs.display === 'none' || cs.visibility === 'hidden' || r.width <= 1 || r.height <= 1) return null;
      if (el.closest('[aria-hidden="true"]')) return null;
      if (el.disabled || el.getAttribute('aria-disabled') === 'true') return null; // no state change owed
      const tag = el.tagName.toUpperCase();
      const isButton = tag === 'BUTTON' || el.getAttribute('role') === 'button' || (tag === 'INPUT' && /submit|button|reset/.test(el.type));
      const inlineText = cs.display === 'inline' && !!el.closest('p,li,dd,td,th,blockquote,figcaption,small');
      if (!isButton && (tag !== 'A' || inlineText)) return null; // only buttons and standalone links
      if (el.hasAttribute('aria-current')) return null; // "you are here" — inert by convention
      const sig = (node) => { const s = getComputedStyle(node); return [s.backgroundColor, s.color, s.borderColor, s.boxShadow, s.textDecorationLine, s.transform, s.opacity, s.outlineStyle, s.filter, s.backgroundImage].join('|'); };
      const nodes = [el, ...[...el.querySelectorAll('*')].slice(0, 6)];
      let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id; const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28); if (t) s += ` "${t}"`;
      return { selector: s, before: nodes.map(sig).join('||'), cursor: cs.cursor, isButton, y: r.top + window.scrollY };
    });
    if (!info) continue;
    checked++;
    try { await h.scrollIntoViewIfNeeded({ timeout: 1500 }); await h.hover({ timeout: 1500, force: false }); }
    catch { results.push({ ...info, hovered: false }); continue; }
    await page.waitForTimeout(350); // let transitions finish
    const after = await h.evaluate((el) => {
      const sig = (node) => { const s = getComputedStyle(node); return [s.backgroundColor, s.color, s.borderColor, s.boxShadow, s.textDecorationLine, s.transform, s.opacity, s.outlineStyle, s.filter, s.backgroundImage].join('|'); };
      const nodes = [el, ...[...el.querySelectorAll('*')].slice(0, 6)];
      return { sig: nodes.map(sig).join('||'), cursor: getComputedStyle(el).cursor };
    });
    results.push({ ...info, hovered: true, changed: after.sig !== info.before, cursor: after.cursor });
    await page.mouse.move(0, 0);
    await page.waitForTimeout(120);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  return {
    checked: results.length,
    noHoverFeedback: results.filter((r) => r.hovered && !r.changed).map((r) => r.selector).slice(0, 20),
    cursorNotPointer: results.filter((r) => r.hovered && r.cursor !== 'pointer').map((r) => r.selector).slice(0, 20),
    couldNotHover: results.filter((r) => !r.hovered).map((r) => r.selector).slice(0, 10),
  };
}

// --------------------------------------------- contact sheet: one image to read first
// All viewports' above-the-fold captures side by side at 1× — the first impression at
// every width in a single image, so the model can judge hierarchy and stacking without
// paying for three or six full-page screenshots.
/** Pixel-diff every PNG in `outDir` against the same-named PNG in `baseDir`; writes diff-<name>.png. */
async function compareRuns(browser, outDir, baseDir) {
  const result = { baseline: baseDir, files: {} };
  let names = [];
  try { names = readdirSync(outDir).filter((n) => /\.png$/.test(n) && !/^(diff-|contact)/.test(n)); } catch { return result; }
  const page = await browser.newPage({ viewport: { width: 200, height: 200 }, deviceScaleFactor: 1 });
  for (const name of names) {
    const basePath = join(baseDir, name);
    if (!existsSync(basePath)) { result.files[name] = { status: 'no baseline' }; continue; }
    const a = `data:image/png;base64,${readFileSync(basePath).toString('base64')}`;
    const b = `data:image/png;base64,${readFileSync(join(outDir, name)).toString('base64')}`;
    const r = await page.evaluate(async ([ua, ub]) => {
      const load = (src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
      const [ia, ib] = await Promise.all([load(ua), load(ub)]);
      const w = Math.min(ia.width, ib.width), h = Math.min(ia.height, ib.height);
      const draw = (im) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, 0, 0); return x.getImageData(0, 0, w, h).data; };
      const da = draw(ia), db = draw(ib);
      const out = document.createElement('canvas'); out.width = w; out.height = h;
      const ox = out.getContext('2d'); ox.drawImage(ib, 0, 0); const od = ox.getImageData(0, 0, w, h);
      let changed = 0;
      for (let i = 0; i < da.length; i += 4) {
        const d = Math.abs(da[i] - db[i]) + Math.abs(da[i + 1] - db[i + 1]) + Math.abs(da[i + 2] - db[i + 2]);
        if (d > 48) { changed++; od.data[i] = 255; od.data[i + 1] = 0; od.data[i + 2] = 200; od.data[i + 3] = 255; }
        else { od.data[i] = 128 + od.data[i] / 2; od.data[i + 1] = 128 + od.data[i + 1] / 2; od.data[i + 2] = 128 + od.data[i + 2] / 2; }
      }
      ox.putImageData(od, 0, 0);
      return { w, h, aw: ia.width, ah: ia.height, bw: ib.width, bh: ib.height, changed, total: w * h, png: changed ? out.toDataURL('image/png') : null };
    }, [a, b]);
    const entry = {
      changedPixels: r.changed, comparedPixels: r.total, changedPct: +((100 * r.changed) / r.total).toFixed(2),
      sizeChanged: (r.aw !== r.bw || r.ah !== r.bh) ? `${r.aw}×${r.ah} → ${r.bw}×${r.bh}` : null,
      diff: null,
    };
    if (r.png) {
      const diffPath = join(outDir, `diff-${name}`);
      await writeFile(diffPath, Buffer.from(r.png.split(',')[1], 'base64'));
      entry.diff = `diff-${name}`;
    }
    entry.status = entry.changedPixels === 0 && !entry.sizeChanged ? 'identical' : 'changed';
    result.files[name] = entry;
  }
  await page.close();
  return result;
}

async function contactSheet(browser, outDir, folds, name = 'contact.png') {
  const gap = 24, pad = 24, labelH = 28;
  const totalW = pad * 2 + folds.reduce((s, f) => s + f.width, 0) + gap * (folds.length - 1);
  const maxH = Math.max(...folds.map((f) => f.height));
  const page = await browser.newPage({ viewport: { width: totalW, height: pad * 2 + labelH + maxH }, deviceScaleFactor: 1 });
  const cells = folds.map((f) => {
    const src = `data:image/png;base64,${readFileSync(f.path).toString('base64')}`;
    return `<figure style="margin:0;width:${f.width}px;flex:none">` +
      `<figcaption style="font:600 14px system-ui,sans-serif;line-height:${labelH}px;height:${labelH}px;color:#333">${f.label || `${f.width} × ${f.height}`}</figcaption>` +
      `<img src="${src}" style="width:${f.width}px;height:${f.height}px;display:block;border:1px solid #bbb;box-sizing:border-box;background:#fff"></figure>`;
  }).join('');
  await page.setContent(
    `<!doctype html><body style="margin:0;padding:${pad}px;background:#e6e6e6;display:flex;gap:${gap}px;align-items:flex-start">${cells}</body>`,
    { waitUntil: 'load' },
  );
  await page.screenshot({ path: join(outDir, name) });
  await page.close();
}

// -------------------------------------------------------------------- main
const browser = await launch();
await mkdir(opt.out, { recursive: true });
const report = { target: url, generatedAt: new Date().toISOString(), viewports: {}, summary: {} };
let anyFail = false;
const folds = [];
const darkFolds = [];
const widest = Math.max(...opt.viewports);

for (const width of opt.viewports) {
  const height = width < 600 ? 812 : width < 1000 ? 1024 : 900;
  const context = await browser.newContext({
    viewport: { width, height }, deviceScaleFactor: 2,
    storageState: opt.storageState || undefined,
    extraHTTPHeaders: Object.keys(opt.headers).length ? opt.headers : undefined,
    httpCredentials: opt.auth || undefined,
  });
  if (opt.cookies.length && /^https?:/.test(url)) {
    await context.addCookies(opt.cookies.map((c) => ({ ...c, url })));
  }
  if (opt.initScript) await context.addInitScript({ path: opt.initScript });
  for (const m of opt.mocks) {
    const body = readFileSync(m.file);
    const type = /\.json$/i.test(m.file) ? 'application/json' : /\.html?$/i.test(m.file) ? 'text/html' : /\.js$/i.test(m.file) ? 'application/javascript' : /\.png$/i.test(m.file) ? 'image/png' : /\.svg$/i.test(m.file) ? 'image/svg+xml' : 'text/plain';
    const matcher = /^\/.*\/$/.test(m.pattern) ? new RegExp(m.pattern.slice(1, -1)) : m.pattern;
    await context.route(matcher, (route) => route.fulfill({ status: 200, contentType: type, body }));
  }
  const page = await context.newPage();
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
    if (opt.waitFor) await page.waitForSelector(opt.waitFor, { timeout: 30000 });
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
  const hover = (!loadError && opt.hover && width === widest) ? await hoverAudit(page) : null;
  if (!loadError) await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(100);
  if (opt.fold) {
    const foldPath = join(opt.out, `${key}-fold.png`);
    await page.screenshot({ path: foldPath });
    folds.push({ width, height, path: foldPath });
  }
  await page.screenshot({ path: join(opt.out, `${key}-full.png`), fullPage: true });

  // --- dark-mode pass: only when the page has a dark rule (or --dark). Same audit, new colours.
  let dark = null;
  const wantDark = !loadError && opt.dark !== 'skip' && (opt.dark === 'force' || (audit && audit.darkSupport.any));
  if (wantDark) {
    await page.emulateMedia({ colorScheme: 'dark' });
    if (audit && audit.darkSupport.class) await page.evaluate(() => document.documentElement.classList.add('dark'));
    await page.waitForTimeout(350);
    const dAudit = await page.evaluate(domAudit, INTERACTIVE_SELECTOR);
    const dFocus = await focusAudit(page);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(100);
    let dFold = null;
    if (opt.fold) {
      dFold = join(opt.out, `${key}-dark-fold.png`);
      await page.screenshot({ path: dFold });
      darkFolds.push({ width, height, path: dFold, label: `${width} × ${height} · dark` });
    }
    const changed = !!(audit && dAudit.pageColors.background && audit.pageColors.background !== dAudit.pageColors.background);
    dark = {
      mode: audit && audit.darkSupport.class && !audit.darkSupport.media ? 'class' : 'media',
      forced: opt.dark === 'force',
      themeChanged: changed,
      pageColors: dAudit.pageColors,
      contrast: dAudit.contrast, nonText: dAudit.nonText,
      focus: { invisible: dFocus.invisible, lowContrastRing: dFocus.lowContrastRing },
      screenshot: dFold ? `${key}-dark-fold.png` : null,
    };
    await page.emulateMedia({ colorScheme: 'light' });
  }

  const fails = [], warns = [];
  if (loadError) fails.push(`load error: ${loadError}`);
  if (audit) {
    if (audit.contrast.failures.length) fails.push(`contrast ${audit.contrast.failures.length}`);
    if (audit.nonText.failures.length) fails.push(`non-text contrast ${audit.nonText.failures.length}`);
    if (audit.overflow.horizontal) fails.push(`horizontal overflow ${audit.overflow.scrollWidth}>${audit.overflow.viewportWidth}`);
    const hard24 = audit.targets.below24.filter((t) => !t.inlineText).length;
    if (hard24) fails.push(`targets<24px ${hard24}`);
    if (audit.unnamedControls.length) fails.push(`unnamed controls ${audit.unnamedControls.length}`);
    if (audit.imagesMissingAlt.length) fails.push(`img without alt ${audit.imagesMissingAlt.length}`);
    if (audit.viewportMeta.blocksZoom) fails.push('zoom blocked');
    if (audit.nonText.weak.length) warns.push(`weak button surface <3:1 ${audit.nonText.weak.length}`);
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
    if (focus.lowContrastRing.length) fails.push(`focus ring <3:1 ${focus.lowContrastRing.length}`);
  }
  if (hover) {
    if (hover.noHoverFeedback.length) warns.push(`no hover feedback ${hover.noHoverFeedback.length}`);
    if (hover.cursorNotPointer.length) warns.push(`cursor not pointer ${hover.cursorNotPointer.length}`);
  }
  if (dark) {
    if (dark.contrast.failures.length) fails.push(`dark contrast ${dark.contrast.failures.length}`);
    if (dark.nonText.failures.length) fails.push(`dark non-text contrast ${dark.nonText.failures.length}`);
    if (dark.focus.invisible.length) fails.push(`dark focus invisible ${dark.focus.invisible.length}`);
    if (dark.focus.lowContrastRing.length) fails.push(`dark focus ring <3:1 ${dark.focus.lowContrastRing.length}`);
    if (dark.nonText.weak.length) warns.push(`dark weak button surface <3:1 ${dark.nonText.weak.length}`);
    if (!dark.themeChanged && !dark.forced) warns.push('dark rule present but page colours did not change');
  }
  if (consoleErrors.length) warns.push(`console errors ${consoleErrors.length}`);
  if (failedRequests.length) warns.push(`failed requests ${failedRequests.length}`);
  if (httpErrors.length) warns.push(`http errors ${httpErrors.length}`);

  const status = fails.length ? 'FAIL' : 'PASS';
  if (fails.length) anyFail = true;
  report.viewports[key] = {
    width, height, status, fails, warns, loadError,
    console: consoleErrors.slice(0, 20), failedRequests: failedRequests.slice(0, 20), httpErrors: httpErrors.slice(0, 20),
    audit, focus, hover, dark,
    screenshots: { fold: opt.fold ? `${key}-fold.png` : null, full: `${key}-full.png`, darkFold: dark && dark.screenshot },
  };
  await context.close();
}
if (folds.length) await contactSheet(browser, opt.out, folds);
if (opt.compare) report.compare = await compareRuns(browser, opt.out, opt.compare);
if (darkFolds.length) await contactSheet(browser, opt.out, darkFolds, 'contact-dark.png');
await browser.close();

report.summary = {
  status: anyFail ? 'FAIL' : 'PASS',
  viewports: Object.fromEntries(Object.entries(report.viewports).map(([k, v]) => [k, v.status])),
  contact: folds.length ? 'contact.png' : null,
  contactDark: darkFolds.length ? 'contact-dark.png' : null,
  darkRendered: darkFolds.length > 0 || Object.values(report.viewports).some((v) => v.dark),
};
await writeFile(join(opt.out, 'report.json'), JSON.stringify(report, null, 2));

// ------------------------------------------------------------------ output
console.log(`ui-craft render → ${opt.out}`);
console.log(`  target: ${url}`);
if (folds.length) console.log(`  look first: ${join(opt.out, 'contact.png')} (all viewports, above the fold, one image)${darkFolds.length ? ` · dark: ${join(opt.out, 'contact-dark.png')}` : ''}`);
for (const [k, v] of Object.entries(report.viewports)) {
  const detail = [...v.fails, ...v.warns.map((w) => `warn:${w}`)].join(' · ') || 'clean';
  console.log(`  ${k.padEnd(5)} ${v.status}  ${detail}`);
}
if (report.compare) {
  const fs_ = Object.entries(report.compare.files);
  const changed = fs_.filter(([, f]) => f.status === 'changed');
  console.log(`  compare vs ${report.compare.baseline}: ${fs_.length - changed.length} identical, ${changed.length} changed${changed.length ? ' — ' + changed.map(([n, f]) => `${n} ${f.changedPct}%${f.sizeChanged ? ` (${f.sizeChanged})` : ''}`).join(', ') : ''}`);
}
const first = Object.values(report.viewports).find((v) => v.audit);
if (first) {
  const fam = first.audit.fonts.declared;
  const line = fam.length ? fam.map((f) => `${f.family} (${f.status})`).join(', ') : 'none declared';
  console.log(`  fonts: ${line}; used: ${first.audit.fonts.used.join(', ')}`);
  console.log(`  dark mode: ${first.audit.darkSupport.any ? `supported (${first.audit.darkSupport.media ? 'media' : ''}${first.audit.darkSupport.media && first.audit.darkSupport.class ? '+' : ''}${first.audit.darkSupport.class ? 'class' : ''})` : 'not implemented'}${report.summary.darkRendered ? ' — rendered and audited' : ''}`);
}
const top = (arr, n, fmt) => arr.slice(0, n).map(fmt).map((s) => `      ${s}`).join('\n');
for (const [k, v] of Object.entries(report.viewports)) {
  if (!v.audit) continue;
  const lines = [];
  if (v.audit.contrast.failures.length) lines.push(`    contrast:\n${top(v.audit.contrast.failures, 6, (f) => `${f.ratio}:1 (need ${f.required}) ${f.selector} — ${f.color} on ${f.background}`)}`);
  if (v.audit.nonText.failures.length) lines.push(`    non-text contrast:\n${top(v.audit.nonText.failures, 5, (f) => `${f.ratio}:1 (need 3) ${f.selector} — ${f.via} ${f.color} against ${f.against}`)}`);
  if (v.audit.nonText.weak.length) lines.push(`    weak button surface (WCAG-exempt, text-labelled):\n${top(v.audit.nonText.weak, 4, (f) => `${f.ratio}:1 ${f.selector} — ${f.via} ${f.color} against ${f.against}`)}`);
  if (v.audit.overflow.horizontal) lines.push(`    overflow:\n${top(v.audit.overflow.offenders, 4, (o) => `${o.selector} right=${o.right}`)}`);
  const hard = v.audit.targets.below24.filter((t) => !t.inlineText);
  if (hard.length) lines.push(`    targets<24:\n${top(hard, 6, (t) => `${t.size} ${t.selector}`)}`);
  if (v.focus && v.focus.invisible.length) lines.push(`    focus invisible:\n${top(v.focus.invisible, 6, (s) => s)}`);
  if (v.focus && v.focus.obscured.length) lines.push(`    focus obscured:\n${top(v.focus.obscured, 4, (s) => s)}`);
  if (v.focus && v.focus.lowContrastRing.length) lines.push(`    focus ring <3:1:\n${top(v.focus.lowContrastRing, 4, (s) => s)}`);
  if (v.hover && v.hover.noHoverFeedback.length) lines.push(`    no hover feedback:\n${top(v.hover.noHoverFeedback, 6, (s) => s)}`);
  if (v.dark && v.dark.nonText.failures.length) lines.push(`    dark non-text contrast:\n${top(v.dark.nonText.failures, 5, (f) => `${f.ratio}:1 (need 3) ${f.selector} — ${f.via} ${f.color} against ${f.against}`)}`);
  if (v.dark && v.dark.focus.lowContrastRing.length) lines.push(`    dark focus ring <3:1:\n${top(v.dark.focus.lowContrastRing, 4, (s) => s)}`);
  if (v.dark && v.dark.contrast.failures.length) lines.push(`    dark contrast:\n${top(v.dark.contrast.failures, 6, (f) => `${f.ratio}:1 (need ${f.required}) ${f.selector} — ${f.color} on ${f.background}`)}`);
  if (v.audit.unnamedControls.length) lines.push(`    unnamed:\n${top(v.audit.unnamedControls, 6, (s) => s)}`);
  if (v.audit.imagesMissingAlt.length) lines.push(`    img without alt:\n${top(v.audit.imagesMissingAlt, 4, (s) => s)}`);
  if (lines.length) console.log(`  ${k}:\n${lines.join('\n')}`);
}
// ---- the Verified block: the numbers the report to the user is made of. Paste it; don't recompute.
{
  const vps = Object.values(report.viewports).filter((v) => v.audit);
  if (vps.length) {
    const widest = vps.reduce((a, b) => (a.width > b.width ? a : b));
    const worst = (fn) => vps.reduce((m, v) => { const n = fn(v) || 0; return n > m.n ? { n, w: v.width } : m; }, { n: 0, w: null });
    const at = (m) => (m.n && vps.length > 1 ? ` (worst at ${m.w})` : '');
    const L = [];
    const cf = worst((v) => v.audit.contrast.failures.length), bf = worst((v) => v.audit.nonText.failures.length);
    const unv = widest.audit.contrast.unverifiable || 0;
    L.push(`- Contrast: ${widest.audit.contrast.checked} text elements, ${cf.n} below threshold${at(cf)} · ${widest.audit.nonText.checked} control boundaries, ${bf.n} below 3:1${at(bf)}${unv ? ` · ${unv} unverifiable (image or gradient backgrounds)` : ''}`);
    const darks = vps.filter((v) => v.dark);
    if (darks.length) {
      const dw = darks.reduce((a, b) => (a.width > b.width ? a : b));
      const df = worst((v) => v.dark ? v.dark.contrast.failures.length : 0), dbf = worst((v) => v.dark ? v.dark.nonText.failures.length : 0);
      const dr = worst((v) => v.dark ? v.dark.focus.lowContrastRing.length : 0);
      L.push(`- Dark mode: rendered (${dw.dark.mode}) · ${dw.dark.contrast.checked} text elements, ${df.n} below threshold${at(df)} · ${dw.dark.nonText.checked} boundaries, ${dbf.n} below 3:1 · ${dr.n} focus rings below 3:1 · background ${widest.audit.pageColors.background} → ${dw.dark.pageColors.background}${dw.dark.themeChanged ? '' : ' (unchanged!)'}`);
    } else {
      L.push(`- Dark mode: ${widest.audit.darkSupport.any ? 'rule present but not rendered' : 'no dark rule — not rendered'}`);
    }
    const t24 = worst((v) => v.audit.targets.below24.filter((t) => !t.inlineText).length), t44 = worst((v) => v.audit.targets.between24and44.length);
    L.push(`- Targets: ${t24.n} below 24px${at(t24)} · ${t44.n} between 24–44px${at(t44)}`);
    const ov = vps.filter((v) => v.audit.overflow.horizontal).map((v) => `${v.width} (${v.audit.overflow.scrollWidth}>${v.audit.overflow.viewportWidth})`);
    L.push(`- Overflow: ${ov.length ? 'horizontal at ' + ov.join(', ') : 'none at ' + vps.map((v) => v.width).join(' / ')}`);
    const f = widest.focus, h = widest.hover;
    const focusLine = f ? `${f.tabbed - f.invisible.length}/${f.tabbed} tabbed show a visible ring, ${f.lowContrastRing.length} rings below 3:1, ${f.obscured.length} obscured` : 'not probed';
    const hoverLine = h ? `${h.checked - h.noHoverFeedback.length}/${h.checked} buttons and links respond${h.cursorNotPointer.length ? `, ${h.cursorNotPointer.length} without pointer cursor` : ''}` : 'not probed';
    L.push(`- Focus: ${focusLine} · Hover: ${hoverLine}`);
    L.push(`- Motion: reduced-motion rule ${widest.audit.motion.reducedMotionRule ? 'present' : 'missing'} · ${widest.audit.motion.animatedElements} animated elements`);
    const un = worst((v) => v.audit.unnamedControls.length), ia = worst((v) => v.audit.imagesMissingAlt.length);
    L.push(`- Names & alt: ${un.n} unnamed controls · ${ia.n} images without alt · ${widest.audit.structure.h1Count} h1 · ${widest.audit.structure.skippedLevels.length} skipped heading levels`);
    const decl = widest.audit.fonts.declared, errs = decl.filter((x) => x.status === 'error').map((x) => x.family);
    L.push(`- Fonts: ${decl.length ? `${decl.length} declared, ${errs.length ? `${errs.length} failed to load (${[...new Set(errs)].join(', ')}) — rendered with fallbacks` : 'all loaded'}` : 'none declared (system stack)'}`);
    if (report.compare) {
      const fs_ = Object.entries(report.compare.files);
      const changed = fs_.filter(([, f]) => f.status === 'changed');
      L.push(`- Compared with ${report.compare.baseline}: ${changed.length ? changed.map(([n, f]) => `${n.replace('.png', '')} ${f.changedPct}% changed${f.sizeChanged ? ` (${f.sizeChanged})` : ''}`).join(' · ') : `all ${fs_.length} screenshots identical`}`);
    }
    console.log(`\nVerified (render.mjs · ${opt.out}):\n${L.join('\n')}`);
  }
}
console.log(`  full report: ${join(opt.out, 'report.json')}`);
process.exit(opt.strict && anyFail ? 1 : 0);
