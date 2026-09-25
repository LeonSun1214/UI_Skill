#!/usr/bin/env node
/**
 * ui-craft critique — a second pair of eyes that did not build the page.
 *
 *   node critique.mjs .ui-craft/pricing-1/contact.png [--brief "one line: audience, feel, the deliberate move"]
 *                     [--dark .ui-craft/pricing-1/contact-dark.png] [--model <id>] [--json]
 *
 * Sends the contact sheet (three viewports above the fold, one image) to a fresh `claude -p`
 * session that sees only the pixels and the brief — no code, no summary, no memory of the
 * choices made — and asks for rubric scores 1–5 plus the three changes that would most
 * improve the page. Self-review is anchored on what one just decided; this is not.
 *
 * Prints the scores, the verdict and the three changes; with --json, the raw object.
 * Needs the `claude` CLI on PATH (Claude Code). Exit 0 always — the critique is advice,
 * the verdict is the workflow's to act on (SKILL.md step 4d).
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log('usage: node critique.mjs <contact.png> [--brief "…"] [--dark <contact-dark.png>] [--model <id>] [--json]');
  process.exit(argv.length ? 0 : 1);
}
const opt = { image: null, dark: null, brief: '', model: null, json: false };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--brief') opt.brief = argv[++i] || '';
  else if (a === '--dark') opt.dark = argv[++i];
  else if (a === '--model') opt.model = argv[++i];
  else if (a === '--json') opt.json = true;
  else opt.image = a;
}
if (!opt.image || !existsSync(opt.image)) { console.error(`contact sheet not found: ${opt.image}`); process.exit(1); }
const image = resolve(opt.image);
const dark = opt.dark && existsSync(opt.dark) ? resolve(opt.dark) : null;

const prompt = `You are a senior product designer giving a candid review of a web page from screenshots. You have not seen the code or talked to whoever built it. Use the Read tool to view the image at ${image} — a contact sheet: the same page above the fold at 375, 768 and 1440 px, side by side.${dark ? ` Then view ${dark}, the same page in dark mode.` : ''}
${opt.brief ? `\nThe brief the page was built to: ${opt.brief}\n` : ''}
Judge only what the pixels show, at every width:
- Hierarchy: does one thing win the first three seconds, then a clear second and third? Do size, weight and colour change between levels? Exactly one primary action per view?
- Distinctive: among ten SaaS sites, would you stop on this one? Is there a deliberate typographic, colour or layout choice, or is it indigo + Inter + three icon cards with different paint?
- Typography: does a display face do something the body face can't? Sane measure and line-height? Widows? Tabular numbers where they align?
- Spacing & alignment: a scale, not arbitrary gaps; related things closer than unrelated; left edges lining up; cards aligned across a row; nothing cramped, no dead bands.
- Color: does the accent have one job? Do neutrals carry structure? Does muted text still read on tinted surfaces? Any colour used decoratively that should mean something, or vice versa?
- Narrow column (375): does the stacking still tell the story? Anything tiny, clipped or six lines long?

Score each dimension 1–5 (1 = template-grade or broken, 3 = competent and forgettable, 4 = a page you would ship with one round of notes, 5 = portfolio work). Be strict: 4 and 5 must be earned. Then name the THREE changes that would most improve the page, each as one line "what · where · why" with concrete values (sizes, colours, spacing) where they apply — not adjectives. Finally say whether a design lead would ship it as is.

Reply with ONLY a JSON object, no prose before or after:
{"hierarchy": n, "distinctive": n, "typography": n, "spacing": n, "color": n, "overall": n, "ship": true|false, "first_impression": "one sentence", "changes": ["what · where · why", "what · where · why", "what · where · why"]}`;

const cmd = ['-p', prompt, '--output-format', 'json', '--allowedTools', 'Read'];
if (opt.model) cmd.push('--model', opt.model);
const env = { ...process.env };
delete env.CLAUDECODE; // allow nesting inside a Claude Code session
const r = spawnSync('claude', cmd, { cwd: dirname(image), env, encoding: 'utf8', timeout: 240000, stdio: ['ignore', 'pipe', 'pipe'] });
if (r.error) {
  console.error(`could not run the claude CLI (${r.error.message}). The critique needs Claude Code on this machine; skip it and say so in the report.`);
  process.exit(0);
}
let outer = null;
try { outer = JSON.parse(r.stdout || '{}'); } catch { /* fall through */ }
const text = outer && typeof outer.result === 'string' ? outer.result : (r.stdout || '');
const s = text.indexOf('{'), e = text.lastIndexOf('}');
let data = null;
if (s >= 0 && e > s) { try { data = JSON.parse(text.slice(s, e + 1)); } catch { /* fall through */ } }
if (!data) {
  console.error(`critique did not return JSON: ${text.slice(0, 300) || (r.stderr || '').slice(0, 300)}`);
  process.exit(0);
}
data.image = image;
if (dark) data.dark = dark;
if (outer && outer.total_cost_usd != null) data.cost_usd = outer.total_cost_usd;

if (opt.json) { console.log(JSON.stringify(data, null, 2)); process.exit(0); }
const dims = ['hierarchy', 'distinctive', 'typography', 'spacing', 'color', 'overall'];
console.log(`Critique (independent, pixels only · ${image}):`);
console.log(`- Scores: ${dims.map((d) => `${d} ${data[d] ?? '?'}`).join(' · ')}  → ${data.ship ? 'would ship' : 'would NOT ship as is'}`);
if (data.first_impression) console.log(`- First impression: ${data.first_impression}`);
for (const [i, c] of (data.changes || []).entries()) console.log(`- Change ${i + 1}: ${c}`);
const low = dims.filter((d) => typeof data[d] === 'number' && data[d] <= 3 && d !== 'overall');
// A round is owed when the critic would not ship it, or when two or more dimensions sit at 3 or
// below. One 3 under a ship verdict is a note for the report (SKILL.md step 4d).
if (data.ship === false || low.length >= 2) console.log(`- Round owed: ${data.ship === false ? 'would not ship' : 'two or more dimensions at 3 or below'}${low.length ? ` (${low.join(', ')})` : ''} — apply the three changes and render once more (SKILL.md step 4d)`);
else if (low.length === 1) console.log(`- ${low[0]} at ${data[low[0]]}: note it in the report; no further round (ship verdict, one dimension)`);
else console.log('- Nothing below 4.');
