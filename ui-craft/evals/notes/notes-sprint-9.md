# Sprint 9 — the reading list

## 9a — inspect.py opens with "Start here"

Both real-repository trials spent about two thirds of their wall clock reading
files to learn what a match task needs to know: which classes the CSS defines
and what they expand to, which components every page imports and what props they
take, which page is the nearest sibling, where the strings live, and what stands
between a fresh browser and the page. `inspect.py` now says all of it in its first
section, so the model reads the one sibling page and nothing else.

On Sunnotice's frontend the section is 45 lines: sixteen component classes with
their `@apply` lines by use (`.muted` ×165 … `.pill` ×17), twelve most-imported
modules with prop names for the components (`Avatar (member, size, title)`,
`Icon (name, size, label, className, …rest)`), eleven pages with signals
(`Team.tsx · 711 lines · form, 5 fields, list · muted ×19, btn-quiet ×12 · imports
Avatar, LoadBar`), the eight routes, the two dictionaries and which is typed, and
five lines on what runs first: the theme script, the splash and its storage key,
the five early returns in `App.tsx` in order, the store's calls through `api.ts`
with the `/api` base, the vite proxy target and `dev.sh`. In the first trial those
facts cost fifteen file reads; in the second, the api call shape cost one wrong
guess and a render of the wrong page.

## 9b — measured on eval-2: no difference, and why

One run of the match task (a second settings page in a two-page fixture) with the
new section, against the three iteration-4 runs:

| | reads before first render | tool calls before first render | tokens (comparable) |
|---|---|---|---|
| iteration-4, three runs | 3 · 7 · 6 | 7 · 12 · 14 | 111k · 145k · 121k |
| iteration-5, one run | 4 | 10 | 127k |

Inside the spread, not below it. The fixture has two pages and five primitives;
the run still opened the sibling page and the four primitives it would reuse,
which is the reading the section is meant to replace only when the project is
big enough for finding them to cost something. The run read the primitives for
their props, which is why 9a now prints prop names. The number that matters is
the next real-repository task's read count against the fifteen of the first
trial, and it has not been measured yet.
