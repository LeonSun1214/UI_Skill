#!/usr/bin/env python3
"""Derive timing.json data from a subagent's JSONL transcript.

Sums usage per unique assistant message id (streamed transcripts repeat a
message once per content block) and takes wall-clock from first/last timestamps.
Prints one JSON line per transcript; with --write <run-dir> also writes
<run-dir>/timing.json. Never prints transcript content.

Usage: python3 timing_from_transcript.py <transcript.jsonl> [--write RUN_DIR] [--label NAME]
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


OUTAGE_GAP_S = 900  # a silence longer than this is an interruption (rate limit, resume), not work


def summarize(path: Path) -> dict:
    first = last = None
    stamps: list[datetime] = []
    usage_by_id: dict[str, dict] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            ts = rec.get("timestamp")
            if ts:
                first = first or ts
                last = ts
                try:
                    stamps.append(parse_ts(ts))
                except ValueError:
                    pass
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else None
            usage = msg.get("usage") if msg and isinstance(msg.get("usage"), dict) else None
            if usage:
                usage_by_id[(msg.get("id") or rec.get("uuid") or str(len(usage_by_id)))] = usage
    tot = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    for u in usage_by_id.values():
        for k in tot:
            tot[k] += int(u.get(k, 0) or 0)
    wall = (parse_ts(last) - parse_ts(first)).total_seconds() if first and last else None
    stamps.sort()
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    excluded = [g for g in gaps if g > OUTAGE_GAP_S]
    dur = (sum(g for g in gaps if g <= OUTAGE_GAP_S)) if gaps else wall
    return {
        "executor_start": first, "executor_end": last,
        "duration_ms": int(dur * 1000) if dur is not None else None,
        "total_duration_seconds": round(dur, 1) if dur is not None else None,
        "executor_duration_seconds": round(dur, 1) if dur is not None else None,
        "wall_clock_seconds": round(wall, 1) if wall is not None else None,
        "excluded_outage_seconds": round(sum(excluded), 1),
        "interruptions": len(excluded),
        "assistant_messages": len(usage_by_id),
        **tot,
        "total_tokens": tot["input_tokens"] + tot["output_tokens"] + tot["cache_creation_input_tokens"],
        "tokens_incl_cache_read": sum(tot.values()),
        "source": "transcript-derived (sum of input+output+cache_creation per unique message)",
    }


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    path = Path(args[0])
    label = args[args.index("--label") + 1] if "--label" in args else path.stem
    data = summarize(path)
    print(json.dumps({"label": label, **{k: data[k] for k in ("total_duration_seconds", "assistant_messages", "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "total_tokens", "tokens_incl_cache_read")}}, ensure_ascii=False))
    if "--write" in args:
        run_dir = Path(args[args.index("--write") + 1])
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "timing.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
