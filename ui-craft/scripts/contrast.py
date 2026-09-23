#!/usr/bin/env python3
"""Contrast ratios for colour pairs or for the tokens in a CSS file — before you render.

  python3 contrast.py '#6b615b' '#fbf8f3'                 one pair (fg bg)
  python3 contrast.py '#fff' '#b5451b' '#2a2320' '#fff'   several pairs
  python3 contrast.py --css src/index.css --text ink,muted,brand,brand-fg --on surface,panel,brand

--css reads `--color-*` (or any `--*`) custom properties from @theme / :root blocks and,
when an `@media (prefers-color-scheme: dark)` or `.dark` block redefines them, prints a
light and a dark column. Names are matched with or without the `--color-` prefix.
Thresholds: 4.5:1 body text · 3:1 large text (≥ 24px, or ≥ 18.66px bold) and control
boundaries / focus rings (WCAG 2.2 1.4.3, 1.4.11). Standard library only.
"""
import re
import sys


def parse_color(s: str):
    s = s.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})", s)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b, a)
    m = re.fullmatch(r"rgba?\(([^)]+)\)", s)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        nums = []
        for p in parts[:4]:
            if p.endswith("%"):
                nums.append(float(p[:-1]) * (2.55 if len(nums) < 3 else 0.01))
            else:
                nums.append(float(p))
        r, g, b = nums[:3]
        a = nums[3] if len(nums) > 3 else 1.0
        return (r, g, b, a)
    m = re.fullmatch(r"oklch\(([^)]+)\)", s)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        L = float(parts[0][:-1]) / 100 if parts[0].endswith("%") else float(parts[0])
        C = float(parts[1]); H = float(parts[2]) if len(parts) > 2 else 0.0
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return oklch_to_srgb(L, C, H) + (a,)
    named = {"white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0), "transparent": (0, 0, 0, 0.0)}
    return named.get(s)


def oklch_to_srgb(L, C, H):
    import math
    a = C * math.cos(math.radians(H)); b = C * math.sin(math.radians(H))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def gam(c):
        c = max(0.0, min(1.0, c))
        return 255 * (1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c)
    return (gam(r), gam(g), gam(bb))


def over(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def luminance(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def ratio(fg, bg):
    if fg[3] < 1:
        fg = over(fg, bg)
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def verdict(r):
    tags = []
    tags.append("AA text ✓" if r >= 4.5 else "AA text ✗")
    tags.append("large/UI ✓" if r >= 3 else "large/UI ✗")
    if r >= 7:
        tags[0] = "AAA text ✓"
    return " · ".join(tags)


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def blocks(css: str):
    """Yield (selector_or_atrule, body) for every top-level and nested block."""
    i = 0
    n = len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            return
        head = css[i:j].strip().split("}")[-1].strip()
        depth, k = 0, j
        while k < n:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        body = css[j + 1:k]
        yield head, body
        yield from blocks(body)
        i = k + 1


def tokens_from_css(css: str):
    """Return (light: {name: value}, dark: {name: value}) from @theme/:root and dark blocks."""
    css = strip_comments(css)
    light, dark = {}, {}
    for head, body in blocks(css):
        decls = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;{}]+);", body))
        if not decls:
            continue
        is_dark = bool(re.search(r"prefers-color-scheme\s*:\s*dark", head)) or re.search(r"(^|[\s,>])\.dark\b", head) is not None
        target = dark if is_dark else light
        for k, v in decls.items():
            if parse_color(v.strip()):
                target.setdefault(k, v.strip())
    return light, dark


def resolve(name: str, table: dict):
    for cand in (name, f"--{name}", f"--color-{name}"):
        if cand in table:
            return cand, table[cand]
    return None, None


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); return 0
    if "--css" in args:
        path = args[args.index("--css") + 1]
        text_roles = args[args.index("--text") + 1].split(",") if "--text" in args else ["ink", "text", "muted", "brand", "primary", "accent", "fg", "foreground"]
        on_roles = args[args.index("--on") + 1].split(",") if "--on" in args else ["surface", "bg", "background", "panel", "card"]
        css = open(path, encoding="utf-8").read()
        light, dark = tokens_from_css(css)
        if not light:
            print(f"no colour custom properties found in {path}"); return 1
        merged_dark = {**light, **dark}
        has_dark = bool(dark)
        print(f"{path}: {len(light)} colour tokens" + (f", {len(dark)} redefined in dark" if has_dark else ", no dark block"))
        print(f"{'text on surface':34} {'light':>9}" + (f" {'dark':>9}" if has_dark else "") + "   verdict (light" + (" / dark)" if has_dark else ")"))
        for t in text_roles:
            tk, tv = resolve(t.strip(), light)
            if not tk:
                continue
            for o in on_roles:
                ok_, ov = resolve(o.strip(), light)
                if not ok_ or ok_ == tk:
                    continue
                rl = ratio(parse_color(tv), parse_color(ov))
                line = f"{tk[8:] if tk.startswith('--color-') else tk} on {ok_[8:] if ok_.startswith('--color-') else ok_}"
                if has_dark:
                    rd = ratio(parse_color(merged_dark[tk]), parse_color(merged_dark[ok_]))
                    print(f"{line:34} {rl:>7.2f}:1 {rd:>7.2f}:1   {verdict(rl)} / {verdict(rd)}")
                else:
                    print(f"{line:34} {rl:>7.2f}:1   {verdict(rl)}")
        return 0
    if len(args) % 2:
        print("give colours in pairs: fg bg [fg bg ...]"); return 1
    for fg_s, bg_s in zip(args[::2], args[1::2]):
        fg, bg = parse_color(fg_s), parse_color(bg_s)
        if not fg or not bg:
            print(f"cannot parse {fg_s!r} / {bg_s!r} (use #hex, rgb(), oklch())"); continue
        r = ratio(fg, bg)
        print(f"{fg_s} on {bg_s}: {r:.2f}:1   {verdict(r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
