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
    "@nuxt/ui": "Nuxt UI", "@nuxt/ui-pro": "Nuxt UI Pro", "element-plus": "Element Plus", "vuetify": "Vuetify",
    "primevue": "PrimeVue", "naive-ui": "Naive UI", "reka-ui": "Reka UI", "radix-vue": "Radix Vue",
    "@headlessui/vue": "Headless UI", "ant-design-vue": "Ant Design Vue", "quasar": "Quasar",
}
KNOWN_ICONS = {
    "lucide-react": "Lucide", "@heroicons/react": "Heroicons", "@phosphor-icons/react": "Phosphor",
    "react-icons": "react-icons", "@tabler/icons-react": "Tabler", "@radix-ui/react-icons": "Radix Icons",
    "@iconify/react": "Iconify",
    "lucide-vue-next": "Lucide", "@iconify/vue": "Iconify", "@heroicons/vue": "Heroicons", "@phosphor-icons/vue": "Phosphor",
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


def iter_dirs(root: Path):
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for d in dirnames:
            yield Path(dirpath) / d


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
    if framework == "Nuxt":
        src = root / "app" if (root / "app" / "pages").is_dir() or (root / "app" / "app.vue").is_file() else root
        router = f"file routes in {rel(root, src / 'pages')}/" if (src / "pages").is_dir() else None
    if framework == "SvelteKit" and (root / "src" / "routes").is_dir():
        router = "file routes in src/routes/"
    if framework == "Astro" and (root / "src" / "pages").is_dir():
        router = "file routes in src/pages/"
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
        "vue": deps.get("vue"),
        "svelte": deps.get("svelte"),
        "frameworkVersion": next((deps.get(key) for key, label in KNOWN_FRAMEWORKS if label == framework and key in deps), None),
        "workspaceApps": workspace_apps,
        "integrations": astro_integrations(root) if framework == "Astro" else [],
        "tailwind": tw,
        "tailwindMajor": tw_major,
        "tailwindConfigFiles": [rel(root, p) for p in config_files],
        "ui": sorted({label for key, label in KNOWN_UI.items() if key in deps}),
        "icons": sorted({label for key, label in KNOWN_ICONS.items() if key in deps}
                        | {f"Iconify ({k.split('/', 1)[1]})" for k in deps if k.startswith("@iconify-json/")}),
        "motion": sorted({label for key, label in KNOWN_MOTION.items() if key in deps}),
        "shadcn": shadcn,
        "typescript": "typescript" in deps,
        "deps": deps,
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


# ---------------------------------------------------------------- start here
# The reading list for a match task. Two real-repository trials put two thirds of the
# wall clock into reading files to learn what this section now says outright: the
# vocabulary the CSS defines, what every page imports, one line per page, where the
# strings live, and what stands between a fresh browser and the page.
PAGE_DIR_NAMES = {"pages", "views", "screens", "routes", "app"}
BOOT_STEM = re.compile(r"^(store|stores|provider|providers|context|app|_app|main|layout|root|bootstrap|session|auth)$", re.I)
SPLASH_STEM = re.compile(r"^(splash|intro|boot|onboarding|welcome|preloader|loader)$", re.I)
I18N_DIRS = {"i18n", "locales", "locale", "lang", "langs", "translations", "messages", "intl"}
I18N_LIBS = {
    "react-i18next": "react-i18next", "i18next": "i18next", "next-intl": "next-intl", "vue-i18n": "vue-i18n",
    "@lingui/react": "Lingui", "react-intl": "react-intl", "@formatjs/intl": "FormatJS", "svelte-i18n": "svelte-i18n",
}
CLASS_USE = r"(?<=[\"'`\s])%s(?=[\"'`\s])"   # the class as a token inside a class string


def _cls_uses(name: str, texts: list[str]) -> int:
    pat = re.compile(CLASS_USE % re.escape(name))
    return sum(len(pat.findall(t)) for t in texts)


def css_vocabulary(root: Path, css_files: list[Path], src_texts: list[str]) -> list[dict]:
    """Single-class rules (`.card {`, `.btn-primary {`) with their first declarations, by use."""
    vocab: dict[str, dict] = {}
    for p in css_files:
        text = read(p)
        for m in re.finditer(r"(?m)^[ \t]*\.([a-zA-Z][\w-]*)\s*\{", text):
            name = m.group(1)
            if name in vocab or name in {"dark", "light"}:      # a theme selector, not a class a page uses
                continue
            decl = re.sub(r"/\*.*?\*/", "", block_after(text, m.start()), flags=re.S)
            decl = " ".join(decl.split()).strip()
            if not decl:
                continue
            vocab[name] = {
                "name": name, "file": rel(root, p), "line": text.count("\n", 0, m.start()) + 1,
                "decl": decl[:110] + ("…" if len(decl) > 110 else ""),
            }
    for entry in vocab.values():
        entry["uses"] = _cls_uses(entry["name"], src_texts)
    items = sorted((v for v in vocab.values() if v["uses"] >= 2), key=lambda v: -v["uses"])
    return items[:16]


def props_of(path: Path) -> list[str]:
    """Prop names of a component file's main export, from its destructured signature or its
    Props type — enough to use it without opening the file."""
    t = read(path, 120_000)
    if path.suffix in {".svelte", ".astro"}:
        code = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", _script_blocks(t), flags=re.S))
        m = re.search(r"let\s*\{(.*?)\}\s*(?::[^=]*)?=\s*\$props\(\)", code, re.S) \
            or re.search(r"const\s*\{(.*?)\}\s*=\s*Astro\.props", code, re.S)
        names = _destructured(m.group(1)) if m else re.findall(r"export\s+let\s+(\w+)", code)
        if not names:
            pm = re.search(r"(?:interface|type)\s+Props\b[^{]*\{([^}]*)\}", code)
            names = re.findall(r"^\s*(\w+)\??\s*:", pm.group(1), re.M) if pm else []
        return names[:9]
    t = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S))
    m = re.search(r"export\s+(?:default\s+)?function\s+\w+\s*\(\s*\{([^}]*)\}", t) \
        or re.search(r"export\s+(?:const|default)\s+\w*\s*=?\s*(?:React\.forwardRef[^(]*)?\(?\s*\{([^}]*)\}", t)
    names: list[str] = []
    if m:
        for part in m.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            name = re.split(r"[=:]", part, 1)[0].strip()
            if name and re.match(r"^\.{0,3}\w+$", name):
                names.append(name)
    if not names and "defineProps" in t:                 # Vue: defineProps<{ … }>() or defineProps({ … })
        dm = re.search(r"defineProps<\s*\{(.*?)\}\s*>", t, re.S)
        if dm:
            names = [m.group(1) for part in re.split(r"[;,\n]", dm.group(1))
                     for m in [re.match(r"\s*['\"]?(\w+)['\"]?\??\s*:", part)] if m]
        else:
            om = re.search(r"defineProps\(\s*\{", t)
            if om:
                names = _top_level_keys(block_after(t, om.start()))
            else:
                am = re.search(r"defineProps\(\s*\[([^\]]*)\]", t)
                if am:
                    names = re.findall(r"['\"](\w+)['\"]", am.group(1))
    if not names:
        pm = re.search(r"(?:interface|type)\s+\w*Props\b[^{]*\{([^}]*)\}", t)
        if pm:
            names = [n for n in re.findall(r"^\s*(\w+)\??\s*:", pm.group(1), re.M)]
    return names[:9]


