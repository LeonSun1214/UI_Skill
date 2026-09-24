#!/usr/bin/env python3
"""Visual judge — does the page *look* good, beyond passing the instruments?

Uses `claude -p` (the Claude Code CLI, with the account's own auth) to look at each run's
contact sheet (three viewports above the fold, one image) and grade it against
references/critique-rubric.md. Two modes:

  python3 judge.py score <iteration-dir> [--only EVAL] [--config CFG] [--model M] [--force] [--dark]
      writes <run>/judge.json: six 1–5 scores (hierarchy, distinctive, typography, spacing,
      color, overall) + one sentence each. Skips runs that already have judge.json unless --force.

  python3 judge.py pair <iteration-dir> --a with_skill --b ui_ux_pro_max [--only EVAL] [--model M] [--dark]
      for every eval, shows both contact sheets and asks which page a design lead would ship;
      asked twice with the images swapped, so a position preference cancels out. Writes
      <iteration>/judge-pairs.json and prints a table.

The judge sees only pixels: no summaries, no config names, no numbers. Cost is roughly one
`claude -p` call per image set; the contact sheet is 1× so a call is cheap.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUBRIC = HERE.parent / "references" / "critique-rubric.md"
DIMENSIONS = ["hierarchy", "distinctive", "typography", "spacing", "color", "overall"]

SCORE_PROMPT = """You are a senior product designer reviewing a web page from screenshots. Use the Read tool to view the image at {image}. It is a contact sheet: the same page above the fold at 375, 768 and 1440 px, side by side{dark_note}.

Judge what the pixels show against this rubric (excerpt):
- Hierarchy: one thing wins the first three seconds, then a clear second and third; size, weight and colour change between levels; one primary action per view.
- Distinctive: would you stop on this page among ten SaaS sites? Deliberate typography, colour or layout choices — not indigo + Inter + three icon cards.
- Typography: a display face doing something the body face can't; sane measure and line-height; no widows; numbers tabular where they align.
- Spacing & alignment: a spacing scale, related things closer than unrelated, left edges lining up, cards aligned across a row.
- Color: the accent has one job; neutrals carry structure; muted text still reads on tinted surfaces.
- Overall: would a design lead ship this without a round of notes?

Score each 1–5 (1 = template-grade or broken, 3 = competent and forgettable, 5 = a page a good studio would put in its portfolio). Be strict: 4 and 5 must be earned. Reply with ONLY a JSON object, no prose before or after:
{{"hierarchy": n, "distinctive": n, "typography": n, "spacing": n, "color": n, "overall": n, "notes": {{"hierarchy": "...", "distinctive": "...", "typography": "...", "spacing": "...", "color": "...", "overall": "..."}}}}"""

PAIR_PROMPT = """You are a design lead choosing between two implementations of the same brief. Use the Read tool to view image A at {a} and then image B at {b}. Each is a contact sheet of one page above the fold at 375, 768 and 1440 px{dark_note}.

The brief both were built for: {brief}

