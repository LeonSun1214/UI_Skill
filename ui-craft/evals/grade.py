#!/usr/bin/env python3
"""Grade ui-craft eval runs objectively.

For every <iteration>/eval-*/<config>/run-*/ that has a project/:
  1. boot the project's Vite dev server on a free port
  2. render the eval's route with ui-craft's own render.mjs → run-N/grader-render/
  3. evaluate each assertion in eval_metadata.json with a programmatic checker
     (the assertion's id is the text before the first colon)
  4. write run-N/grading.json in the skill-creator schema (text / passed / evidence)

The grader never trusts a run's own report.json: it re-measures everything.

Usage: python3 <skill>/evals/grade.py <workspace>/iteration-N [--only eval-2-established-match] [--skip-render]

Layout expected (what skill-creator's aggregator and viewer read):
  iteration-N/eval-<id>-<name>/{with_skill,without_skill}/run-1/{project,outputs,timing.json}
  with eval_metadata.json in the eval dir and in each config dir.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # <skill>/evals
SKILL = HERE.parent                                 # <skill>
RENDER = SKILL / "scripts" / "render.mjs"
FIXTURES = SKILL / "evals" / "fixtures"
ROUTES = {1: ["/"], 2: ["/settings/notifications"], 3: ["/"], 4: ["/", "/settings/profile"]}  # every route is graded
FIXTURE_FOR = {1: "greenfield", 2: "established", 3: "generic", 4: "established"}
FIXTURE_LIGHT_BG = {4: "rgb(251, 248, 243)"}  # Maple Books paper — must survive a dark-mode addition
# Maple Books ships `--color-line: #e5ddd3` (1.35:1 on white) on its Field border and Switch track. The
# established-project evals forbid touching shared tokens/primitives, so boundaries drawn in that token
# are the fixture's defect, not the run's: exempt them from the light-mode non-text check. Dark mode is
# entirely the run's own palette and is checked in full.
FIXTURE_LINE = {2: "rgb(229, 221, 211)", 4: "rgb(229, 221, 211)"}
VIEWPORTS = ("375", "768", "1440")
SKIP = {"node_modules", ".vite-cache", ".ui-craft", "dist"}

TW = "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose"
PREFIX = r"(?:bg|text|border|ring|from|via|to|fill|stroke|outline|decoration|divide|placeholder|shadow)"
RAW_PALETTE = re.compile(rf"(?<![\w-]){PREFIX}-(?:{TW})-\d{{2,3}}(?:/\d+)?(?![\w-])")
INDIGO = re.compile(rf"(?<![\w-]){PREFIX}-(?:indigo|violet|purple)-\d{{2,3}}(?:/\d+)?(?![\w-])")
ICON_BADGE = re.compile(r"rounded-full[^\"'\n]*bg-[a-z]+-100|bg-[a-z]+-100[^\"'\n]*rounded-full")
COPY_ANCHORS = ["智能排队", "实时通知", "数据分析", "王经理", "李女士", "张总", "基础版", "专业版", "准备好开始了吗"]
TELL_GROUPS = [
    r"indigo|靛|紫|violet|purple", r"渐变|gradient", r"图标|圆形|圆圈|circle|icon",
    r"\bInter\b|字体|font|typeface|serif", r"模板|template|generic|AI ?味|同质|千篇一律",
]
NEEDS_RENDER = {"renders", "contrast", "overflow", "targets", "focus", "labels", "motion",
                "hover-feedback", "non-text-contrast", "dark-support", "dark-contrast", "light-unchanged"}


# ------------------------------------------------------------------ helpers
def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def source_files(project: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for root, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for n in names:
            p = Path(root) / n
            if p.suffix in {".tsx", ".jsx", ".ts", ".js", ".css", ".html"}:
                files[str(p.relative_to(project))] = read(p)
    return files


def theme_block(css: str) -> str:
    m = re.search(r"@theme\b[^{]*\{", css)
    if not m:
        return ""
    depth, i = 0, m.end() - 1
    for j in range(i, len(css)):
        if css[j] == "{":
            depth += 1
        elif css[j] == "}":
            depth -= 1
            if depth == 0:
                return re.sub(r"\s+", "", css[i + 1:j])
    return ""


def free_port(start: int) -> int:
    for p in range(start, start + 100):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("no free port")


def boot(project: Path, port: int, log: Path):
    proc = subprocess.Popen(
        ["npx", "vite", "--port", str(port), "--strictPort", "--clearScreen", "false"],
        cwd=project, stdout=open(log, "w"), stderr=subprocess.STDOUT, start_new_session=True,
    )
    for _ in range(90):
        with socket.socket() as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
                time.sleep(0.5)
                return proc
            except OSError:
                pass
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    stop(proc)
    return None


def stop(proc) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass


def render(port: int, route: str, out: Path) -> tuple[dict | None, str]:
    url = f"http://127.0.0.1:{port}{route}"
    try:
        r = subprocess.run(["node", str(RENDER), url, "--out", str(out)], capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, "render.mjs timed out"
    rep = out / "report.json"
    if not rep.exists():
        return None, (r.stdout + r.stderr)[-400:]
    return json.loads(read(rep)), ""


# ----------------------------------------------------------------- checkers
def A(ctx, w):
    return ctx["rep"]["viewports"][w]["audit"]


def c_renders(ctx):
    rep = ctx["rep"]
    errs = [f"{w}: {v.get('loadError')}" for w, v in rep["viewports"].items() if v.get("loadError")]
    if errs:
        return False, "load errors: " + "; ".join(errs)
    st = A(ctx, "1440")["structure"]
    h1s = [h["text"] for h in st["headings"] if h["level"] == 1]
    if st["h1Count"] != 1:
        return False, f"h1Count={st['h1Count']} at 1440: {h1s}"
    if "通知" in ctx["text"] and not any("通知" in t for t in h1s):
        return False, f"h1 does not mention 通知: {h1s}"
    return True, f"loaded at 375/768/1440; h1 = {h1s[0]!r}"


def c_contrast(ctx):
    per = {w: A(ctx, w)["contrast"]["failures"] for w in VIEWPORTS}
    total = sum(len(v) for v in per.values())
    if total:
        w = max(per, key=lambda k: len(per[k]))
        f = per[w][0]
        return False, f"failures per viewport {{ {', '.join(f'{k}: {len(v)}' for k, v in per.items())} }}; worst {f['ratio']}:1 (need {f['required']}) {f['selector']} — {f['color']} on {f['background']}"
    return True, f"0 failures; {A(ctx, '1440')['contrast']['checked']} text elements checked at 1440, {A(ctx, '375')['contrast']['checked']} at 375"


def c_overflow(ctx):
    o = A(ctx, "375")["overflow"]
    if o["horizontal"]:
        return False, f"scrollWidth {o['scrollWidth']} > viewport {o['viewportWidth']} at 375; " + ", ".join(x["selector"] for x in o["offenders"][:3])
    return True, f"scrollWidth {o['scrollWidth']} ≤ {o['viewportWidth']} at 375"


def c_targets(ctx):
    bad = {w: [t for t in A(ctx, w)["targets"]["below24"] if not t["inlineText"]] for w in VIEWPORTS}
    n = sum(len(v) for v in bad.values())
    if n:
        w = max(bad, key=lambda k: len(bad[k]))
        return False, f"{n} non-inline targets below 24px; e.g. at {w}: " + ", ".join(f"{t['size']} {t['selector']}" for t in bad[w][:3])
    return True, f"0 non-inline targets below 24px; {A(ctx, '1440')['targets']['checked']} interactive elements checked"


def c_focus(ctx):
    f = ctx["rep"]["viewports"]["1440"]["focus"]
    if not f or f["tabbed"] == 0:
        return False, "nothing reachable by Tab"
    if f["invisible"] or f["obscured"]:
        return False, f"invisible: {f['invisible'][:4]}; obscured: {f['obscured'][:3]}"
    low = f.get("lowContrastRing", [])
    if low:
        return False, f"focus ring below 3:1 on {len(low)}: {low[:3]}"
    return True, f"{f['tabbed']} elements tabbed, all show a focus change, none obscured, rings ≥ 3:1"


def c_hover_feedback(ctx):
    h = ctx["rep"]["viewports"]["1440"].get("hover")
    if not h:
        return False, "hover probe did not run"
    if h["checked"] == 0:
        return True, "no buttons or standalone links to probe"
    if h["noHoverFeedback"]:
        return False, f"{len(h['noHoverFeedback'])}/{h['checked']} change nothing on hover: {h['noHoverFeedback'][:4]}"
    return True, f"{h['checked']} buttons/links probed, all change on hover"


def c_non_text_contrast(ctx):
    inherited = FIXTURE_LINE.get(ctx["eval_id"])
    per, exempt = {}, 0
    for w in VIEWPORTS:
        fails = A(ctx, w)["nonText"]["failures"]
        keep = [f for f in fails if f["color"] != inherited]
        exempt += len(fails) - len(keep)
        per[w] = keep
    total = sum(len(v) for v in per.values())
    note = f" ({exempt} inherited from the fixture's line token, exempt)" if exempt else ""
    if total:
        w = max(per, key=lambda k: len(per[k]))
        f = per[w][0]
        return False, f"boundaries below 3:1 per viewport {{ {', '.join(f'{k}: {len(v)}' for k, v in per.items())} }}{note}; worst {f['ratio']}:1 {f['selector']} ({f['via']} {f['color']} against {f['against']})"
    weak = len(A(ctx, "1440")["nonText"].get("weak", []))
    return True, f"0 failures{note}; {A(ctx, '1440')['nonText']['checked']} control boundaries checked at 1440" + (f"; {weak} text-labelled buttons with a surface <3:1 (WCAG-exempt, warned)" if weak else "")


def c_dark_support(ctx):
    a = A(ctx, "1440")
    d = ctx["rep"]["viewports"]["1440"].get("dark")
    if not a["darkSupport"]["any"]:
        return False, "no prefers-color-scheme: dark rule and no .dark class styles"
    if not d or not d.get("themeChanged"):
        return False, f"dark rule present but page background did not change (light {a['pageColors']['background']} → dark {d and d['pageColors']['background']})"
    return True, f"dark mode via {d['mode']}; background {a['pageColors']['background']} → {d['pageColors']['background']}"


def c_dark_contrast(ctx):
    darks = {w: ctx["rep"]["viewports"][w].get("dark") for w in VIEWPORTS}
    if not all(darks.values()):
        return False, "dark mode was not rendered (no dark rule detected)"
    per = {w: d["contrast"]["failures"] for w, d in darks.items()}
    total = sum(len(v) for v in per.values())
    nt = sum(len(d["nonText"]["failures"]) for d in darks.values())
    if total or nt:
        w = max(per, key=lambda k: len(per[k]))
        f = per[w][0] if per[w] else None
        worst = f" worst {f['ratio']}:1 {f['selector']} — {f['color']} on {f['background']}" if f else ""
        return False, f"dark text failures {{ {', '.join(f'{k}: {len(v)}' for k, v in per.items())} }}, dark non-text failures {nt};{worst}"
    return True, f"dark rendering clean: {darks['1440']['contrast']['checked']} text elements, {darks['1440']['nonText']['checked']} boundaries at 1440"


def c_light_unchanged(ctx):
    want = FIXTURE_LIGHT_BG.get(ctx["eval_id"])
    got = A(ctx, "1440")["pageColors"]["background"]
    if want is None:
        return True, f"no fixture reference; light background is {got}"
    if got == want:
        return True, f"light background still {got}"
    return False, f"light background changed: {got} (fixture {want})"


def c_labels(ctx):
    unnamed = sorted({u for w in VIEWPORTS for u in A(ctx, w)["unnamedControls"]})
    noalt = sorted({u for w in VIEWPORTS for u in A(ctx, w)["imagesMissingAlt"]})
    if unnamed or noalt:
        return False, f"unnamed controls: {unnamed[:4]}; img without alt: {noalt[:4]}"
    return True, "all controls named; all images have alt"


def c_motion(ctx):
    m = A(ctx, "1440")["motion"]
    if m["animatedElements"] and not m["reducedMotionRule"]:
        return False, f"{m['animatedElements']} animated elements and no prefers-reduced-motion rule"
    return True, f"animated elements: {m['animatedElements']}; reduced-motion rule: {m['reducedMotionRule']}"


def c_content(ctx):
    s = ctx["src"]
    missing = [k for k, ok in (("Free", "Free" in s), ("Pro", re.search(r"\bPro\b", s) is not None), ("$12", re.search(r"\$\s*12", s) is not None)) if not ok]
    return (not missing), ("missing: " + ", ".join(missing) if missing else "Free, Pro and $12 all present in source")


def c_not_indigo(ctx):
    hits = INDIGO.findall(ctx["src"])
    css_hits = re.findall(r"--color-[\w-]+:\s*[^;]*(?:indigo|violet|purple)", ctx["css"])
    if hits or css_hits:
        return False, f"{len(hits)} indigo/violet/purple classes (e.g. {hits[:3]}); css tokens {len(css_hits)}"
    return True, "no indigo / violet / purple color classes in source"


def c_type_move(ctx):
    html = ctx["files"].get("index.html", "")
    css = ctx["css"]
    signals = []
    if "fonts.googleapis" in html or "fonts.googleapis" in css:
        signals.append("Google Fonts link")
    if "@font-face" in css:
        signals.append("@font-face")
    if "next/font" in ctx["src"]:
        signals.append("next/font")
    m = re.search(r"--font-(display|heading|title|brand|serif|sans|body)\s*:\s*([^;]+);", css)
    if m and not re.match(r"^\s*(ui-sans-serif|system-ui|-apple-system)", m.group(2)):
        signals.append(f"token --font-{m.group(1)}: {m.group(2).strip()[:40]}")
    return (bool(signals)), (", ".join(signals) if signals else "no typeface set up — system stack only")


def c_report_numbers(ctx):
    s = ctx["summary"]
    if not s:
        return False, "no SUMMARY.md"
    c = re.search(r"(对比度|contrast)[^\n]{0,80}\d", s, re.I)
    t = re.search(r"(触控|点击目标|触摸|target|tap)[^\n]{0,80}\d", s, re.I)
    if c and t:
        return True, f"contrast: {c.group(0)[:60]!r}; targets: {t.group(0)[:60]!r}"
    return False, f"contrast numbers: {bool(c)}; target numbers: {bool(t)}"


def new_pages(ctx):
    return {p: t for p, t in ctx["files"].items() if p.endswith((".tsx", ".jsx")) and "通知" in t}


def c_reuse(ctx):
    pages = new_pages(ctx)
    text = "\n".join(pages.values())
    sw = re.search(r"from\s+[\"'][^\"']*components/ui/Switch[\"']", text)
    bt = re.search(r"from\s+[\"'][^\"']*components/ui/Button[\"']", text)
    if sw and bt:
        return True, f"Switch and Button imported in {list(pages)[:2]}"
    return False, f"pages mentioning 通知: {list(pages)[:3]}; imports Switch={bool(sw)} Button={bool(bt)}"


def c_no_raw_palette(ctx):
    hits = RAW_PALETTE.findall(ctx["src"])
    return (not hits), (f"{len(hits)} raw palette classes, e.g. {sorted(set(hits))[:5]}" if hits else "0 raw palette classes; only semantic tokens")


def theme_tokens(block: str) -> dict[str, str]:
    """`--name: value` pairs of a whitespace-stripped @theme block (comments removed)."""
    block = re.sub(r"/\*.*?\*/", "", block)
    return dict(re.findall(r"(--[\w-]+):([^;]+);", block))


def c_tokens_unchanged(ctx):
    mine = theme_block(ctx["files"].get("src/index.css", ""))
    ref = theme_block(read(FIXTURES / FIXTURE_FOR[ctx["eval_id"]] / "src" / "index.css"))
    if mine == ref:
        return True, "@theme block identical to fixture"
    if ctx["eval_id"] == 4:
        # Dark mode may add tokens; the light values of the existing ones must survive.
        m, r = theme_tokens(mine), theme_tokens(ref)
        changed = [k for k in r if m.get(k) != r[k]]
        added = [k for k in m if k not in r]
        if changed:
            return False, f"existing token values changed: {changed[:6]}"
        return True, f"all {len(r)} fixture tokens keep their light values; added {added or 'none'}"
    return False, f"@theme differs from fixture (len {len(mine)} vs {len(ref)})"


def c_nav(ctx):
    shells = {p: t for p, t in ctx["files"].items() if "AppShell" in p or "NavLink" in t}
    if any("/settings/notifications" in t for t in shells.values()):
        return True, f"route linked in {[p for p, t in shells.items() if '/settings/notifications' in t][:2]}"
    return False, f"no nav link to /settings/notifications in {list(shells)[:3]}"


def c_save_feedback(ctx):
    text = "\n".join(new_pages(ctx).values())
    hits = [k for k in ('role="status"', "aria-live", "已保存") if k in text]
    return (bool(hits)), (f"found {hits}" if hits else "no live region or 已保存 text in the new page")


def c_summary_matches(ctx):
    s = ctx["summary"]
    keys = ["Switch", "Button", "Card", "Field", "brand", "Fraunces", "rounded-md", "IBM Plex", "token", "令牌", "语义", "赤陶", "terracotta"]
    hits = [k for k in keys if k.lower() in s.lower()]
    return (bool(hits)), (f"mentions {hits[:5]}" if hits else "SUMMARY.md names nothing it reused")


def c_copy_preserved(ctx):
    missing = [a for a in COPY_ANCHORS if a not in ctx["src"]]
    return (not missing), ("missing: " + ", ".join(missing) if missing else "all 9 copy anchors present")


def c_no_gradient_text(ctx):
    n = ctx["src"].count("bg-clip-text")
    return (n == 0), (f"bg-clip-text ×{n}" if n else "no bg-clip-text")


def c_no_icon_badges(ctx):
    n = len(ICON_BADGE.findall(ctx["src"]))
    return (n == 0), (f"icon-in-tinted-circle pattern ×{n}" if n else "pattern gone")


def c_before_after(ctx):
    pngs = [p for p in ctx["outputs"] if p.lower().endswith(".png")]
    before = [p for p in pngs if "before" in p.lower()]
    after = [p for p in pngs if "before" not in p.lower()]
    if before and after:
        return True, f"before: {before[0]}; after: {after[0]}"
    return False, f"pngs in outputs: {len(pngs)} (before={len(before)}, after={len(after)})"


def c_summary_critique(ctx):
    s = ctx["summary"]
    groups = [g for g in TELL_GROUPS if re.search(g, s, re.I)]
    return (len(groups) >= 2), (f"{len(groups)} tell groups named: {[g.split('|')[0] for g in groups]}" if s else "no SUMMARY.md")


def c_facts(ctx):
    """verify.py finds no hallucinated package, icon name or web font in the run's project."""
    project = ctx.get("project")
    if not project or not Path(project).is_dir():
        return False, "no project directory"
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "verify.py"), str(project)], capture_output=True, text=True, timeout=120)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    fails = [ln for ln in lines if ln.startswith("FAIL")]
    facts = next((ln for ln in lines if ln.startswith("Facts:")), "")
    if fails:
        return False, f"{len(fails)} invented facts: " + " | ".join(f[6:] for f in fails[:3])
    return True, facts[7:] if facts else "verify.py ran, no FAIL lines"