def _top_level_keys(block: str) -> list[str]:
    """Keys at depth 0 of an object literal's body: { title: String, size: { type: … } } → title, size."""
    keys, depth, i = [], 0, 0
    while i < len(block):
        ch = block[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif depth == 0:
            m = re.match(r"\s*['\"]?(\w+)['\"]?\s*:", block[i:])
            if m and (i == 0 or block[i - 1] in ",{\n \t"):
                keys.append(m.group(1))
                i += m.end()
                continue
        i += 1
    return list(dict.fromkeys(keys))


def import_fanin(root: Path, src_files: list[Path]) -> list[dict]:
    """Local modules by how many files import them: the chrome, the store, the strings."""
    counts: collections.Counter = collections.Counter()
    src_dir = root / "src" if (root / "src").is_dir() else root
    for p in src_files:
        if p.suffix not in {".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro"}:
            continue
        text = read(p, 200_000)
        seen = set()
        for spec in re.findall(r"""from\s+['"]([^'"]+)['"]""", text):
            if spec.startswith("."):
                target = (p.parent / spec).resolve()
            elif spec.startswith(("@/", "~/")):
                target = (src_dir / spec[2:]).resolve()
            elif spec.startswith("$lib/"):
                target = (root / "src" / "lib" / spec[5:]).resolve()
            else:
                continue
            if target in seen:
                continue
            seen.add(target)
            counts[target] += 1
    out = []
    for target, n in counts.most_common(80):
        found = None
        for suffix in ("", ".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte", ".astro", "/index.tsx", "/index.ts", "/index.js"):
            c = Path(str(target) + suffix)
            if c.is_file():
                found = c
                break
        if not found:
            continue
        parts = {x.lower() for x in found.parts}
        is_component = bool(parts & COMPONENT_DIR_NAMES)
        if n >= 3 or (is_component and n >= 2):
            out.append({"file": rel(root, found), "importers": n, "component": is_component,
                        "props": props_of(found) if is_component else []})
    return out[:12]


def _signals(text: str) -> list[str]:
    signals = []
    if re.search(r"export\s+default\s+async\s+function", text):
        signals.append("server component")
    if re.search(r"<(?:form|UForm|u-form|el-form|ElForm|v-form|VForm)\b", text):
        signals.append("form")
    n_fields = len(re.findall(r"<(?:input|select|textarea)\b|<(?:U|u-|El|el-|V|v-)?(?:Input|input|Select|select|Textarea|textarea|SelectMenu|select-menu|InputNumber|Checkbox|Switch|RadioGroup)\b(?![\w-])", text))
    if n_fields:
        signals.append(f"{n_fields} field{'s' if n_fields > 1 else ''}")
    if re.search(r"<(?:table|UTable|u-table|el-table|ElTable|VDataTable|v-data-table)\b", text):
        signals.append("table")
    elif (".map(" in text and re.search(r"<(?:li|article|tr)\b", text)) or "v-for=" in text or "{#each" in text:
        signals.append("list")
    if re.search(r'role="dialog"|<dialog\b|<Dialog\b|<(?:UModal|USlideover|u-modal|el-dialog|ElDialog|VDialog|v-dialog)\b', text):
        signals.append("dialog")
    data = [f"content `{c}`" for c in dict.fromkeys(re.findall(r"queryCollection(?:Navigation)?\(\s*['\"](\w+)['\"]", text))]
    data += [f"fetch `{u}`" for u in dict.fromkeys(re.findall(r"(?:useFetch|useLazyFetch|\$fetch)\(\s*['\"`]([^'\"`$]+)", text))]
    data += [f"collection `{c}`" for c in dict.fromkeys(re.findall(r"\b(?:getCollection|getEntry|getEntries)\(\s*['\"](\w+)['\"]", text))]
    islands = list(dict.fromkeys(re.findall(r"<([A-Z]\w*)[^>]*\sclient:(load|idle|visible|only|media)\b", text)))
    if islands:
        signals.append("islands " + ", ".join(f"{n} (client:{d})" for n, d in islands[:3]))
    if data:
        signals.append("data: " + ", ".join(data[:3]))
    return signals


def _resolve_import(root: Path, from_file: Path, spec: str) -> Path | None:
    """A local import's file: relative, `@/` and `~/` aliases, or a bare path from the root or src/."""
    if spec.startswith("."):
        bases = [from_file.parent / spec]
    elif spec.startswith("$lib/"):                          # SvelteKit's alias for src/lib
        bases = [root / "src" / "lib" / spec[5:]]
    else:
        stripped = re.sub(r"^[@~]/", "", spec)
        bases = [root / stripped, root / "src" / stripped]
    for b in bases:
        for ext in ("", ".tsx", ".jsx", ".ts", ".js", ".svelte", ".astro", ".vue", "/index.tsx", "/index.jsx", "/index.ts", "/index.js"):
            c = Path(str(b) + ext)
            if c.is_file():
                return Path(os.path.normpath(c))
    return None


def _rendered_by(root: Path, page: Path, text: str) -> dict | None:
    """The local component a thin page hands everything to — a layout or template that is the real page."""
    m = re.search(r"return\s*\(?\s*<([A-Z]\w*)", text)
    if not m:
        return None
    name = m.group(1)
    im = re.search(r"import\s+(?:\{[^}]*\b" + re.escape(name) + r"\b[^}]*\}|" + re.escape(name) + r"\b[^;'\"]*)\s*from\s*['\"]([^'\"]+)['\"]", text)
    if not im:
        return None
    target = _resolve_import(root, page, im.group(1))
    if not target or target == page or target.suffix not in {".tsx", ".jsx"}:
        return None
    t = read(target, 200_000)
    signals = _signals(t)
    if not signals and t.count("\n") < 30:          # a wrapper, not the page
        return None
    return {"name": name, "file": rel(root, target), "lines": t.count("\n") + 1, "signals": signals}


def next_layouts(root: Path) -> list[dict]:
    """App Router layouts, root first: what every page under them is wrapped in."""
    app_dir = next((d for d in (root / "app", root / "src" / "app") if d.is_dir()), None)
    if not app_dir:
        return []
    out = []
    for lay in sorted(app_dir.rglob("layout.*"), key=lambda q: (len(q.parts), str(q))):
        if set(lay.parts) & SKIP_DIRS or lay.suffix not in {".tsx", ".jsx", ".js", ".ts"}:
            continue
        t = read(lay, 200_000)
        segs = lay.relative_to(app_dir).parent.parts
        local: list[str] = []
        for names, spec in re.findall(r"import\s+(\{[^}]+\}|\w+)\s*from\s*['\"]([^'\"]+)['\"]", t):
            if spec.endswith(".css") or not _resolve_import(root, lay, spec):
                continue
            local += re.findall(r"[A-Z]\w*", names)
        used = [n for n in dict.fromkeys(local) if re.search(r"<" + n + r"\b", t)]
        providers = [n for n in used if "Provider" in n] + sorted({m for m in re.findall(r"<(\w*Provider\w*)", t) if m not in used})
        fonts = [x.strip().split(" as ")[0] for f in re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/(?:google|local)['\"]", t) for x in f.split(",") if x.strip()]
        out.append({
            "file": rel(root, lay), "scope": "/" + "/".join(segs),
            "css": re.findall(r"import\s+['\"]([^'\"]+\.css)['\"]", t), "fonts": fonts,
            "providers": providers, "chrome": [n for n in used if n not in providers],
        })
    return out[:6]


def theme_mechanism(root: Path, css_files: list[Path], stack: dict, src_files: list[Path]) -> str | None:
    """What `dark:` keys on, and who sets it — the dark pass in render.mjs needs to know."""
    how = where = None
    for c in css_files:
        t = read(c)
        m = re.search(r"@custom-variant\s+dark\s*(?:\(([^)]*)\)|\{([^}]*)\})", t)
        if m:
            sel = (m.group(1) or m.group(2) or "").strip()
            how = "`.dark` on an ancestor" if ".dark" in sel else ("`[data-theme]` on an ancestor" if "data-theme" in sel else f"`{sel[:40]}`")
            where = f"`{rel(root, c)}:{t[:m.start()].count(chr(10)) + 1}` (`@custom-variant dark`)"
            break
    if how is None:
        for cfg in stack.get("tailwindConfigFiles") or []:
            m = re.search(r"darkMode\s*:\s*(\[[^\]]*\]|['\"][^'\"]*['\"])", read(root / cfg))
            if m:
                v = m.group(1)
                how = ("`[data-theme]` on an ancestor" if "data-" in v else "`.dark` on an ancestor" if "class" in v or "selector" in v
                       else "the OS scheme (`prefers-color-scheme`)" if "media" in v else f"`{v[:40]}`")
                where = f"`{cfg}` (`darkMode: {v[:40]}`)"
                break
    uses_dark = any("dark:" in read(p, 200_000) for p in src_files[:MAX_SRC_FILES] if p.suffix in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".mdx"})
    deps = stack.get("deps") or {}
    color_mode = None
    if any(k in deps for k in ("@nuxtjs/color-mode", "@nuxt/ui", "@nuxt/ui-pro")):
        nuxt_ui_on = any(k in deps for k in ("@nuxt/ui", "@nuxt/ui-pro"))
        cfg = "".join(read(c) for c in root.glob("nuxt.config.*"))
        m = re.search(r"colorMode\s*:\s*\{", cfg)
        opts = dict(re.findall(r"(\w+)\s*:\s*['\"]([^'\"]*)['\"]", block_after(cfg, m.start()))) if m else {}
        color_mode = {"cls": "dark" + opts.get("classSuffix", "" if nuxt_ui_on else "-mode"), "pref": opts.get("preference", "system"),
                      "key": opts.get("storageKey", "nuxt-color-mode"), "nuxtui": nuxt_ui_on}
        if how is None:
            how = f"`.{color_mode['cls']}` on `<html>`"
            where = "the class @nuxtjs/color-mode sets" + (" (Nuxt UI brings it)" if nuxt_ui_on else "")
    plain = False
    if how is None and "@astrojs/starlight" in deps:
        how, where, plain = "`[data-theme=dark]` on `<html>`", "Starlight's own CSS (`--sl-color-*` properties)", True
    if how is None:                                  # plain CSS: dark rules keyed on an attribute, a class, or the OS scheme
        for c in css_files:
            t = read(c)
            for pat, label in ((r"\[data-theme=['\"]?dark", "`[data-theme=dark]` on `<html>`"),
                               (r"(?:^|[\s,}])(?::root|html)?\.dark\b", "`.dark` on `<html>`"),
                               (r"prefers-color-scheme:\s*dark", "the OS scheme (`prefers-color-scheme`)")):
                m = re.search(pat, t, re.M)
                if m:
                    how, where, plain = label, f"`{rel(root, c)}:{t[:m.start()].count(chr(10)) + 1}` (plain CSS)", True
                    break
            if how:
                break
    if how is None:
        if not stack.get("tailwind") or not uses_dark:
            return None
        how, where = "the OS scheme (`prefers-color-scheme`)", "Tailwind's default, no toggle in the app"
    setter = None
    if "mode-watcher" in deps:
        setter = "set before paint by mode-watcher (`<ModeWatcher />` in the root layout; localStorage `mode-watcher-mode`)"
    elif "@astrojs/starlight" in deps:
        setter = "set before paint by Starlight's theme select (localStorage `starlight-theme`; follows the OS until chosen)"
    else:                                            # an inline script at boot: SvelteKit's app.html, an Astro head component
        for f in [root / "src" / "app.html", *(q for q in src_files if q.suffix == ".astro")]:
            if not f.is_file():
                continue
            for body in re.findall(r"<script\b[^>]*>(.*?)</script>", read(f, 200_000), re.S):
                if "localStorage" in body and re.search(r"dataset\.theme|classList\.(?:add|toggle)|setAttribute\(\s*['\"]data-theme|colorScheme", body):
                    key = re.search(r"localStorage\.getItem\(\s*['\"]([^'\"]+)", body)
                    setter = f"set before paint by an inline script in `{rel(root, f)}`" + (f" (localStorage `{key.group(1)}`)" if key else "")
                    break
            if setter:
                break
    if "next-themes" in (stack.get("deps") or {}):
        for p in src_files:
            if p.suffix not in {".tsx", ".jsx"}:
                continue
            m = re.search(r"<ThemeProvider\b([^>]*)>", read(p, 100_000))
            if m:
                attrs = m.group(1)
                attr = re.search(r"attribute=\{?['\"]([^'\"]+)", attrs)
                default = re.search(r"defaultTheme=\{?['\"]?([\w.]+)", attrs)
                key = re.search(r"storageKey=\{?['\"]([^'\"]+)", attrs)
                dflt, dsrc = (default.group(1) if default else "light"), None
                if "." in dflt:                                   # {siteMetadata.theme}: read it from that module
                    obj, field = dflt.split(".", 1)
                    for q in src_files:
                        if q.stem.lower() == obj.lower():
                            mm = re.search(r"\b" + re.escape(field) + r"\s*:\s*['\"](\w+)['\"]", read(q, 100_000))
                            if mm:
                                dflt, dsrc = mm.group(1), rel(root, q)
                                break
                setter = (f"set before paint by next-themes in `{rel(root, p)}` (attribute `{attr.group(1) if attr else 'data-theme'}`, "
                          f"default `{dflt}`" + (f" from `{dsrc}`" if dsrc else "") + f", localStorage `{key.group(1) if key else 'theme'}`)")
                break
        setter = setter or "next-themes is installed"
    if color_mode:
        setter = (f"set before paint by @nuxtjs/color-mode (preference `{color_mode['pref']}`, localStorage `{color_mode['key']}`)"
                  + ("; Nuxt UI's components switch through their CSS variables" if color_mode["nuxtui"] else ""))
        if color_mode["nuxtui"]:
            uses_dark = True
    if plain:
        return f"dark styles apply under {how} — {where}" + (f"; {setter}" if setter else "")
    return f"`dark:` applies under {how} — {where}" + (f"; {setter}" if setter else "") + ("" if uses_dark else " — no `dark:` class uses it yet")


MIDDLEWARE_LIBS = {
    "@clerk/nextjs": "Clerk", "next-intl/middleware": "next-intl", "next-auth": "NextAuth", "@supabase/ssr": "Supabase",
    "@kinde-oss": "Kinde", "@auth0/nextjs-auth0": "Auth0", "@workos-inc": "WorkOS",
}


def middleware_line(root: Path) -> str | None:
    for name in ("middleware", "proxy"):
        for d in (root, root / "src"):
            for ext in (".ts", ".js", ".mjs"):
                p = d / f"{name}{ext}"
                if not p.is_file():
                    continue
                t = read(p)
                libs = [label for key, label in MIDDLEWARE_LIBS.items() if key in t]
                matchers = re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*createRouteMatcher\(\s*\[([^\]]*)\]", t)
                guarded = [grp for name, grp in matchers if re.search(r"protect|private|guard|member|admin", name, re.I)] or [grp for _, grp in matchers]
                pats = [x.strip().strip("'\"`") for grp in guarded[:1] for x in grp.split(",") if x.strip()]
                matcher = re.search(r"matcher\s*:\s*(\[[^\]]*\]|['\"][^'\"]*['\"])", t)
                bits = []
                if libs:
                    bits.append(", ".join(libs))
                if pats:
                    bits.append("guards " + ", ".join(f"`{x}`" for x in pats[:4]) + " — a render there needs a session (`--cookie` / `--storage-state`)")
                elif matcher:
                    bits.append(f"matcher `{matcher.group(1)[:60]}`")
                return f"`{rel(root, p)}` runs before every page" + (": " + "; ".join(bits) if bits else "")
    return None


def locale_routing(root: Path, src_files: list[Path], routes: list) -> dict | None:
    if not any("[locale]" in path or "[lang]" in path for path, _ in routes):
        return None
    for p in sorted(src_files, key=lambda q: (0 if re.search(r"i18n|routing|config", q.stem, re.I) else 1, str(q))):
        if p.suffix not in {".ts", ".tsx", ".js", ".mjs"}:
            continue
        t = read(p, 100_000)
        default = re.search(r"defaultLocale\s*:\s*['\"](\w[\w-]*)['\"]", t)
        if not default:
            continue
        locales = re.search(r"locales\s*:\s*\[([^\]]*)\]", t)
        prefix = re.search(r"localePrefix[^\n]*?['\"](always|as-needed|never)['\"]", t)
        return {
            "file": rel(root, p), "default": default.group(1),
            "locales": [x.strip().strip("'\"") for x in locales.group(1).split(",") if x.strip()] if locales else [],
            "prefix": prefix.group(1) if prefix else None,
        }
    return None


# ------------------------------------------------------------------ Vue / Nuxt
VUE_BUILTINS = {"Transition", "TransitionGroup", "KeepAlive", "Teleport", "Suspense", "Component", "Slot", "Template",
                "RouterView", "RouterLink", "NuxtLink", "NuxtPage", "NuxtLayout", "NuxtRouteAnnouncer", "ClientOnly",
                "NuxtLoadingIndicator", "NuxtImg", "NuxtPicture", "NuxtErrorBoundary", "ContentRenderer", "Icon"}


def vue_template(text: str) -> str:
    """The template of a single-file component: the first <template> to the last </template>."""
    m = re.search(r"<template(?:\s[^>]*)?>", text)
    if not m:
        return ""
    end = text.rfind("</template>")
    return text[m.end():end] if end > m.end() else text[m.end():]


def _pascal(tag: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[-_.]", tag) if w)


def vue_tags(template: str) -> list[str]:
    """Component tags in a template, in order of first use: <AppHeader>, <app-header> → AppHeader."""
    tags = re.findall(r"<([A-Z][A-Za-z0-9]*)\b|<([a-z][a-z0-9]*-[a-z0-9-]+)\b", template)
    return list(dict.fromkeys(_pascal(a or b) for a, b in tags))


def nuxt_src(root: Path) -> Path:
    """Nuxt 4 keeps the app in app/; Nuxt 3 at the root."""
    return root / "app" if (root / "app" / "pages").is_dir() or (root / "app" / "app.vue").is_file() else root


def nuxt_components(root: Path) -> dict[str, Path]:
    """Auto-imported component name → file. components/base/Button.vue is <BaseButton>, and
    components/base/BaseButton.vue too (a repeated prefix is dropped)."""
    base = nuxt_src(root) / "components"
    out: dict[str, Path] = {}
    if not base.is_dir():
        return out
    for f in sorted(base.rglob("*.vue")):
        if set(f.parts) & SKIP_DIRS:
            continue
        name = ""
        for seg in f.relative_to(base).with_suffix("").parts:
            seg = _pascal(seg.split(".")[0])
            if seg == "Index" and name:
                continue
            name = seg if seg.startswith(name) and name else name + seg
        out.setdefault(name, f)
    return out


def vue_component_uses(root: Path, src_files: list[Path], names: dict[str, Path]) -> list[dict]:
    """Auto-imported components by how many templates use them: Nuxt's answer to 'imported most'."""
    counts: collections.Counter = collections.Counter()
    for p in src_files:
        if p.suffix != ".vue":
            continue
        for tag in dict.fromkeys(vue_tags(vue_template(read(p, 200_000)))):
            if tag in names and names[tag] != p:
                counts[tag] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], rel(root, names[kv[0]])))   # ties by path: the same order every run
    return [{"file": rel(root, names[n]), "importers": c, "component": True, "props": props_of(names[n])} for n, c in ranked[:12]]


