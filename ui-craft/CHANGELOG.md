# Changelog

## 0.6.0 — facts, and a tuned description

- `verify.py`: every imported package must be installed, every icon name exported by
  its package (closest real name suggested), every Google Fonts family and weight
  must exist and carry the subset the page's language needs, every `@font-face`
  file must exist; a font-family nothing loads is a WARN. Bundled catalog of 1,908
  Google Fonts families (`scripts/data/google-fonts.json`, Jan 2026 snapshot).
- `facts` assertion in every eval; SKILL.md runs `verify.py` before the first render
  and pastes its `Facts:` line into the report.
- The description was re-tuned on a 20-query trigger eval set (see
  `evals/trigger-eval.json`).

## 0.5.0 — real projects, and a product

- `render.mjs`: `--storage-state`, `--cookie`, `--header`, `--auth` (logged-in pages);
  `--init-script`, `--mock` (data without a backend); `--wait-for` (late hydration);
  `--compare DIR` (pixel diff against a previous run, `diff-*.png`). Font entries are
  one per family; next/font fallbacks no longer count as load errors. Disabled
  controls are not probed for hover.
- `harness.mjs`: render one component in isolation (Vite + React), one cell per state.
- `login-state.mjs`: capture a session in a visible browser for `--storage-state`.
- `inspect.py`: Vue, Nuxt, Svelte, SvelteKit, Angular, Solid in the stack line;
  workspace roots list their UI app packages.
- `doctor.mjs` (`npm run doctor`), `selftest.mjs` (`npm test`, 11 checks on pages
  with planted defects), `install.sh`, CI workflow, README, this file.
- Next.js App Router fixture (`evals/fixtures/nextjs`).

## 0.4.0 — cost rules

- Seven cost rules at the top of SKILL.md: scripts are black boxes, no `report.json`
  dumps, no home-made probes, an image budget, no environment audits, match tasks read
  nothing extra, twenty-line reports.
- `render.mjs` ends with a pasteable `Verified` block.
- `contrast.py`: ratios for pairs or a CSS token file, light and dark side by side.
- Token accounting: interruption re-cache and the shared harness prefix split out so
  runs compare fairly.

## 0.3.0 — deeper instruments

- Dark-mode pass (media or `.dark` class) with its own contrast, boundary and focus
  audit and `contact-dark.png`.
- Non-text contrast per WCAG 1.4.11 (fields, icon buttons, switches FAIL; text
  buttons WARN), focus-ring contrast measured after transitions finish, hover
  feedback and cursor probe, `pageColors`.
- Eval 4 (dark mode on Maple Books); every route of an eval is graded.

## 0.2.0 — cost control

- Adaptive verify rounds (clean round 1 delivers; two-round ceiling), contact sheets
  at 1×, read the contact sheet before any full-page image, no confirmation renders.

## 0.1.0 — first version

- SKILL.md workflow (classify → inspect → brief → build → verify → report),
  `render.mjs` (screenshots + DOM audits), `inspect.py`, four references, three
  fixtures and the three-way benchmark against ui-ux-pro-max and no skill.