def c_summary_dark_numbers(ctx):
    s = ctx["summary"]
    if not s:
        return False, "no SUMMARY.md"
    # A line that talks about dark mode AND carries a contrast measurement (an N:1 ratio, or
    # "对比度"/"contrast" followed by a number) — not just any digit near the word.
    for line in s.splitlines():
        if not re.search(r"深色|暗色|dark", line, re.I):
            continue
        if re.search(r"\d+(?:\.\d+)?\s*:\s*1\b", line) or re.search(r"(对比度|contrast)[^\n]{0,60}\d", line, re.I):
            return True, f"dark-mode measurement stated: {line.strip()[:100]!r}"
    return False, "no dark-mode contrast numbers in SUMMARY.md"


CHECKERS = {
    "renders": c_renders, "contrast": c_contrast, "overflow": c_overflow, "targets": c_targets,
    "focus": c_focus, "labels": c_labels, "motion": c_motion, "content": c_content,
    "not-indigo": c_not_indigo, "type-move": c_type_move, "report-numbers": c_report_numbers,
    "reuse": c_reuse, "no-raw-palette": c_no_raw_palette, "tokens-unchanged": c_tokens_unchanged,
    "nav": c_nav, "save-feedback": c_save_feedback, "summary-matches": c_summary_matches,
    "copy-preserved": c_copy_preserved, "no-gradient-text": c_no_gradient_text,
    "no-icon-badges": c_no_icon_badges, "before-after": c_before_after, "summary-critique": c_summary_critique,
    "hover-feedback": c_hover_feedback, "non-text-contrast": c_non_text_contrast,
    "dark-support": c_dark_support, "dark-contrast": c_dark_contrast, "light-unchanged": c_light_unchanged,
    "summary-dark-numbers": c_summary_dark_numbers,
    "facts": c_facts,
}