def nuxt_ui(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    """Nuxt UI's vocabulary: the colours app.config gives it, and its components by use."""
    if not any(k in deps for k in ("@nuxt/ui", "@nuxt/ui-pro")):
        return None
    colors, cfg = {}, None
    for c in (nuxt_src(root) / "app.config.ts", root / "app.config.ts", nuxt_src(root) / "app.config.js"):
        if c.is_file():
            t = read(c)
            m = re.search(r"colors\s*:\s*\{", t)
            if m:
                colors = dict(re.findall(r"(\w+)\s*:\s*['\"]([\w-]+)['\"]", block_after(t, m.start())))
            cfg = rel(root, c)
            break
    counts: collections.Counter = collections.Counter()
    for p in src_files:
        if p.suffix == ".vue":
            counts.update(t for t in vue_tags(vue_template(read(p, 200_000))) if re.match(r"^U[A-Z]", t))
    return {"config": cfg, "colors": colors, "components": counts.most_common(14)}


def nuxt_routes(root: Path) -> list[tuple[str, str]]:
    pages = nuxt_src(root) / "pages"
    out = []
    if not pages.is_dir():
        return out
    for f in sorted(pages.rglob("*.vue")):
        if set(f.parts) & SKIP_DIRS:
            continue
        segs = [x for x in f.relative_to(pages).with_suffix("").parts
                if x != "index" and not (x.startswith("(") and x.endswith(")"))]
        path = "/" + "/".join(segs)
        wraps = (f.parent / f.stem).is_dir()
        out.append((path + (" (wraps its children: <NuxtPage> inside)" if wraps else ""), rel(root, f)))
    return out


def vue_router_routes(root: Path, src_files: list[Path]) -> list[tuple[str, str]]:
    """routes: [{ path: '/x', component: () => import('../views/X.vue') }] in a vue-router file."""
    out = []
    for p in src_files:
        if p.suffix not in {".ts", ".js", ".mjs"} or "router" not in str(p).lower():
            continue
        t = read(p, 300_000)
        if "createRouter" not in t and "RouteRecordRaw" not in t:
            continue
        imports = dict(re.findall(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", t))
        for m in re.finditer(r"\bpath\s*:\s*['\"]([^'\"]*)['\"]", t):
            chunk = t[m.end(): m.end() + 600]
            nxt = re.search(r"\bpath\s*:", chunk)
            chunk = chunk[:nxt.start()] if nxt else chunk
            c = re.search(r"component\s*:\s*(?:\(\)\s*=>\s*import\(\s*['\"]([^'\"]+)['\"]\s*\)|(\w+))", chunk)
            if c:
                spec = c.group(1) or imports.get(c.group(2), "")
                target = (p.parent / spec).resolve() if spec.startswith(".") else (root / "src" / spec[2:]) if spec.startswith("@/") else None
                shown = rel(root, target) if target is not None else (c.group(2) or spec)
            elif re.search(r"\bredirect\s*:", chunk):
                shown = "(redirect)"
            else:
                shown = "(children below)"
            out.append((m.group(1) or "(child)", shown))
    return out[:40]


def nuxt_layouts(root: Path, src_files: list[Path]) -> list[dict]:
    src = nuxt_src(root)
    out = []
    uses: dict[str, list[str]] = collections.defaultdict(list)
    pages = src / "pages"
    for f in sorted(pages.rglob("*.vue")) if pages.is_dir() else []:
        m = re.search(r"definePageMeta\(\s*\{[^}]*?\blayout\s*:\s*(?:['\"]([\w-]+)['\"]|(false))", read(f, 100_000), re.S)
        uses[(m.group(1) or "none") if m else "default"].append(rel(root, f))
    app = src / "app.vue"
    if app.is_file():
        tags = [t for t in vue_tags(vue_template(read(app))) if t not in {"Template"}]
        out.append({"file": rel(root, app), "scopeText": "wraps every page", "css": [], "fonts": [], "providers": [], "chrome": tags[:8]})
    for lay in sorted((src / "layouts").glob("*.vue")) if (src / "layouts").is_dir() else []:
        tags = [t for t in vue_tags(vue_template(read(lay))) if t not in VUE_BUILTINS]
        who = uses.get(lay.stem, [])
        scope = ("wraps every page that names no other layout" if lay.stem == "default"
                 else f"wraps the pages that set `layout: '{lay.stem}'`" + (f" ({len(who)}: {', '.join(os.path.basename(x) for x in who[:4])})" if who else " (none found in pages/)"))
        out.append({"file": rel(root, lay), "scopeText": scope, "css": [], "fonts": [], "providers": [], "chrome": tags[:8]})
    return out[:8]


NUXT_AUTH = {"nuxt-auth-utils": "nuxt-auth-utils", "@sidebase/nuxt-auth": "sidebase auth", "@nuxtjs/supabase": "Supabase",
             "@clerk/nuxt": "Clerk", "@hebilicious/authjs-nuxt": "Auth.js", "@nuxtjs/auth-next": "nuxt auth"}


def nuxt_before(root: Path, deps: dict, src_files: list[Path]) -> list[str]:
    """Middleware, the server API, content: what stands between a fresh browser and a Nuxt page."""
    src = nuxt_src(root)
    lines = []
    mw = src / "middleware"
    if mw.is_dir():
        named: dict[str, list[str]] = collections.defaultdict(list)
        for f in sorted((src / "pages").rglob("*.vue")) if (src / "pages").is_dir() else []:
            m = re.search(r"\bmiddleware\s*:\s*(\[[^\]]*\]|['\"][\w-]+['\"])", read(f, 100_000))
            if m:
                for n in re.findall(r"['\"]([\w-]+)['\"]", m.group(1)):
                    named[n].append(os.path.basename(str(f)))
        for f in sorted(mw.glob("*.[tj]s")):
            name = f.stem.replace(".global", "")
            redirects = bool(re.search(r"\b(navigateTo|abortNavigation)\s*\(", read(f, 50_000)))
            session = " — it can redirect: a render there needs a session (`--cookie` / `--storage-state`)" if redirects else ""
            if f.stem.endswith(".global"):
                lines.append(f"`{rel(root, f)}` runs before every route{session}")
            else:
                who = named.get(name, [])
                lines.append(f"`{rel(root, f)}` runs before the pages that name it" + (f": {', '.join(who[:5])}" if who else " (none found in pages/)") + session)
    auth = [label for key, label in NUXT_AUTH.items() if key in deps]
    if auth:
        lines.append(f"auth: {', '.join(auth)} — a signed-in page needs a session (`--storage-state`)")
    api = sorted((root / "server" / "api").rglob("*.[tj]s")) if (root / "server" / "api").is_dir() else []
    if api:
        eps = []
        for f in api[:40]:
            parts = list(f.relative_to(root / "server" / "api").with_suffix("").parts)
            method = ""
            m = re.match(r"^(.*)\.(get|post|put|patch|delete)$", parts[-1])
            if m:
                parts[-1], method = m.group(1), m.group(2).upper() + " "
            if parts[-1] == "index":
                parts = parts[:-1]
            eps.append(f"{method}/api/{'/'.join(parts)}")
        lines.append(f"`server/api` answers {len(api)} route{'s' if len(api) > 1 else ''} in the same dev server ({', '.join(f'`{e}`' for e in eps[:4])}{', …' if len(eps) > 4 else ''}): start `nuxt dev`, nothing to mock")
    if "@nuxt/content" in deps:
        cols = []
        for p in src_files:
            if p.suffix == ".vue":
                cols += re.findall(r"queryCollection(?:Navigation|SearchSections)?\(\s*['\"](\w+)['\"]", read(p, 100_000))
        cols = list(dict.fromkeys(cols))
        lines.append("`content/` is compiled by @nuxt/content when the dev server starts; pages read it with `queryCollection`"
                     + (f" ({', '.join(f'`{c}`' for c in cols[:6])})" if cols else "") + " — server-rendered, nothing to mock")
    return lines


def _vue_wrapper(root: Path, page: Path, text: str, comps: dict[str, Path]) -> dict | None:
    """The component a .vue page is wrapped in, or hands everything to."""
    tmpl = vue_template(text)
    m = re.search(r"<([A-Z][A-Za-z0-9]*|[a-z][a-z0-9]*-[a-z0-9-]+)\b", tmpl)
    if not m or not re.match(r"^\s*(?:<!--.*?-->\s*)*<", tmpl, re.S) or tmpl.strip().find("<" + m.group(1)) != 0:
        return None
    name = _pascal(m.group(1))
    if name in VUE_BUILTINS:
        return None
    im = re.search(r"import\s+" + re.escape(name) + r"\s+from\s*['\"]([^'\"]+)['\"]", text)
    target = _resolve_import(root, page, im.group(1)) if im else comps.get(name)
    if not target or target.suffix != ".vue" or target == page:
        return None
    target = Path(os.path.normpath(target))
    t = read(target, 200_000)
    wrapper = "<slot" in vue_template(t)
    return {"name": name, "file": rel(root, target), "lines": t.count("\n") + 1, "signals": _signals(t), "wrapper": wrapper}


# ------------------------------------------------------------- SvelteKit / Astro
def _script_blocks(text: str) -> str:
    """The code of a component: a .svelte file's <script> blocks, or an .astro file's frontmatter."""
    fm = re.match(r"\s*---\n(.*?)\n---", text, re.S)
    return (fm.group(1) + "\n" if fm else "") + "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", text, re.S))


def _markup(text: str) -> str:
    """The markup of a .svelte or .astro file: no frontmatter, no scripts, no styles."""
    t = re.sub(r"^\s*---\n.*?\n---", "", text, count=1, flags=re.S)
    return re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", t, flags=re.S)


def component_tags(markup: str) -> list[str]:
    """The components a Svelte or Astro template uses: capitalised tags, in order of first use."""
    return list(dict.fromkeys(re.findall(r"<([A-Z]\w*(?:\.[A-Z]\w*)?)[\s/>]", markup)))


def _destructured(block: str) -> list[str]:
    """Names bound by a destructuring pattern's body: `a, b = 1, class: cls, ...rest` → a, b, class, rest."""
    names, depth, cur = [], 0, ""
    for ch in block + ",":
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            m = re.match(r"\s*(?:\.\.\.)?\s*([\w$]+)", cur)
            if m:
                names.append(m.group(1))
            cur = ""
        else:
            cur += ch
    return names


def _route_from(parts: list[str]) -> str:
    """A route from folder names, route groups `(name)` dropped: ["(app)", "blog", "[slug]"] → /blog/[slug]."""
    return "/" + "/".join(x for x in parts if not (x.startswith("(") and x.endswith(")")))


def sveltekit_routes(root: Path) -> list[tuple[str, str]]:
    d = root / "src" / "routes"
    if not d.is_dir():
        return []
    return [(_route_from(list(f.relative_to(d).parent.parts)), rel(root, f))
            for f in sorted(d.rglob("+page.svelte")) if not set(f.parts) & SKIP_DIRS]


def sveltekit_page_data(page: Path) -> list[str]:
    """What the files beside a +page.svelte do: load its data (on the server, or anywhere), handle form actions, render options."""
    out = []
    for stem, where in (("+page.server", "on the server"), ("+page", "on the server, then in the browser after a navigation")):
        for ext in (".ts", ".js"):
            f = page.parent / f"{stem}{ext}"
            if not f.is_file():
                continue
            t = read(f, 100_000)
            if re.search(r"export\s+(?:const|async\s+function|function)\s+load\b", t):
                out.append(f"loads data {where} (`{f.name}`)")
            if re.search(r"export\s+const\s+actions\b", t):
                out.append("form actions")
            out += [f"{opt} {v}" for opt, v in re.findall(r"export\s+const\s+(prerender|ssr|csr)\s*=\s*(\w+)", t)]
    return out


def _chrome_of(root: Path, text: str) -> dict:
    """What a layout wraps each page in: its components, providers, stylesheets and font packages."""
    code, tags = _script_blocks(text), component_tags(_markup(text))
    return {
        "css": [x for x in re.findall(r"""import\s+['"]([^'"]+\.(?:css|scss|pcss))['"]""", code)][:4],
        "fonts": [x for x in re.findall(r"""import\s+['"](@fontsource[^'"]*)['"]""", code)][:3],
        "providers": [t for t in tags if re.search(r"Provider$|^ModeWatcher$|^Toaster$|^ViewTransitions$|^ClientRouter$", t)],
        "chrome": [t for t in tags if not re.search(r"Provider$|^ModeWatcher$|^Toaster$|^ViewTransitions$|^ClientRouter$", t)][:8],
    }


def sveltekit_layouts(root: Path) -> list[dict]:
    d = root / "src" / "routes"
    if not d.is_dir():
        return []
    pages = [f for f in d.rglob("+page.svelte") if not set(f.parts) & SKIP_DIRS]
    out = []
    for f in sorted((f for f in d.rglob("+layout*.svelte") if not set(f.parts) & SKIP_DIRS),
                    key=lambda x: (len(x.relative_to(d).parts), str(x))):
        parts = list(f.relative_to(d).parent.parts)
        under = [p for p in pages if f.parent in p.parents or p.parent == f.parent]
        group = next((x for x in reversed(parts) if x.startswith("(") and x.endswith(")")), None)
        if not parts:
            scope = "wraps every page"
        elif group and _route_from(parts) == "/":
            scope = f"wraps the pages in `{group}` ({len(under)}: {', '.join(rel(d, p.parent) for p in under[:3])})"
        else:
            scope = f"wraps `{_route_from(parts)}` and the pages below it ({len(under)})"
        if "@" in f.stem:
            scope += "; `@` resets it to an outer layout"
        loads = [x.name for x in (f.parent / "+layout.server.ts", f.parent / "+layout.server.js", f.parent / "+layout.ts", f.parent / "+layout.js") if x.is_file()]
        lay = {"file": rel(root, f), "scope": rel(root, f.parent), "scopeText": scope, **_chrome_of(root, read(f, 200_000))}
        if loads:
            lay["data"] = f"loads data for every page below (`{loads[0]}`)"
        out.append(lay)
    return out


AUTH_HINTS = {"@auth/sveltekit": "Auth.js", "lucia": "Lucia", "@supabase/ssr": "Supabase", "@clerk/astro": "Clerk",
              "clerk-sveltekit": "Clerk", "better-auth": "Better Auth", "@kinde-oss": "Kinde"}


def _guard_line(root: Path, f: Path, t: str) -> str:
    """A server hook or middleware: the auth it uses, the paths it guards, whether it redirects."""
    bits = [lbl for key, lbl in AUTH_HINTS.items() if key in t]
    guarded = list(dict.fromkeys(re.findall(r"pathname\.startsWith\(\s*['\"](/[^'\"]*)", t)))
    if re.search(r"\bredirect\(", t):
        bits.append((f"guards {', '.join(f'`{g}`' for g in guarded[:4])} and " if guarded else "")
                    + "can redirect: a render there needs a session (`--cookie` / `--storage-state`)")
    return f"`{rel(root, f)}` runs before every request" + (": " + "; ".join(bits) if bits else "")


def sveltekit_before(root: Path, deps: dict) -> list[str]:
    out = []
    for stem in ("hooks.server", "hooks"):
        for ext in (".ts", ".js"):
            f = root / "src" / f"{stem}{ext}"
            if not f.is_file():
                continue
            t = read(f, 100_000)
            out.append(_guard_line(root, f, t))
    d = root / "src" / "routes"
    eps = [_route_from(list(f.relative_to(d).parent.parts)) for f in sorted(d.rglob("+server.*")) if not set(f.parts) & SKIP_DIRS] if d.is_dir() else []
    if eps:
        out.append(f"endpoints (`+server.ts`): " + ", ".join(f"`{e}`" for e in eps[:6]) + " — the dev server answers them: start it, don't mock them")
    errs = [rel(root, f) for f in sorted(d.rglob("+error.svelte"))] if d.is_dir() else []
    if errs:
        out.append("error pages: " + ", ".join(f"`{e}`" for e in errs[:3]))
    return out


def astro_routes(root: Path) -> list[tuple[str, str]]:
    d = root / "src" / "pages"
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.rglob("*")):
        if not f.is_file() or set(f.parts) & SKIP_DIRS or any(x.startswith("_") for x in f.relative_to(d).parts):
            continue
        parts = list(f.relative_to(d).with_suffix("").parts)
        if f.suffix in {".astro", ".md", ".mdx", ".html"}:
            if parts[-1] == "index":
                parts = parts[:-1]
            out.append(("/" + "/".join(parts), rel(root, f)))
        elif f.suffix in {".ts", ".js"}:                       # an endpoint: rss.xml.js → /rss.xml
            out.append(("/" + "/".join(parts) + " (endpoint)", rel(root, f)))
    return out


