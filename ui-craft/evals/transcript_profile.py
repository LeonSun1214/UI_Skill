#!/usr/bin/env python3
"""Where did the tokens go? Step-by-step cost profile of a subagent transcript.

For every assistant turn: the tools it called (name + a short argument), the usage the
API billed for that turn (fresh input, cache writes, output) and the size of each tool
result it then received (characters; images flagged). Prints a table and a per-tool
roll-up. Never prints transcript prose.

Usage: python3 transcript_profile.py <transcript.jsonl> [--steps]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def arg_summary(name: str, inp: dict) -> str:
    if name in ("Read",):
        return str(inp.get("file_path", ""))[-70:]
    if name in ("Bash",):
        return (inp.get("description") or inp.get("command", ""))[:70].replace("\n", " ")
    if name in ("Edit", "Write", "MultiEdit"):
        return str(inp.get("file_path", ""))[-60:]
    if name in ("Grep", "Glob"):
        return f"{inp.get('pattern', '')[:40]} in {str(inp.get('path', ''))[-30:]}"
    if name == "Skill":
        return str(inp.get("skill", ""))
    return json.dumps(inp, ensure_ascii=False)[:70]


def result_size(block) -> tuple[int, int]:
    """(chars, images) of a tool_result block."""
    c = block.get("content")
    if isinstance(c, str):
        return len(c), 0
    chars = imgs = 0
    for part in c or []:
        if isinstance(part, dict):
            if part.get("type") == "text":
                chars += len(part.get("text", ""))
            elif part.get("type") == "image":
                imgs += 1
        elif isinstance(part, str):
            chars += len(part)
    return chars, imgs


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__); return 1
    path = Path(sys.argv[1]); show_steps = "--steps" in sys.argv
    turns = {}          # message id -> {usage, tools:[(tool_use_id, name, arg)]}
    order = []
    results = {}        # tool_use_id -> (chars, images)
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try: rec = json.loads(line)
            except json.JSONDecodeError: continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            if not isinstance(msg, dict): continue
            content = msg.get("content")
            if msg.get("role") == "assistant":
                mid = msg.get("id") or rec.get("uuid")
                t = turns.setdefault(mid, {"usage": {}, "tools": [], "text": 0})
                if mid not in order: order.append(mid)
                if isinstance(msg.get("usage"), dict): t["usage"] = msg["usage"]
                for blk in content if isinstance(content, list) else []:
                    if not isinstance(blk, dict): continue
                    if blk.get("type") == "tool_use":
                        if all(blk.get("id") != x[0] for x in t["tools"]):
                            t["tools"].append((blk.get("id"), blk.get("name", "?"), arg_summary(blk.get("name", ""), blk.get("input") or {})))
                    elif blk.get("type") == "text":
                        t["text"] = max(t["text"], len(blk.get("text", "")))
            elif msg.get("role") == "user" and isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        results[blk.get("tool_use_id")] = result_size(blk)

    per_tool = defaultdict(lambda: {"calls": 0, "result_chars": 0, "images": 0})
    tot = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    rows = []
    for i, mid in enumerate(order, 1):
        t = turns[mid]; u = t["usage"]
        for k in tot: tot[k] += int(u.get(k, 0) or 0)
        billed = int(u.get("input_tokens", 0) or 0) + int(u.get("output_tokens", 0) or 0) + int(u.get("cache_creation_input_tokens", 0) or 0)
        calls = []
        for tid, name, arg in t["tools"]:
            chars, imgs = results.get(tid, (0, 0))
            per_tool[name]["calls"] += 1; per_tool[name]["result_chars"] += chars; per_tool[name]["images"] += imgs
            calls.append(f"{name}({arg}) → {chars:,}c{' +' + str(imgs) + 'img' if imgs else ''}")
        rows.append((i, billed, int(u.get("cache_read_input_tokens", 0) or 0), int(u.get("output_tokens", 0) or 0), t["text"], calls))

    print(f"{path.name}: {len(order)} assistant turns; billed {tot['input_tokens'] + tot['output_tokens'] + tot['cache_creation_input_tokens']:,} "
          f"(fresh in {tot['input_tokens']:,} · cache write {tot['cache_creation_input_tokens']:,} · out {tot['output_tokens']:,}) · cache read {tot['cache_read_input_tokens']:,}")
    if show_steps:
        print(f"{'#':>3} {'billed':>8} {'cached':>9} {'out':>6}  tools → result size")
        for i, billed, cached, out, text, calls in rows:
            first = calls[0] if calls else (f"[text {text:,}c]" if text else "")
            print(f"{i:>3} {billed:>8,} {cached:>9,} {out:>6,}  {first}")
            for c in calls[1:]:
                print(f"{'':>30}  {c}")
    print("\nper tool:")
    for name, d in sorted(per_tool.items(), key=lambda kv: -kv[1]["result_chars"]):
        print(f"  {name:12} {d['calls']:>3} calls  {d['result_chars']:>9,} result chars  {d['images']} images")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
