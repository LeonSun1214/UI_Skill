#!/usr/bin/env python3
"""ui-craft inspect — what does this React + Tailwind project already look like?

Prints a Markdown report of the design conventions a project already has, so new
UI can match them instead of introducing a second design language:

  * stack: framework, Tailwind major, UI / icon / motion libraries, shadcn
  * declared tokens: @theme (Tailwind v4), tailwind.config extend (v3), :root vars
  * fonts: next/font, Google Fonts links, @font-face
  * component inventory: primitives vs composed
  * what the code ACTUALLY uses: dominant color families, radius, shadow, text
    sizes, spacing steps, semantic-token vs raw-palette ratio, dark: usage,
    arbitrary values (token drift)
  * existing design docs
  * a verdict: match the established conventions, or establish a direction

Usage: python3 inspect.py [project-root] [--json]
Standard library only.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".next", ".nuxt", ".svelte-kit", "dist", "build", "out", ".git",
    "coverage", ".turbo", ".vercel", ".cache", "storybook-static", ".ui-craft",
    "__pycache__", ".venv", "venv",
}
SRC_EXT = {".tsx", ".jsx", ".ts", ".js", ".mjs", ".mdx", ".astro", ".vue", ".svelte", ".html"}
CSS_EXT = {".css", ".scss", ".pcss"}
MAX_SRC_FILES = 600
MAX_READ = 400_000

KNOWN_FRAMEWORKS = [
    ("next", "Next.js"), ("@remix-run/react", "Remix"), ("react-router", "React Router"),
    ("react-router-dom", "React Router"), ("@tanstack/react-router", "TanStack Router"),
    ("nuxt", "Nuxt"), ("@sveltejs/kit", "SvelteKit"), ("@angular/core", "Angular"),
    ("astro", "Astro"), ("gatsby", "Gatsby"), ("vue", "Vue"), ("svelte", "Svelte"), ("solid-js", "Solid"),
    ("vite", "Vite"), ("react-scripts", "Create React App"),
]
KNOWN_UI = {
    "@radix-ui/react-dialog": "Radix primitives", "@radix-ui/react-slot": "Radix primitives",
    "radix-ui": "Radix primitives", "@headlessui/react": "Headless UI", "@mui/material": "MUI",
    "antd": "Ant Design", "@chakra-ui/react": "Chakra UI", "@mantine/core": "Mantine",
    "daisyui": "daisyUI", "flowbite-react": "Flowbite", "@heroui/react": "HeroUI",
    "@nextui-org/react": "NextUI", "@ark-ui/react": "Ark UI", "react-aria-components": "React Aria",
    "@base-ui-components/react": "Base UI",
}
KNOWN_ICONS = {
    "lucide-react": "Lucide", "@heroicons/react": "Heroicons", "@phosphor-icons/react": "Phosphor",
    "react-icons": "react-icons", "@tabler/icons-react": "Tabler", "@radix-ui/react-icons": "Radix Icons",
    "@iconify/react": "Iconify",
}
KNOWN_MOTION = {
    "framer-motion": "Framer Motion", "motion": "Motion", "gsap": "GSAP",
    "@react-spring/web": "react-spring", "@formkit/auto-animate": "AutoAnimate", "lottie-react": "Lottie",
}

# --- class-usage regexes (Tailwind v3/v4 syntax) -----------------------------
_B = r"(?<![\w-])"   # class boundary before
_A = r"(?![\w-])"    # class boundary after
COLOR = re.compile(_B + r"(?:bg|text|border|ring|from|via|to|fill|stroke|outline|accent|decoration|divide|placeholder|caret)-([a-z]+)-(\d{2,3})(?:/\d+)?" + _A)
NEUTRAL = re.compile(_B + r"(?:bg|text|border)-(white|black)(?:/\d+)?" + _A)
SEMANTIC = re.compile(_B + r"(?:bg|text|border|ring|fill|stroke|from|to)-(primary|secondary|accent|muted|destructive|foreground|background|card|popover|input|ring|brand|surface|success|warning|danger|info|neutral|base|content)(?:-(?:foreground|content|hover|subtle|strong|soft|\d{2,3}))?(?:/\d+)?" + _A)
RADIUS = re.compile(_B + r"rounded(?:-(?:ss|se|ee|es|tl|tr|br|bl|[tblrse]))?(?:-(none|xs|sm|md|lg|xl|2xl|3xl|4xl|full))?" + _A)
SHADOW = re.compile(_B + r"shadow(?:-(none|2xs|xs|sm|md|lg|xl|2xl|inner))?" + _A)
TEXT_SIZE = re.compile(_B + r"text-(xs|sm|base|lg|xl|[2-9]xl)" + _A)
SPACING = re.compile(_B + r"(?:p|px|py|pt|pb|pl|pr|ps|pe|gap|gap-x|gap-y|space-x|space-y|m|mx|my|mt|mb|ml|mr)-(\d+(?:\.\d+)?)" + _A)
DARK = re.compile(_B + r"dark:")
ARBITRARY = re.compile(_B + r"(?:bg|text|border|w|h|min-w|max-w|min-h|max-h|p[xytblr]?|m[xytblr]?|gap|rounded|shadow|top|left|right|bottom|inset|z|font|leading|tracking|grid-cols)-\[[^\]]{1,48}\]")
FONT_CLASS = re.compile(_B + r"font-(sans|serif|mono|display|heading|body|brand|title)" + _A)
CSS_VAR = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+);")


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            yield Path(dirpath) / name


def read(p: Path, limit: int = MAX_READ) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def block_after(text: str, start: int) -> str:
    """Text inside the first balanced {...} at or after `start`."""
    i = text.find("{", start)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return text[i + 1:]


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# --------------------------------------------------------------------- stack
def detect_stack(root: Path) -> dict:
    pkg_path = root / "package.json"
    deps: dict[str, str] = {}
    name = None
    if pkg_path.exists():
        try:
            pkg = json.loads(read(pkg_path))
            name = pkg.get("name")
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        except (json.JSONDecodeError, AttributeError):
            pass

    # Workspace / monorepo: the app's package.json may carry no deps of its own.
    deps_source = "package.json"
    if not any(key in deps for key, _ in KNOWN_FRAMEWORKS) and "tailwindcss" not in deps:
        for up in (root.parent, root.parent.parent):
            pp = up / "package.json"
            if not pp.exists() or pp == pkg_path:
                continue
            try:
                up_pkg = json.loads(read(pp))
                up_deps = {**up_pkg.get("dependencies", {}), **up_pkg.get("devDependencies", {})}
            except (json.JSONDecodeError, AttributeError):
                continue
            if up_deps:
                deps = {**up_deps, **deps}
                deps_source = os.path.relpath(pp, root)
                break

    # A workspace root (npm/yarn/pnpm workspaces) is not an app: point at the packages that are.
    workspace_apps: list[str] = []
    patterns: list[str] = []
    try:
        ws = json.loads(read(pkg_path)).get("workspaces") if pkg_path.exists() else None
        if isinstance(ws, dict):
            ws = ws.get("packages")
        if isinstance(ws, list):
            patterns += [w for w in ws if isinstance(w, str)]
    except (json.JSONDecodeError, AttributeError):
        pass
    pnpm = root / "pnpm-workspace.yaml"
    if pnpm.exists():
        patterns += re.findall(r"^\s*-\s*['\"]?([^'\"\n#]+)['\"]?", read(pnpm), re.M)
    for pat in patterns:
        for d in sorted(root.glob(pat.strip().rstrip("/"))):
            pj = d / "package.json"
            if not d.is_dir() or not pj.exists():
                continue
            try:
                dd = json.loads(read(pj))
                ddeps = {**dd.get("dependencies", {}), **dd.get("devDependencies", {})}
            except (json.JSONDecodeError, AttributeError):
                continue
            if any(key in ddeps for key, _ in KNOWN_FRAMEWORKS) or "tailwindcss" in ddeps:
                workspace_apps.append(os.path.relpath(d, root))

    # No package.json here, or one with no UI stack in it (a repo laid out as frontend/ +
    # backend/, an apps/ folder without a workspace file): look one and two levels down for
    # the packages that are apps, so the verdict can say where to run this instead.
    framework = next((label for key, label in KNOWN_FRAMEWORKS if key in deps), None)
    if not workspace_apps and framework is None and "tailwindcss" not in deps:
        skip = {"node_modules", "dist", "build", "out", "coverage", "target", "vendor", ".venv", "venv"}
        candidates: list[Path] = []
        for d in sorted(root.iterdir()) if root.is_dir() else []:
            if not d.is_dir() or d.name.startswith(".") or d.name in skip:
                continue
            candidates.append(d)
            candidates += [e for e in sorted(d.iterdir()) if e.is_dir() and not e.name.startswith(".") and e.name not in skip]
        for d in candidates:
            pj = d / "package.json"
            if not pj.exists():
                continue
            try:
                dd = json.loads(read(pj))
                ddeps = {**dd.get("dependencies", {}), **dd.get("devDependencies", {})}
            except (json.JSONDecodeError, AttributeError):
                continue
            if any(key in ddeps for key, _ in KNOWN_FRAMEWORKS) or "tailwindcss" in ddeps:
                workspace_apps.append(os.path.relpath(d, root))
    router = None
    if framework == "Next.js":
        if (root / "app").is_dir() or (root / "src" / "app").is_dir():
            router = "App Router"
        elif (root / "pages").is_dir() or (root / "src" / "pages").is_dir():
            router = "Pages Router"

    tw = deps.get("tailwindcss")
    tw_major = None
    if tw:
        m = re.search(r"(\d+)", tw)
        tw_major = int(m.group(1)) if m else None
    if tw_major is None and ("@tailwindcss/vite" in deps or "@tailwindcss/postcss" in deps):
        tw_major = 4
    config_files = [p for p in root.glob("tailwind.config.*") if p.is_file()]

    shadcn = None
    cj = root / "components.json"
    if cj.exists():
        try:
            data = json.loads(read(cj))
            shadcn = {
                "style": data.get("style"),
                "baseColor": (data.get("tailwind") or {}).get("baseColor"),
                "cssVariables": (data.get("tailwind") or {}).get("cssVariables"),
                "componentsAlias": (data.get("aliases") or {}).get("components"),
            }
        except json.JSONDecodeError:
            shadcn = {"present": True}

    return {
        "name": name,
        "depsSource": deps_source,
        "framework": framework,
        "router": router,
        "react": deps.get("react"),
        "workspaceApps": workspace_apps,
        "tailwind": tw,
        "tailwindMajor": tw_major,
        "tailwindConfigFiles": [rel(root, p) for p in config_files],
        "ui": sorted({label for key, label in KNOWN_UI.items() if key in deps}),
        "icons": sorted({label for key, label in KNOWN_ICONS.items() if key in deps}),
        "motion": sorted({label for key, label in KNOWN_MOTION.items() if key in deps}),
        "shadcn": shadcn,
        "typescript": "typescript" in deps,
    }


# -------------------------------------------------------------------- tokens
def collect_tokens(root: Path, css_files: list[Path], stack: dict) -> dict:
    theme_vars: list[tuple[str, str, str]] = []   # (file, name, value)
    root_vars: list[tuple[str, str, str]] = []
    dark_block = False
    for p in css_files:
        text = read(p)
        if not text:
            continue
        for m in re.finditer(r"@theme\b[^{]*", text):
            for name, value in CSS_VAR.findall(block_after(text, m.end())):
                theme_vars.append((rel(root, p), name, value.strip()))
        for m in re.finditer(r"(?<![\w-]):root\b[^{]*", text):
            for name, value in CSS_VAR.findall(block_after(text, m.end())):
                root_vars.append((rel(root, p), name, value.strip()))
        if re.search(r"(\.dark\b|\[data-theme=|prefers-color-scheme:\s*dark)[^{]*\{[^}]*--", text):
            dark_block = True

    config_extract: dict[str, str] = {}
    for f in stack.get("tailwindConfigFiles", []):
        text = read(root / f)
        idx = text.find("extend")
        if idx < 0:
            continue
        ext = block_after(text, idx)
        for key in ("colors", "fontFamily", "borderRadius", "boxShadow", "spacing", "fontSize", "screens"):
            m = re.search(rf"\b{key}\s*:", ext)
            if m:
                sub = block_after(ext, m.end()).strip("\n")
                lines = [ln.rstrip() for ln in sub.splitlines() if ln.strip()]
                config_extract[key] = "\n".join(lines[:25]) + ("\n  …" if len(lines) > 25 else "")

    return {
        "theme": theme_vars[:120],
        "root": root_vars[:120],
        "darkBlock": dark_block,
        "configExtend": config_extract,
    }


# --------------------------------------------------------------------- fonts
def collect_fonts(root: Path, src_files: list[Path], css_files: list[Path], tokens: dict) -> dict:
    next_font, google, face = set(), set(), set()
    for p in src_files[:MAX_SRC_FILES]:
        text = read(p, 120_000)
        if "next/font" in text:
            for names in re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/(?:google|local)['\"]", text):
                next_font.update(n.strip().split(" as ")[0] for n in names.split(",") if n.strip())
        for q in re.findall(r"fonts\.googleapis\.com/css2?\?([^\"'\s>]+)", text):
            for fam in re.findall(r"family=([^&:]+)", q):
                google.add(fam.replace("+", " "))
    for p in css_files:
        text = read(p)
        for q in re.findall(r"fonts\.googleapis\.com/css2?\?([^\"'\s)]+)", text):
            for fam in re.findall(r"family=([^&:]+)", q):
                google.add(fam.replace("+", " "))
        for m in re.finditer(r"@font-face\b[^{]*", text):
            fm = re.search(r"font-family\s*:\s*[\"']?([^;\"']+)", block_after(text, m.end()))
            if fm:
                face.add(fm.group(1).strip())
    token_fonts = [
        (n, v.split(",")[0].strip().strip("\"'"))
        for _, n, v in tokens["theme"] + tokens["root"] if n.startswith("--font")
    ]
    return {"nextFont": sorted(next_font), "googleLinks": sorted(google), "fontFace": sorted(face), "tokenFonts": token_fonts[:12]}


# ---------------------------------------------------------------- components
COMPONENT_DIR_NAMES = {"components", "ui", "primitives", "design-system", "elements", "shared"}


def component_inventory(root: Path, src_files: list[Path]) -> dict:
    primitives, composed = [], []
    for p in src_files:
        if p.suffix not in {".tsx", ".jsx", ".vue", ".svelte"}:
            continue
        stem = p.stem
        if stem.lower() in {"index", "page", "layout", "loading", "error", "not-found", "route", "template"}:
            continue
        if re.search(r"\.(test|spec|stories)$", stem):
            continue
        parts = {part.lower() for part in p.parts}
        if not (parts & COMPONENT_DIR_NAMES):
            continue
        entry = rel(root, p)
        if re.search(r"/(ui|primitives)/", "/" + entry.replace(os.sep, "/")):
            primitives.append(entry)
        else:
            composed.append(entry)
    return {"primitives": sorted(primitives)[:60], "composed": sorted(composed)[:60]}


# --------------------------------------------------------------------- usage
def usage_stats(src_files: list[Path]) -> dict:
    color_fam, color_tok, neutral, semantic = (collections.Counter() for _ in range(4))
    radius, shadow, text_size, spacing, font_cls, arbitrary = (collections.Counter() for _ in range(6))
    dark = 0
    scanned = 0
    for p in src_files[:MAX_SRC_FILES]:
        text = read(p, 200_000)
        if not text:
            continue
        scanned += 1
        for m in COLOR.finditer(text):
            color_fam[m.group(1)] += 1
            color_tok[m.group(0)] += 1
        for m in NEUTRAL.finditer(text):
            neutral[m.group(0)] += 1
        for m in SEMANTIC.finditer(text):
            semantic[m.group(0)] += 1
        for m in RADIUS.finditer(text):
            radius[m.group(1) or "default"] += 1
        for m in SHADOW.finditer(text):
            shadow[m.group(1) or "default"] += 1
        for m in TEXT_SIZE.finditer(text):
            text_size[m.group(1)] += 1
        for m in SPACING.finditer(text):
            spacing[m.group(1)] += 1
        for m in FONT_CLASS.finditer(text):
            font_cls[m.group(1)] += 1
        for m in ARBITRARY.finditer(text):
            arbitrary[m.group(0)] += 1
        dark += len(DARK.findall(text))
    raw_total = sum(color_fam.values())
    sem_total = sum(semantic.values())
    return {
        "scannedFiles": scanned,
        "colorFamilies": color_fam.most_common(8),
        "colorTokens": color_tok.most_common(12),
        "neutrals": neutral.most_common(4),
        "semantic": semantic.most_common(10),
        "rawTotal": raw_total,
        "semanticTotal": sem_total,
        "radius": radius.most_common(6),
        "shadow": shadow.most_common(6),
        "textSize": text_size.most_common(8),
        "spacing": spacing.most_common(8),
        "fontClasses": font_cls.most_common(6),
        "dark": dark,
        "arbitraryTotal": sum(arbitrary.values()),
        "arbitrary": arbitrary.most_common(8),
    }


# ----------------------------------------------------------------- documents
DOC_GLOBS = [
    "DESIGN.md", "DESIGN_SYSTEM.md", "STYLEGUIDE.md", "STYLE_GUIDE.md", "BRAND.md",
    "docs/design/*.md", "docs/DESIGN*.md", "docs/design-system/*.md", "docs/brand*.md",
    "design-system/**/MASTER.md", ".ui-craft/DIRECTION.md", "design/*.md",
]


def find_docs(root: Path) -> list[str]:
    found = []
    for pattern in DOC_GLOBS:
        for p in root.glob(pattern):
            if p.is_file() and not (set(p.parts) & SKIP_DIRS):
                found.append(rel(root, p))
    return sorted(set(found))[:12]


# ------------------------------------------------------------------- verdict
def verdict(stack: dict, tokens: dict, fonts: dict, comps: dict, usage: dict, docs: list[str]) -> dict:
    tokens_declared = bool(tokens["theme"] or tokens["root"] or tokens["configExtend"])
    established = (
        usage["rawTotal"] + usage["semanticTotal"] >= 25
        or len(comps["primitives"]) + len(comps["composed"]) >= 4
        or tokens_declared
    )
    lines = []
    total_color = usage["rawTotal"] + usage["semanticTotal"]
    if total_color:
        sem_pct = round(100 * usage["semanticTotal"] / total_color)
        if usage["colorFamilies"]:
            fam, n = usage["colorFamilies"][0]
            lines.append(f"Dominant hue family: **{fam}** ({n} uses)")
        lines.append(f"Color naming: {sem_pct}% semantic tokens (`bg-primary`) vs {100 - sem_pct}% raw palette (`bg-indigo-600`)")
    if usage["radius"]:
        lines.append(f"Radius: **rounded-{usage['radius'][0][0]}** dominant" if usage["radius"][0][0] != "default" else "Radius: **rounded** (default) dominant")
    if usage["shadow"]:
        lines.append(f"Shadow: **shadow-{usage['shadow'][0][0]}** dominant" if usage["shadow"][0][0] != "default" else "Shadow: **shadow** (default) dominant")
    if usage["textSize"]:
        lines.append(f"Most-used text size: **text-{usage['textSize'][0][0]}**")
    all_fonts = fonts["nextFont"] + fonts["googleLinks"] + fonts["fontFace"] + [v for _, v in fonts["tokenFonts"]]
    if all_fonts:
        lines.append("Fonts: " + ", ".join(dict.fromkeys(all_fonts))[:160])
    lines.append("Dark mode: " + ("present" if usage["dark"] or tokens["darkBlock"] else "not used"))
    if usage["arbitraryTotal"] >= 8:
        lines.append(f"Token drift: {usage['arbitraryTotal']} arbitrary values (`w-[…]`, `bg-[#…]`) — missing tokens, or one-offs to avoid repeating")
    if docs:
        lines.append("Design docs exist: read them first — " + ", ".join(docs))
    return {"established": established, "lines": lines}


# ------------------------------------------------------------------ rendering
def md(data: dict) -> str:
    s, t, f, c, u, v = data["stack"], data["tokens"], data["fonts"], data["components"], data["usage"], data["verdict"]
    out = [f"# ui-craft inspect — {data['root']}", ""]

    # Stack
    bits = []
    if s["framework"]:
        bits.append(s["framework"] + (f" ({s['router']})" if s["router"] else ""))
    if s["react"]:
        bits.append(f"React {s['react']}")
    if s["tailwind"] or s["tailwindMajor"]:
        mode = "CSS-first @theme" if s["tailwindMajor"] == 4 else "tailwind.config"
        bits.append(f"Tailwind {s['tailwind'] or s['tailwindMajor']} ({mode})")
    if s["shadcn"]:
        sc = s["shadcn"]
        bits.append("shadcn/ui" + (f" (style {sc.get('style')}, base {sc.get('baseColor')})" if sc.get("style") else ""))
    if s["ui"]:
        bits.append("UI: " + ", ".join(s["ui"]))
    if s["icons"]:
        bits.append("Icons: " + ", ".join(s["icons"]))
    if s["motion"]:
        bits.append("Motion: " + ", ".join(s["motion"]))
    out += ["## Stack", "- " + (" · ".join(bits) if bits else "no package.json or no recognised UI stack")]
    if s.get("workspaceApps"):
        out.append("- not an app itself; the UI apps are: " + ", ".join(f"`{a}`" for a in s["workspaceApps"]) + " — run inspect.py (and the dev server) in the one you are changing")
    if s.get("depsSource") and s["depsSource"] != "package.json":
        out.append(f"- dependencies read from `{s['depsSource']}` (workspace root)")
    out.append("")

    # Tokens
    out.append("## Declared tokens")
    if t["theme"]:
        by_file = collections.defaultdict(list)
        for file, name, value in t["theme"]:
            by_file[file].append(f"{name}: {value}")
        for file, items in by_file.items():
            out += [f"### `@theme` in {file}", "```css", *items[:60], *(["…"] if len(items) > 60 else []), "```"]
    if t["root"]:
        by_file = collections.defaultdict(list)
        for file, name, value in t["root"]:
            by_file[file].append(f"{name}: {value}")
        for file, items in by_file.items():
            out += [f"### `:root` in {file}", "```css", *items[:40], *(["…"] if len(items) > 40 else []), "```"]
    for key, snippet in t["configExtend"].items():
        out += [f"### tailwind.config `extend.{key}`", "```js", snippet, "```"]
    if not (t["theme"] or t["root"] or t["configExtend"]):
        out.append("- none declared (no @theme, :root vars, or config extend)")
    out.append("")

    # Fonts
    out.append("## Fonts")
    if f["nextFont"]:
        out.append("- next/font: " + ", ".join(f["nextFont"]))
    if f["googleLinks"]:
        out.append("- Google Fonts links: " + ", ".join(f["googleLinks"]))
    if f["fontFace"]:
        out.append("- @font-face: " + ", ".join(f["fontFace"]))
    for name, value in f["tokenFonts"]:
        out.append(f"- token {name}: {value}")
    if u["fontClasses"]:
        out.append("- classes in use: " + ", ".join(f"font-{k} ×{n}" for k, n in u["fontClasses"]))
    if len(out) and out[-1] == "## Fonts":
        out.append("- nothing explicit (system / Tailwind default stack)")
    out.append("")

    # Components
    out.append(f"## Components ({len(c['primitives']) + len(c['composed'])} found)")
    if c["primitives"]:
        out.append("- primitives (`ui/`): " + ", ".join(Path(p).stem for p in c["primitives"]))
    if c["composed"]:
        out.append("- composed: " + ", ".join(Path(p).stem for p in c["composed"][:40]) + (" …" if len(c["composed"]) > 40 else ""))
    if not (c["primitives"] or c["composed"]):
        out.append("- none found in components/ ui/ primitives/ dirs")
    out.append("")

    # Usage
    out.append(f"## What the code actually uses ({u['scannedFiles']} source files)")
    total = u["rawTotal"] + u["semanticTotal"]
    if total:
        out.append("- color families: " + ", ".join(f"{k} {n}" for k, n in u["colorFamilies"]) +
                   f"  → raw {u['rawTotal']} / semantic {u['semanticTotal']}")
        if u["colorTokens"]:
            out.append("- most-used color classes: " + ", ".join(f"{k} {n}" for k, n in u["colorTokens"]))
        if u["semantic"]:
            out.append("- semantic tokens: " + ", ".join(f"{k} {n}" for k, n in u["semantic"]))
        if u["neutrals"]:
            out.append("- neutrals: " + ", ".join(f"{k} {n}" for k, n in u["neutrals"]))
    else:
        out.append("- no Tailwind color classes found")
    if u["radius"]:
        out.append("- radius: " + ", ".join(f"rounded{'' if k == 'default' else '-' + k} {n}" for k, n in u["radius"]))
    if u["shadow"]:
        out.append("- shadow: " + ", ".join(f"shadow{'' if k == 'default' else '-' + k} {n}" for k, n in u["shadow"]))
    if u["textSize"]:
        out.append("- text sizes: " + ", ".join(f"text-{k} {n}" for k, n in u["textSize"]))
    if u["spacing"]:
        out.append("- spacing steps: " + ", ".join(f"{k} ×{n}" for k, n in u["spacing"]))
    out.append(f"- `dark:` variants: {u['dark']}")
    if u["arbitraryTotal"]:
        out.append(f"- arbitrary values: {u['arbitraryTotal']} — " + ", ".join(f"{k} ×{n}" for k, n in u["arbitrary"][:6]))
    out.append("")

    # Docs
    out.append("## Existing design docs")
    out += [f"- {d}" for d in data["docs"]] or ["- none"]
    out.append("")

    # Verdict
    out.append("## Verdict")
    if v["established"]:
        out.append("**Established conventions detected → match them.** Reuse the primitives, hue, radius, and shadow below; don't introduce a second system.")
    else:
        out.append("**Greenfield (no meaningful conventions yet) → establish a direction.** Read `references/anti-generic.md`, write the six-line brief, then build.")
    out += [f"- {ln}" for ln in v["lines"]]
    return "\n".join(out) + "\n"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    root = Path(args[0]).resolve() if args else Path.cwd()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    files = list(iter_files(root))
    src_files = [p for p in files if p.suffix in SRC_EXT]
    css_files = [p for p in files if p.suffix in CSS_EXT]

    stack = detect_stack(root)
    tokens = collect_tokens(root, css_files, stack)
    fonts = collect_fonts(root, src_files, css_files, tokens)
    comps = component_inventory(root, src_files)
    usage = usage_stats(src_files)
    docs = find_docs(root)
    data = {
        "root": str(root), "stack": stack, "tokens": tokens, "fonts": fonts,
        "components": comps, "usage": usage, "docs": docs,
        "verdict": verdict(stack, tokens, fonts, comps, usage, docs),
    }
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(md(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