def _astro_wrapper(root: Path, page: Path, text: str) -> dict | None:
    """The layout a page sits in: the outermost component it imports from a layouts folder, or a Markdown page's `layout:`."""
    target, name = None, None
    if page.suffix in {".md", ".mdx"}:
        m = re.search(r"^layout:\s*['\"]?([^'\"\n]+)", text, re.M)
        if m:
            target = Path(os.path.normpath(page.parent / m.group(1).strip()))
            name = target.stem
    else:
        code, tags = _script_blocks(text), component_tags(_markup(text))
        for tag in tags[:1]:
            m = re.search(r"import\s+" + re.escape(tag) + r"\s+from\s+['\"]([^'\"]+)['\"]", code)
            if m and re.search(r"layouts?/", m.group(1)):
                target, name = _resolve_import(root, page, m.group(1)), tag
    if not target or not target.is_file():
        return None
    return {"name": name, "file": rel(root, target), "lines": read(target, 200_000).count("\n") + 1, "signals": [], "wrapper": True}


def astro_layouts(root: Path, src_files: list[Path]) -> list[dict]:
    pages = [f for f in src_files if (root / "src" / "pages") in f.parents and f.suffix in {".astro", ".md", ".mdx"}]
    users: dict[str, list[str]] = collections.defaultdict(list)
    for pg in pages:
        w = _astro_wrapper(root, pg, read(pg, 200_000))
        if w:
            users[w["file"]].append(pg.name)
    out = []
    for f in sorted({*users, *(rel(root, p) for p in src_files if p.suffix == ".astro" and "layouts" in [x.lower() for x in p.parts])}):
        us = users.get(f, [])
        scope = f"wraps the pages that use it ({len(us)}: {', '.join(us[:4])})" if us else "used by no page directly"
        out.append({"file": f, "scope": f, "scopeText": scope, **_chrome_of(root, read(root / f, 200_000))})
    return out


