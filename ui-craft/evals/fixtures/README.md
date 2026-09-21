# Eval fixtures

Three small Vite + React 19 + Tailwind 4 projects used by `../evals.json`. They share
one `node_modules` (installed here, in this folder) so each fixture stays tiny.

| Fixture | Tests | Starting point |
|---|---|---|
| `greenfield/` | direction-setting, anti-generic, the verify loop | empty `App.tsx`, no tokens |
| `established/` | `inspect.py` → *match* existing conventions | warm palette, Fraunces + IBM Plex, `rounded-md`, hairline borders, `Button`/`Switch`/`Card`/`Field` primitives, a `/settings/profile` page showing the form convention |
| `generic/` | critique + one deliberate move away from the template look | a deliberately AI-default marketing page (indigo, gradient blob, icon-in-circle cards, fake logos and stats) |

## Running a fixture

Fixtures are pristine templates. Never work in them directly — copy one to a work
directory, link the shared dependencies, and run the dev server there:

```bash
cp -r evals/fixtures/established /path/to/work/project
ln -s "$(pwd)/evals/fixtures/node_modules" /path/to/work/project/node_modules
cd /path/to/work/project && npm run dev -- --port 5173
```

Install the shared dependencies once: `cd evals/fixtures && npm install`.
