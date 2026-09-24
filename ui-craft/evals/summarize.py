#!/usr/bin/env python3
"""Three-way summary of an iteration: pass counts and tokens per eval × configuration.

Reads every  <iteration>/eval-*/<config>/run-*/grading.json  (+ timing.json when present)
and prints a Markdown table plus the per-assertion failures, so a re-grade can be read at
a glance. Optionally rewrites the `delta` fields of an existing benchmark.json so that
`delta` is always with_skill − without_skill and `delta_vs_<cfg>` exists for every other
configuration (skill-creator's aggregator computes only one delta).

Usage: python3 summarize.py <iteration-dir> [--patch-benchmark]
"""
import json
import statistics
import sys
from pathlib import Path


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def collect(it: Path):
    rows = []  # (eval, config, run, passed, total, tokens, seconds, failed_ids)
    for eval_dir in sorted(it.glob("eval-*")):
        for cfg in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            for run in sorted(cfg.glob("run-*")):
                g = load(run / "grading.json")
                if not g:
                    continue
                t = load(run / "timing.json") or {}
                failed = [e["text"].split(":")[0] for e in g["expectations"] if not e["passed"]]
                j = load(run / "judge.json") or {}
                rows.append((eval_dir.name, cfg.name, run.name, g["summary"]["passed"], g["summary"]["total"],
                             t.get("total_tokens"), t.get("total_duration_seconds"), failed,
                             t.get("total_tokens_comparable") or t.get("total_tokens_excl_resume"),
                             j.get("overall"), j.get("distinctive")))
    return rows


def table(rows):
    evals = sorted({r[0] for r in rows})
    cfgs = ["with_skill", "ui_ux_pro_max", "without_skill"]
    cfgs = [c for c in cfgs if any(r[1] == c for r in rows)] + sorted({r[1] for r in rows} - set(cfgs))
    out = ["| | " + " | ".join(cfgs) + " |", "|---|" + "---|" * len(cfgs)]
    for ev in evals:
        cells = []
        for c in cfgs:
            rs = [r for r in rows if r[0] == ev and r[1] == c]
            if not rs:
                cells.append("—")
                continue
            r = rs[0]
            tok = f" · {r[5] / 1000:.0f}k" if r[5] else ""
            if r[5] and r[8] and r[8] != r[5]:
                tok += f" ({r[8] / 1000:.0f}k)"
            vis = f" · look {r[9]}/5" if r[9] is not None else ""
            cells.append(f"{r[3]}/{r[4]}{tok}{vis}")
        out.append(f"| {ev} | " + " | ".join(cells) + " |")
    tot = []
    for c in cfgs:
        rs = [r for r in rows if r[1] == c]
        tot.append(f"**{sum(r[3] for r in rs)}/{sum(r[4] for r in rs)}**")
    out.append("| **pass** | " + " | ".join(tot) + " |")
    means = []
    for c in cfgs:
        toks = [r[5] for r in rows if r[1] == c and r[5]]
        means.append(f"{statistics.mean(toks):,.0f}" if toks else "—")
    out.append("| token mean | " + " | ".join(means) + " |")
    excl = []
    for c in cfgs:
        toks = [r[8] for r in rows if r[1] == c and r[8]]
        excl.append(f"{statistics.mean(toks):,.0f}" if toks else "—")
    out.append("| token mean, comparable | " + " | ".join(excl) + " |")
    looks = []
    for c in cfgs:
        v = [r[9] for r in rows if r[1] == c and r[9] is not None]
        d = [r[10] for r in rows if r[1] == c and r[10] is not None]
        looks.append(f"{statistics.mean(v):.2f} (distinctive {statistics.mean(d):.2f})" if v else "—")
    if any(l != "—" for l in looks):
        out.append("| visual judge, overall 1–5 | " + " | ".join(looks) + " |")
    out.append("")
    out.append("(a)k (b)k = billed tokens (comparable: minus the cache re-write after an interruption, plus the harness-prefix cache write when a sibling run had paid it)")
    return "\n".join(out), cfgs


def failures(rows):
    out = []
    for ev, cfg, run, p, t, tok, sec, failed, _, _o, _d in rows:
        if failed:
            out.append(f"- {ev} · {cfg}: " + ", ".join(failed))
    return "\n".join(out) or "- none"


def patch_benchmark(it: Path, cfgs):
    bp = it / "benchmark.json"
    b = load(bp)
    if not b or "run_summary" not in b:
        return "no benchmark.json to patch"
    rs = b["run_summary"]
    if "with_skill" not in rs:
        return "benchmark.json has no with_skill summary"
    ws = rs["with_skill"]

    def delta(other):
        d = {}
        for k in ("pass_rate", "time_seconds", "tokens"):
            if k in ws and k in other:
                v = ws[k]["mean"] - other[k]["mean"]
                d[k] = f"{v:+.2f}" if k == "pass_rate" else f"{v:+.1f}" if k == "time_seconds" else f"{v:+.0f}"
        return d

    for c in cfgs:
        if c == "with_skill" or c not in rs:
            continue
        key = "delta" if c == "without_skill" else f"delta_vs_{c}"
        rs[key] = delta(rs[c])
    bp.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"patched deltas in {bp}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    it = Path(sys.argv[1]).resolve()
    rows = collect(it)
    if not rows:
        print("no grading.json found under", it)
        return 1
    md, cfgs = table(rows)
    print(md)
    pairs = load(it / "judge-pairs.json")
    if pairs:
        print("\nVisual judge, pairwise (both image orders; 'split' = the two orders disagreed):")
        for key, res in pairs.items():
            a, b = key.split("_vs_")
            wins = {a: 0, b: 0, "split": 0}
            for ev, r in res.items():
                wins[r["verdict"] if r["verdict"] in wins else "split"] += 1
            print(f"- {a} vs {b}: {wins[a]}–{wins[b]}, {wins['split']} split · " + "; ".join(f"{ev.split('-')[1]}: {r['verdict']}" for ev, r in res.items()))
    print("\nFailures:\n" + failures(rows))
    if "--patch-benchmark" in sys.argv:
        print("\n" + patch_benchmark(it, cfgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