def astro_integrations(root: Path) -> list[str]:
    for cfg in root.glob("astro.config.*"):
        t = read(cfg)
        m = re.search(r"integrations\s*:\s*\[", t)
        if m:
            depth, i = 0, m.end() - 1
            for i in range(m.end() - 1, len(t)):
                depth += {"[": 1, "(": 1, "{": 1, "]": -1, ")": -1, "}": -1}.get(t[i], 0)
                if depth == 0:
                    break
            body, prev = t[m.end():i], None
            while prev != body:                            # innermost call arguments first: starlight({ … }) → starlight\x00
                prev, body = body, re.sub(r"\([^()]*\)", "\x00", body)
            return list(dict.fromkeys(re.findall(r"(?<![\w.])([a-z]\w*)\s*\x00", body)))[:8]
    return []


def starlight_pages(root: Path) -> list[tuple[str, str, str]]:
    """Starlight renders every file in src/content/docs as a page: (route, file, template)."""
    d = root / "src" / "content" / "docs"
    out = []
    for f in sorted(d.rglob("*")) if d.is_dir() else []:
        if f.suffix not in {".md", ".mdx", ".mdoc"} or set(f.parts) & SKIP_DIRS:
            continue
        parts = list(f.relative_to(d).with_suffix("").parts)
        if parts[-1] == "index":
            parts = parts[:-1]
        m = re.search(r"^template:\s*(\w+)", read(f, 20_000), re.M)
        out.append(("/" + "/".join(parts), rel(root, f), m.group(1) if m else "doc"))
    return out