# --------------------------------------------------------------------- main
def grade_run(eval_dir: Path, meta: dict, run: Path, port: int, skip_render: bool) -> dict:
    project, outputs = run / "project", run / "outputs"
    eval_id = int(meta["eval_id"])
    files = source_files(project) if project.exists() else {}
    ctx = {
        "eval_id": eval_id, "files": files, "project": str(project),
        "src": "\n".join(files.values()),
        "css": "\n".join(t for p, t in files.items() if p.endswith(".css")),
        "summary": read(outputs / "SUMMARY.md"),
        "outputs": [str(p.relative_to(outputs)) for p in outputs.rglob("*") if p.is_file()] if outputs.exists() else [],
        "rep": None, "render_error": "",
    }
    # One render per route: grader-render (first route), grader-render-2, ... Render-based
    # assertions must hold on every route.
    routes = ROUTES[eval_id]
    outs = [run / ("grader-render" if i == 0 else f"grader-render-{i + 1}") for i in range(len(routes))]
    out = outs[0]
    reps: list[tuple[str, dict | None]] = []
    if not project.exists():
        ctx["render_error"] = "no project directory"
    elif skip_render and all((o / "report.json").exists() for o in outs):
        reps = [(r, json.loads(read(o / "report.json"))) for r, o in zip(routes, outs)]
    else:
        proc = boot(project, port, run / "grader-vite.log")
        if proc is None:
            ctx["render_error"] = "dev server did not start: " + read(run / "grader-vite.log")[-300:]
        else:
            try:
                for r, o in zip(routes, outs):
                    rep, err = render(port, r, o)
                    reps.append((r, rep))
                    if err and not ctx["render_error"]:
                        ctx["render_error"] = f"{r}: {err}"
            finally:
                stop(proc)
    ctx["rep"] = reps[0][1] if reps else None
    ctx["reps"] = reps

    def run_checker(fn, key):
        if key not in NEEDS_RENDER or len(reps) <= 1:
            return fn(ctx)
        results = []
        for route, rep in reps:
            if rep is None:
                results.append((False, f"{route}: not rendered"))
                continue
            sub = dict(ctx, rep=rep)
            ok, ev = fn(sub)
            results.append((bool(ok), f"{route}: {ev}"))
        return all(ok for ok, _ in results), " | ".join(ev for _, ev in results)

    expectations = []
    for text in meta.get("assertions", []):
        key = text.split(":", 1)[0].strip()
        ctx["text"] = text
        fn = CHECKERS.get(key)
        if fn is None:
            passed, evidence = False, f"no checker for '{key}'"
        elif key in NEEDS_RENDER and ctx["rep"] is None:
            passed, evidence = False, "not rendered: " + (ctx["render_error"] or "unknown")
        else:
            try:
                passed, evidence = run_checker(fn, key)
            except Exception as e:  # a checker crash is a failed check with a reason
                passed, evidence = False, f"checker error: {type(e).__name__}: {e}"
        expectations.append({"text": text, "passed": bool(passed), "evidence": str(evidence)[:600]})

    passed = sum(1 for e in expectations if e["passed"])
    grading = {
        "expectations": expectations,
        "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations),
                    "pass_rate": round(passed / len(expectations), 4) if expectations else 0.0},
        "grader": "grade.py (programmatic; re-rendered with render.mjs)",
        "render_dir": str(out.relative_to(run)) if ctx["rep"] else None,
        "routes": routes,
    }
    # Timing stays in the sibling timing.json: the aggregator only reads tokens from
    # there, and only when grading.json carries no timing of its own.
    (run / "grading.json").write_text(json.dumps(grading, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return grading


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("iteration")
    ap.add_argument("--only", default=None, help="grade one eval dir (name)")
    ap.add_argument("--config", default=None, help="grade one configuration (e.g. with_skill)")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()
    it = Path(args.iteration).resolve()
    rows = []
    port = free_port(5200)
    for eval_dir in sorted(it.glob("eval-*")):
        if args.only and eval_dir.name != args.only:
            continue
        meta = json.loads(read(eval_dir / "eval_metadata.json"))
        for cfg in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            if args.config and cfg.name != args.config:
                continue
            for run in sorted(cfg.glob("run-*")):
                if not (run / "outputs").is_dir() or not any((run / "outputs").iterdir()):
                    print(f"{eval_dir.name:32} {cfg.name:14} {run.name}  (no outputs yet — skipped)")
                    continue
                port = free_port(port + 1)
                g = grade_run(eval_dir, meta, run, port, args.skip_render)
                rows.append((eval_dir.name, cfg.name, run.name, g["summary"]))
                print(f"{eval_dir.name:32} {cfg.name:14} {run.name}  {g['summary']['passed']}/{g['summary']['total']}")
                for e in g["expectations"]:
                    if not e["passed"]:
                        print(f"    ✗ {e['text'].split(':')[0]:18} {e['evidence'][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