Which page would you ship, judged only on what the pixels show — hierarchy, distinctiveness, typography, spacing and alignment, colour discipline, and how finished it feels at every width? Prefer the one that is more clearly designed, not the one with more stuff. Reply with ONLY a JSON object: {{"winner": "A" or "B", "confidence": 1-5, "reason": "one sentence naming the deciding difference"}}"""


def call_claude(prompt: str, cwd: Path, model: str | None, timeout: int = 240) -> dict | None:
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--allowedTools", "Read"]
    if model:
        cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None
    try:
        outer = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    text = str(outer.get("result", ""))
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < 0:
        return {"_error": text[:300], "_cost": outer.get("total_cost_usd")}
    try:
        data = json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return {"_error": text[:300], "_cost": outer.get("total_cost_usd")}
    data["_cost"] = outer.get("total_cost_usd")
    return data


DARK = False  # set by --dark: judge the dark-mode contact sheets instead of the light ones


def contact_for(run: Path) -> Path | None:
    name = "contact-dark.png" if DARK else "contact.png"
    for cand in (run / "grader-render" / name, run / "outputs" / f"after-{name}", run / "outputs" / "render" / name):
        if cand.exists():
            return cand
    return None


def runs_in(it: Path, only: str | None, config: str | None):
    for eval_dir in sorted(it.glob("eval-*")):
        if only and only not in eval_dir.name:
            continue
        for cfg in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            if config and cfg.name != config:
                continue
            for run in sorted(cfg.glob("run-*")):
                if (run / "grading.json").exists():
                    yield eval_dir, cfg, run


def brief_of(eval_dir: Path) -> str:
    try:
        return json.loads((eval_dir / "eval_metadata.json").read_text(encoding="utf-8")).get("prompt", "")
    except (OSError, ValueError):
        return ""


def cmd_score(it: Path, only, config, model, force):
    total_cost = 0.0
    rows = []
    for eval_dir, cfg, run in runs_in(it, only, config):
        out = run / ("judge-dark.json" if DARK else "judge.json")
        if out.exists() and not force:
            data = json.loads(out.read_text(encoding="utf-8"))
        else:
            img = contact_for(run)
            if not img:
                print(f"{eval_dir.name:32} {cfg.name:14} no contact sheet"); continue
            data = call_claude(SCORE_PROMPT.format(image=img, dark_note=" — rendered in dark mode (prefers-color-scheme: dark); judge it as a dark theme" if DARK else ""), cwd=img.parent, model=model)
            if not data or "_error" in (data or {}):
                print(f"{eval_dir.name:32} {cfg.name:14} judge failed: {(data or {}).get('_error', 'timeout')}"); continue
            data["image"] = str(img.relative_to(run))
            data["judged_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            data["model"] = model
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total_cost += float(data.get("_cost") or 0)
        scores = [data.get(d) for d in DIMENSIONS]
        rows.append((eval_dir.name, cfg.name, scores))
        print(f"{eval_dir.name:32} {cfg.name:14} " + " ".join(f"{d[:4]}={s}" for d, s in zip(DIMENSIONS, scores)))
    if rows:
        cfgs = sorted({r[1] for r in rows})
        print("\nmean overall per configuration: " + " · ".join(
            f"{c} {sum(r[2][-1] for r in rows if r[1] == c and r[2][-1] is not None) / max(1, len([r for r in rows if r[1] == c and r[2][-1] is not None])):.2f}" for c in cfgs))
    print(f"judge cost this call: ${total_cost:.2f}")


def cmd_pair(it: Path, a: str, b: str, only, model):
    results = {}
    total_cost = 0.0
    for eval_dir in sorted(it.glob("eval-*")):
        if only and only not in eval_dir.name:
            continue
        ra, rb = eval_dir / a / "run-1", eval_dir / b / "run-1"
        ia, ib = contact_for(ra), contact_for(rb)
        if not ia or not ib:
            print(f"{eval_dir.name}: missing contact sheet for {a if not ia else b}"); continue
        brief = brief_of(eval_dir)[:400]
        votes = []
        for order, (x, y) in enumerate(((ia, ib), (ib, ia))):
            data = call_claude(PAIR_PROMPT.format(a=x, b=y, brief=brief, dark_note=", rendered in dark mode" if DARK else ""), cwd=it, model=model)
            if not data or "_error" in data:
                votes.append({"order": order, "winner": None, "error": (data or {}).get("_error", "timeout")}); continue
            total_cost += float(data.get("_cost") or 0)
            win = data.get("winner")
            # map back to config names: in order 0, A=a; in order 1, A=b
            picked = (a if win == "A" else b) if order == 0 else (b if win == "A" else a)
            votes.append({"order": order, "picked": picked, "confidence": data.get("confidence"), "reason": data.get("reason")})
        picks = [v.get("picked") for v in votes if v.get("picked")]
        verdict = picks[0] if len(picks) == 2 and picks[0] == picks[1] else ("split" if len(picks) == 2 else "incomplete")
        results[eval_dir.name] = {"a": a, "b": b, "votes": votes, "verdict": verdict}
        print(f"{eval_dir.name:32} {verdict:14} " + " | ".join(f"{v.get('picked', '?')} ({v.get('confidence', '?')}) {str(v.get('reason', v.get('error', '')))[:90]}" for v in votes))
    out = it / ("judge-pairs-dark.json" if DARK else "judge-pairs.json")
    existing = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    merged = existing.get(f"{a}_vs_{b}", {})
    merged.update(results)  # a --only run refreshes one eval and keeps the others
    existing[f"{a}_vs_{b}"] = merged
    results = merged
    out.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    wins = {a: 0, b: 0, "split": 0}
    for r in results.values():
        wins[r["verdict"] if r["verdict"] in wins else "split"] += 1
    print(f"\n{a} {wins[a]} · {b} {wins[b]} · split {wins['split']}  (judge cost ${total_cost:.2f}) → {out}")


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    opt = lambda flag, default=None: a[a.index(flag) + 1] if flag in a else default
    it = Path(a[1]).resolve()
    model = opt("--model", "claude-fable-5-1")
    global DARK
    DARK = "--dark" in a
    if a[0] == "score":
        cmd_score(it, opt("--only"), opt("--config"), model, "--force" in a)
    elif a[0] == "pair":
        cmd_pair(it, opt("--a", "with_skill"), opt("--b", "ui_ux_pro_max"), opt("--only"), model)
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