def astro_before(root: Path, deps: dict) -> list[str]:
    out = []
    for ext in (".ts", ".js"):
        f = root / "src" / f"middleware{ext}"
        if f.is_file():
            out.append(_guard_line(root, f, read(f, 100_000)))
    if "@astrojs/starlight" in deps:
        sp = starlight_pages(root)
        splash = [f for _, f, t in sp if t == "splash"]
        out.append(f"Starlight renders each of the {len(sp)} files in `src/content/docs/` as a page (listed above)"
                   + (f"; `{splash[0]}` uses the splash template" if splash else "")
                   + " — its layout, sidebar (`astro.config.*`), search and theme come from the integration: a new page is a new file there, styled by its Markdown and Starlight's components")
    for cfg in (root / "src" / "content.config.ts", root / "src" / "content.config.js", root / "src" / "content" / "config.ts", root / "src" / "content" / "config.js"):
        if cfg.is_file():
            t = read(cfg, 100_000)
            m = re.search(r"collections\s*=\s*\{", t)
            names = _destructured(block_after(t, m.end() - 1)) if m else []
            loaders = dict(re.findall(r"(\w+)\s*=\s*defineCollection\(\{[^}]*?base\s*:\s*['\"]([^'\"]+)", t, re.S))
            coll = ", ".join(f"`{n}`" + (f" from `{loaders[n]}`" if n in loaders else "") for n in dict.fromkeys(names))
            out.append(f"content collections in `{rel(root, cfg)}`: {coll or '?'} — pages read them with `getCollection`; new entries are files, no data to mock")
            break
    return out


def page_signatures(root: Path, src_files: list[Path], vocab_names: list[str], framework: str | None = None) -> dict:
    pages, routes = [], []
    is_next, is_nuxt = framework == "Next.js", framework == "Nuxt"
    is_kit, is_astro = framework == "SvelteKit", framework == "Astro"
    file_routes = sveltekit_routes(root) if is_kit else astro_routes(root) if is_astro else []
    if is_astro and "starlight" in astro_integrations(root):
        file_routes += [(r, f) for r, f, _ in starlight_pages(root)]
    # Next.js: app/ (page files only) and pages/; Nuxt: pages/ only (app/ is its source folder);
    # everything else: the usual page folders.
    page_dirs = {"pages", "app"} if is_next else {"pages"} if is_nuxt else PAGE_DIR_NAMES - {"app"}
    comps = nuxt_components(root) if is_nuxt else {}
    # SvelteKit and Astro name their pages by convention: take them from the route readers.
    candidates = [root / f for r, f in file_routes if not r.endswith("(endpoint)")] if (is_kit or is_astro) else src_files
    for p in candidates:
        if p.suffix not in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".md", ".mdx"}:
            continue
        rp = p.relative_to(root)
        dirs = [x.lower() for x in rp.parts[:-1]]
        if not (is_kit or is_astro):
            if not (set(dirs) & page_dirs) or re.search(r"\.(test|spec|stories)$", p.stem) or p.suffix == ".md":
                continue
            if is_next and "app" in dirs and p.stem != "page":          # Next.js App Router: page files only
                continue
            if p.stem in {"layout", "template", "loading", "error", "not-found", "index"} and "app" not in dirs and p.stem != "index":
                continue
        text = read(p, 200_000)
        signals = _signals(text) + (sveltekit_page_data(p) if is_kit else [])
        rendered = (_astro_wrapper(root, p, text) if is_astro else _vue_wrapper(root, p, text, comps) if p.suffix == ".vue"
                    else None if p.suffix in {".svelte", ".md", ".mdx"} else _rendered_by(root, p, text))
        used = sorted(((n, _cls_uses(n, [text])) for n in vocab_names), key=lambda x: -x[1])
        page_comps: list[str] = []
        if p.suffix == ".vue":                   # the components its template uses, library ones included
            page_comps = [t for t in vue_tags(vue_template(text)) if t not in VUE_BUILTINS and (not rendered or t != rendered["name"])]
        elif p.suffix in {".svelte", ".astro", ".mdx"}:
            page_comps = [t for t in component_tags(_markup(text)) if not rendered or t != rendered["name"]]
        for names in re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"][^'\"]*components/[^'\"]+['\"]", text):
            page_comps += [x.strip().split(" as ")[0] for x in names.split(",") if x.strip() and not x.strip().startswith("type ")]
        pages.append({
            "file": str(rp), "lines": text.count("\n") + 1, "signals": signals,
            "classes": [f"{n} ×{c}" for n, c in used if c][:3], "components": list(dict.fromkeys(page_comps))[:6], "renders": rendered,
        })
    pages.sort(key=lambda x: x["file"])
    for p in src_files:
        if p.suffix in {".tsx", ".jsx"}:
            text = read(p, 200_000)
            if "<Route" in text:
                routes += re.findall(r"<Route\s+[^>]*?path=\{?['\"]([^'\"]+)['\"]\}?[^>]*?element=\{<(\w+)", text)
                routes += [("(index)", comp) for comp in re.findall(r"<Route\s+index\b[^>]*?element=\{<(\w+)", text)]
    if is_kit or is_astro:
        routes += file_routes
    elif is_nuxt:
        routes += nuxt_routes(root)
    elif framework == "Vue" or any(p.suffix == ".vue" for p in src_files[:200]):
        routes += vue_router_routes(root, src_files)
    app_dir = next((d for d in (root / "app", root / "src" / "app") if d.is_dir()), None) if is_next else None
    if app_dir:
        for pg in sorted(app_dir.rglob("page.*")):
            if set(pg.parts) & SKIP_DIRS:
                continue
            segs = [x for x in pg.relative_to(app_dir).parent.parts if not (x.startswith("(") and x.endswith(")"))]
            routes.append(("/" + "/".join(segs), rel(root, pg)))
    return {"pages": pages[:24], "routes": routes[:30]}


def copy_mechanism(root: Path, src_files: list[Path], deps: dict) -> dict:
    libs = [label for key, label in I18N_LIBS.items() if key in deps]
    dirs = sorted({rel(root, p.parent) for p in src_files if p.parent.name.lower() in I18N_DIRS}
                  | {rel(root, d) for d in iter_dirs(root) if d.name.lower() in I18N_DIRS})
    hook = None
    for p in src_files[:MAX_SRC_FILES]:
        m = re.search(r"\b(useI18n|useTranslation|useTranslations|useIntl|useLingui)\b", read(p, 100_000))
        if m:
            hook = m.group(1)
            break
    dictionaries, typed = [], None
    for d in dirs:
        for f in sorted((root / d).glob("*")):
            if f.is_file() and f.suffix in {".ts", ".js", ".json", ".tsx"}:
                t = read(f, 400_000)
                keys = len(re.findall(r'^\s*"[^"\n]+"\s*:', t, re.M))
                if keys:
                    dictionaries.append((rel(root, f), keys))
                code = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S))
                # The dictionary that is typed against another (en.ts: Record<TranslationKey, string>),
                # not the provider that merely maps locales to dictionaries.
                if keys and typed is None and re.search(r"Record<\s*TranslationKey|Record<\s*keyof typeof|satisfies\s+Record", code):
                    typed = rel(root, f)
    return {"libs": libs, "dirs": dirs, "hook": hook, "dictionaries": dictionaries[:6], "typed": typed}


def boot_requests(root: Path, src_files: list[Path]) -> dict:
    api_map: dict[str, str] = {}
    base, api_file = None, None
    for p in src_files:
        if p.stem.lower() in {"api", "client", "http", "request", "fetcher"} and p.suffix in {".ts", ".js", ".tsx"}:
            t = read(p, 300_000)
            m = re.search(r"fetch\(\s*`([^`$]*)\$\{", t)
            if m:
                base = m.group(1)
            for name, path in re.findall(r"(\w+)\s*:\s*\([^)]*\)\s*=>\s*\w+(?:<[^>]*>)?\(\s*[`'\"]([^`'\"]+)", t):
                api_map.setdefault(name, path)
            if api_map:
                api_file = rel(root, p)
                break
    files = []
    for p in src_files:
        if not BOOT_STEM.match(p.stem) or p.suffix not in {".ts", ".tsx", ".js", ".jsx", ".vue"}:
            continue
        t = read(p, 300_000)
        found = [api_map[m.group(1)] for m in re.finditer(r"\bapi\.(\w+)\(", t) if m.group(1) in api_map]
        found += re.findall(r"fetch\(\s*[`'\"]([^`'\"$]+)", t)
        found += re.findall(r"axios\.\w+\(\s*[`'\"]([^`'\"$]+)", t)
        if found:
            files.append({"file": rel(root, p), "requests": list(dict.fromkeys(found))[:8]})
    return {"apiModule": api_file, "base": base, "files": files[:5]}


def dev_setup(root: Path) -> dict:
    proxies = []
    for cfg in [*root.glob("vite.config.*"), *root.glob("next.config.*"), *root.glob("nuxt.config.*")]:
        t = read(cfg)
        for path, target in re.findall(r"['\"]([^'\"]+)['\"]\s*:\s*\{[^}]*?target\s*:\s*['\"]([^'\"]+)['\"]", t, re.S):
            proxies.append((path, target, rel(root, cfg)))
        for src, dest in re.findall(r"source\s*:\s*['\"]([^'\"]+)['\"][^}]*?destination\s*:\s*['\"]([^'\"]+)['\"]", t, re.S):
            proxies.append((src, dest, rel(root, cfg)))
    helpers = set()
    for base_dir in (root, root.parent):
        for pat in ("dev.sh", "dev.*", "run.sh", "start.sh", "Makefile", "justfile", "docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml", "Procfile"):
            for p in base_dir.glob(pat):
                helpers.add(os.path.relpath(p, root))
    next_cfg = {}
    for cfg in root.glob("next.config.*"):
        t = read(cfg)
        if re.search(r"trailingSlash\s*:\s*true", t):
            next_cfg["trailingSlash"] = True
        m = re.search(r"basePath\s*:\s*['\"]([^'\"]+)['\"]", t)
        if m:
            next_cfg["basePath"] = m.group(1)
    scripts = {}
    pj = root / "package.json"
    if pj.exists():
        try:
            scripts = {k: v for k, v in json.loads(read(pj)).get("scripts", {}).items() if k in {"dev", "start", "preview"} or k.startswith("dev:")}
        except (json.JSONDecodeError, AttributeError):
            pass
    return {"proxies": proxies[:6], "helpers": sorted(helpers), "scripts": scripts, "next": next_cfg}


def storage_keys(root: Path, src_files: list[Path]) -> list[str]:
    """Where the app keeps its state in the browser: the keys to seed with --init-script."""
    found: dict[str, str] = {}
    # The store's own file names the key best; an error boundary that also reads it comes later.
    ranked = sorted(src_files, key=lambda p: (0 if re.search(r"stor(e|age)|persist|db", str(p), re.I) else 1, str(p)))
    for p in ranked:
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"}:
            continue
        t = read(p, 200_000)
        if "localStorage" not in t and "sessionStorage" not in t and "indexedDB" not in t and "openDB(" not in t:
            continue
        keys = re.findall(r"(?:localStorage|sessionStorage)\.(?:getItem|setItem)\(\s*['\"`]([^'\"`$]+)['\"`]", t)
        for name, value in re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*['\"`]([\w.:/-]+)['\"`]", t):
            if re.search(r"(?:localStorage|sessionStorage)\.(?:getItem|setItem)\(\s*" + re.escape(name) + r"\b", t):
                keys.append(value)
        db = re.findall(r"(?:indexedDB\.open|openDB)\(\s*['\"`]([^'\"`]+)['\"`]", t)
        for k in keys:
            found.setdefault(f"localStorage `{k}`", rel(root, p))
        for k in db:
            found.setdefault(f"IndexedDB `{k}`", rel(root, p))
    by_file: dict[str, list[str]] = collections.defaultdict(list)
    for k, f in found.items():
        by_file[f].append(k)
    return [f"`{f}` keeps state in " + ", ".join(ks[:5]) + " — seed it with `--init-script` to render a populated page" for f, ks in list(by_file.items())[:3]]


def gates(root: Path, src_files: list[Path]) -> list[str]:
    out = []
    idx = root / "index.html"
    if idx.exists() and re.search(r"<script>(?:(?!</script>).)*?(matchMedia|localStorage|data-?theme|dataset\.theme)", read(idx), re.S):
        out.append("`index.html` decides the theme in an inline script at boot (`data-theme`); the dark pass reloads for it")
    for p in src_files:
        if SPLASH_STEM.match(p.stem) and p.suffix in {".tsx", ".jsx", ".vue", ".svelte"}:
            t = read(p, 100_000)
            key = None
            for name, value in re.findall(r"const\s+(\w+)\s*=\s*['\"]([\w.:-]+)['\"]", t):
                if re.search(r"(?:sessionStorage|localStorage)\.(?:getItem|setItem)\(\s*" + re.escape(name), t):
                    key = value
                    break
            key = key or next(iter(re.findall(r"(?:sessionStorage|localStorage)\.(?:getItem|setItem)\(\s*['\"]([^'\"]+)", t)), None)
            lifts = "any key or tap lifts it" if re.search(r"keydown|pointerdown|click", t) else "waits it out"
            out.append(f"`{rel(root, p)}` covers the first paint ({lifts}" + (f"; storage key `{key}`" if key else "") + ")")
    for p in src_files:
        if p.stem in {"App", "app", "layout", "_app", "Root", "root"} and p.suffix in {".tsx", ".jsx"}:
            conds = re.findall(r"\n[ \t]*if\s*\(([^)\n]{1,80})\)\s*\{\s*\n[ \t]*return\b", read(p, 200_000))
            if conds:
                out.append(f"`{rel(root, p)}` returns early on, in order: " + " → ".join(f"`{c.strip()}`" for c in conds[:6]))
    return out[:6]


def start_here(root: Path, src_files: list[Path], css_files: list[Path], stack: dict, deps: dict) -> dict:
    ui_files = [p for p in src_files if p.suffix in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".mdx"}]
    texts = [read(p, 200_000) for p in ui_files[:MAX_SRC_FILES]]
    vocab = css_vocabulary(root, css_files, texts)
    sig = page_signatures(root, src_files, [v["name"] for v in vocab], stack.get("framework"))
    is_next = stack.get("framework") == "Next.js"
    is_nuxt = stack.get("framework") == "Nuxt"
    is_kit, is_astro = stack.get("framework") == "SvelteKit", stack.get("framework") == "Astro"
    notes = {"Nuxt": "references/stacks/nuxt.md", "Vue": "references/stacks/vue.md", "SvelteKit": "references/stacks/sveltekit.md",
             "Svelte": "references/stacks/sveltekit.md", "Astro": "references/stacks/astro.md"}.get(stack.get("framework") or "")
    return {
        "vocabulary": vocab,
        "imported": import_fanin(root, src_files),
        **sig,
        "layouts": (next_layouts(root) if is_next else nuxt_layouts(root, src_files) if is_nuxt else sveltekit_layouts(root) if is_kit
                    else astro_layouts(root, src_files) if is_astro else []),
        "stackBefore": sveltekit_before(root, deps) if is_kit else astro_before(root, deps) if is_astro else [],
        "astro": is_astro,
        "autoImported": vue_component_uses(root, src_files, nuxt_components(root)) if is_nuxt else [],
        "nuxtui": nuxt_ui(root, src_files, deps),
        "nuxtBefore": nuxt_before(root, deps, src_files) if is_nuxt else [],
        "nuxt": is_nuxt,
        "vite": "vite" in deps and not is_next and not is_nuxt and not is_astro,
        "stackNotes": notes,
        "theme": theme_mechanism(root, css_files, stack, src_files),
        "middleware": middleware_line(root) if is_next else None,
        "locale": locale_routing(root, src_files, sig["routes"]),
        "next": is_next,
        "contentlayer": any(k in deps for k in ("contentlayer", "contentlayer2", "next-contentlayer", "next-contentlayer2")),
        "copy": copy_mechanism(root, src_files, deps),
        "boot": boot_requests(root, src_files),
        "dev": dev_setup(root),
        "gates": gates(root, src_files) + storage_keys(root, src_files),
    }


def md_start_here(sh: dict) -> list[str]:
    out = ["## Start here (a match task reads these, not the tree)"]
    if sh["vocabulary"]:
        out.append("- Vocabulary — the classes the CSS defines, by use:")
        for v in sh["vocabulary"]:
            out.append(f"  - `.{v['name']}` ×{v['uses']} — {v['file']}:{v['line']} — {v['decl']}")
    nu = sh.get("nuxtui")
    if nu:
        cols = ", ".join(f"`{k}: {v}`" for k, v in nu["colors"].items())
        out.append("- Nuxt UI" + (f" — colours {cols}" + (f" (`{nu['config']}`)" if nu["config"] else "") if cols else "")
                   + (": its components by use, " + " · ".join(f"{n} ×{c}" for n, c in nu["components"]) if nu["components"] else "")
                   + ". A match task builds with these and the colour names, not hand-rolled Tailwind.")
    if sh.get("autoImported"):
        out.append("- Used most (auto-imported: counted by the templates that use them): " + " · ".join(
            f"`{m['file']}` ({m['importers']}" + (f"; props {', '.join(m['props'])}" if m.get("props") else "") + ")" for m in sh["autoImported"]))
    if sh["imported"]:
        out.append("- Imported most: " + " · ".join(
            f"`{m['file']}` ({m['importers']}" + (f"; props {', '.join(m['props'])}" if m.get("props") else "") + ")" for m in sh["imported"]))
    if sh["pages"]:
        out.append("- Pages, one line each:")
        wrappers_named = set()  # a wrapper's path and role once; later pages say only "inside X"
        for pg in sh["pages"]:
            bits = [f"{pg['lines']} lines"]
            if pg["signals"]:
                bits.append(", ".join(pg["signals"]))
            if pg["classes"]:
                bits.append(", ".join(pg["classes"]))
            if pg["components"]:
                bits.append(("uses " if pg["file"].endswith((".vue", ".svelte", ".astro", ".md", ".mdx")) else "imports ") + ", ".join(pg["components"]))
            r = pg.get("renders")
            if r and r.get("wrapper"):
                bits.append(f"inside {r['name']}" + ("" if r["file"] in wrappers_named else f" (`{r['file']}` · {r['lines']} lines: the chrome, its slot holds the page)"))
                wrappers_named.add(r["file"])
            elif r:
                bits.append(f"renders {r['name']} (`{r['file']}` · {r['lines']} lines" + (f" · {', '.join(r['signals'])}" if r["signals"] else "") + ")")
            out.append(f"  - `{pg['file']}` · " + " · ".join(bits))
    if sh["routes"]:
        out.append("- Routes: " + " · ".join(f"`{path}` → {comp}" for path, comp in sh["routes"][:20]))
    loc = sh.get("locale")
    if loc:
        out.append(f"  - `[locale]`: {', '.join(loc['locales']) or '?'} · default `{loc['default']}`"
                   + (f" · prefix {loc['prefix']}" + (" → `/` is the default locale" if loc["prefix"] != "always" else " → every path starts with the locale") if loc["prefix"] else "")
                   + f" (`{loc['file']}`)")
    c = sh["copy"]
    if c["dictionaries"] or c["libs"] or c["hook"]:
        parts = []
        if c["dictionaries"]:
            parts.append("dictionaries " + ", ".join(f"`{f}` ({n} keys)" for f, n in c["dictionaries"]))
        if c["typed"]:
            parts.append(f"`{c['typed']}` is typed against the other — a key missing there fails the build")
        if c["libs"]:
            parts.append("library " + ", ".join(c["libs"]))
        if c["hook"]:
            parts.append(f"components call `{c['hook']}()`")
        out.append("- Strings: " + "; ".join(parts) + ". New copy goes into every dictionary.")
    before = []
    if sh.get("theme"):
        before.append("theme: " + sh["theme"])
    for i, lay in enumerate(sh.get("layouts") or []):
        parts = []
        if lay["css"]:
            parts.append("css " + ", ".join(f"`{c}`" for c in lay["css"]))
        if lay["fonts"]:
            parts.append(("next/font " if sh.get("next") else "fonts ") + ", ".join(lay["fonts"]))
        if lay["providers"]:
            parts.append("providers " + ", ".join(lay["providers"]))
        if lay.get("data"):
            parts.append(lay["data"])
        if lay["chrome"]:
            parts.append("chrome " + ", ".join(lay["chrome"]))
        scope = lay.get("scopeText") or ("wraps every page" if i == 0 else f"wraps `{lay['scope']}/*`")
        before.append(f"`{lay['file']}` {scope}" + (": " + " · ".join(parts) if parts else ""))
    if sh.get("middleware"):
        before.append(sh["middleware"])
    before += sh.get("nuxtBefore") or []
    before += sh.get("stackBefore") or []
    before += list(sh["gates"])
    b = sh["boot"]
    for f in b["files"]:
        via = f" through `{b['apiModule']}`" + (f" (base `{b['base']}`)" if b["base"] else "") if b["apiModule"] else ""
        before.append(f"`{f['file']}` calls " + ", ".join(f"`{r}`" for r in f["requests"]) + via + " — mock what the page needs, or start the backend")
    d = sh["dev"]
    for path, target, cfg in d["proxies"]:
        before.append(f"`{cfg}` proxies `{path}` → `{target}`")
    if d["helpers"]:
        before.append("starts everything: " + ", ".join(f"`{h}`" for h in d["helpers"]))
    if d["scripts"]:
        line = "scripts: " + ", ".join(f"`{k}` = `{v}`" for k, v in list(d["scripts"].items())[:3])
        if sh.get("next"):
            dev = d["scripts"].get("dev", "")
            line += " — Next.js listens on :3000 unless `-p` says otherwise"
            if d.get("next", {}).get("trailingSlash"):
                line += "; routes end with `/` (`trailingSlash`), a request without it is redirected"
            if d.get("next", {}).get("basePath"):
                line += f"; every route sits under `{d['next']['basePath']}` (`basePath`)"
            if re.search(r"run-p|concurrently|npm-run-all|&&|\s&\s", dev):
                line += "; `dev` starts more than Next (a database, a worker): run it as it is"
            if sh.get("contentlayer"):
                line += "; contentlayer compiles the content on start"
        elif sh.get("nuxt"):
            line += " — `nuxt dev` listens on :3000 unless `--port` says otherwise"
        elif sh.get("astro"):
            line += " — `astro dev` listens on :4321 unless `--port` says otherwise"
        elif sh.get("vite"):
            line += " — Vite listens on :5173 unless `--port` or `server.port` says otherwise"
        before.append(line)
    if before:
        out.append("- Before a page renders:")
        out += [f"  - {ln}" for ln in before]
    if sh.get("stackNotes"):
        out.append(f"- Stack notes: `{sh['stackNotes']}` in the skill folder — how this stack serves a page, switches theme and names its components")
    if sh["pages"] or sh["vocabulary"]:
        thin = any(pg.get("renders") and not pg["renders"].get("wrapper") for pg in sh["pages"])
        out.append("- Read next: " + (("the page above whose signals match yours" + (" (a thin page: the file it renders)" if thin else "") if sh["pages"] else "the vocabulary lines")
                   + (" and the vocabulary lines" if sh["pages"] and sh["vocabulary"] else ""))
                   + ". Not the CSS file, not the store.")
    else:
        out.append("- Nothing to read first: no pages or component classes yet — see the verdict below.")
    out.append("")
    return out


# ------------------------------------------------------------------ rendering
def md(data: dict) -> str:
    s, t, f, c, u, v = data["stack"], data["tokens"], data["fonts"], data["components"], data["usage"], data["verdict"]
    out = [f"# ui-craft inspect — {data['root']}", ""]

    # Stack
    bits = []
    if s["framework"]:
        bits.append(s["framework"] + (f" ({s['router']})" if s["router"] else ""))
    if s["framework"] in ("Nuxt", "Vue", "SvelteKit", "Svelte", "Astro", "Angular") and s.get("frameworkVersion"):
        bits[-1] = bits[-1].replace(s["framework"], f"{s['framework']} {s['frameworkVersion']}", 1)
    if s["react"]:
        bits.append(f"React {s['react']}")
    if s.get("vue") and s["framework"] != "Vue":
        bits.append(f"Vue {s['vue']}")
    if s.get("svelte") and s["framework"] != "Svelte":
        bits.append(f"Svelte {s['svelte']}")
    if s.get("integrations"):
        bits.append("integrations " + ", ".join(s["integrations"]))
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
    if data.get("startHere"):
        out += md_start_here(data["startHere"])

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
        "startHere": start_here(root, src_files, css_files, stack, stack.get("deps") or {}) if not stack.get("workspaceApps") else None,
    }
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(md(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
