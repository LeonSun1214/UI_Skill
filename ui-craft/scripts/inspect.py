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
    "@angular/material": "Angular Material", "primeng": "PrimeNG", "ng-zorro-antd": "NG-ZORRO", "@taiga-ui/core": "Taiga UI",
    "@nebular/theme": "Nebular", "@clr/angular": "Clarity", "@ng-bootstrap/ng-bootstrap": "ng-bootstrap",
    "ngx-bootstrap": "ngx-bootstrap", "@ionic/angular": "Ionic", "@spartan-ng/brain": "spartan/ui",
}
KNOWN_ICONS = {
    "lucide-react": "Lucide", "@heroicons/react": "Heroicons", "@phosphor-icons/react": "Phosphor",
    "react-icons": "react-icons", "@tabler/icons-react": "Tabler", "@radix-ui/react-icons": "Radix Icons",
    "@iconify/react": "Iconify",
    "lucide-vue-next": "Lucide", "@iconify/vue": "Iconify", "@heroicons/vue": "Heroicons", "@phosphor-icons/vue": "Phosphor",
    "lucide-angular": "Lucide", "@ng-icons/core": "ng-icons", "@fortawesome/angular-fontawesome": "Font Awesome",
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
    next_font, google, face, icon_fonts = set(), set(), set(), set()
    for p in src_files[:MAX_SRC_FILES]:
        text = read(p, 120_000)
        if "next/font" in text:
            for names in re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/(?:google|local)['\"]", text):
                next_font.update(n.strip().split(" as ")[0] for n in names.split(",") if n.strip())
        for q in re.findall(r"fonts\.googleapis\.com/css2?\?([^\"'\s>]+)", text):
            for fam in re.findall(r"family=([^&]+)", q):
                google.update(f.split(":")[0].replace("+", " ") for f in fam.split("|") if f)
        icon_fonts.update(f.replace("+", " ") for f in re.findall(r"fonts\.googleapis\.com/icon\?family=([\w+]+)", text))
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
    icon_fonts |= {g for g in google if re.match(r"Material (Icons|Symbols)", g)}
    google -= icon_fonts
    return {"nextFont": sorted(next_font), "googleLinks": sorted(google), "fontFace": sorted(face), "tokenFonts": token_fonts[:12],
            "iconFonts": sorted(icon_fonts)}


# ---------------------------------------------------------------- components
COMPONENT_DIR_NAMES = {"components", "ui", "primitives", "design-system", "elements", "shared"}


def component_inventory(root: Path, src_files: list[Path]) -> dict:
    primitives, composed = [], []
    for p in src_files:
        if p.suffix not in {".tsx", ".jsx", ".vue", ".svelte", ".ts"}:
            continue
        stem = p.stem
        if p.suffix == ".ts":                            # an Angular component: a class under @Component
            if re.search(r"\.(spec|test|stories)$", stem) or not (set(x.lower() for x in p.parts) & COMPONENT_DIR_NAMES) \
                    or "@Component" not in read(p, 100_000):
                continue
            stem = re.sub(r"\.component$", "", stem)
        if stem.lower() in {"index", "page", "layout", "loading", "error", "not-found", "route", "template"} and p.suffix != ".ts":
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
def verdict(stack: dict, tokens: dict, fonts: dict, comps: dict, usage: dict, docs: list[str], sh: dict | None = None) -> dict:
    tokens_declared = bool(tokens["theme"] or tokens["root"] or tokens["configExtend"])
    ng = (sh or {}).get("ng")
    mt = (sh or {}).get("material")
    established = (
        usage["rawTotal"] + usage["semanticTotal"] >= 25
        or len(comps["primitives"]) + len(comps["composed"]) >= 4
        or tokens_declared
        or bool(ng and (ng["components"] >= 4 or (mt and (mt["file"] or mt["prebuilt"]))))
    )
    lines = []
    if mt and (mt["file"] or mt["prebuilt"]):
        cols = ", ".join(f"{k} {v}" for k, v in list(mt["colors"].items())[:2])
        lines.append(f"UI kit: **Angular Material** ({mt['kind'] or 'prebuilt'} theme" + (f", {cols}" if cols else "") + ") — build with its components, not hand-rolled ones")
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
    lines.append("Dark mode: " + ("present" if usage["dark"] or tokens["darkBlock"] or (ng and (sh or {}).get("theme")) else "not used"))
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


def css_vocabulary(root: Path, css_files: list[Path], src_texts: list[str], skip: str | None = None) -> list[dict]:
    """Single-class rules (`.card {`, `.btn-primary {`) with their first declarations, by use."""
    vocab: dict[str, dict] = {}
    for p in css_files:
        text = read(p)
        for m in re.finditer(r"(?m)^[ \t]*\.([a-zA-Z][\w-]*)\s*\{", text):
            name = m.group(1)
            if name in vocab or name in {"dark", "light"} or (skip and re.match(skip, name)):  # a theme selector, or a kit's own class
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
        if p.suffix not in {".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro"} or re.search(r"\.(spec|test|stories)\.\w+$", p.name):
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
    n_fields += len(re.findall(r"<(?:mat-(?:select|checkbox|slide-toggle|radio-group|slider|chip-grid)|p-(?:select|dropdown|inputnumber|checkbox|calendar|datepicker|multiselect|autocomplete|toggleswitch)|nz-(?:select|input-number|date-picker|checkbox|switch|radio-group))(?![\w-])", text))
    if n_fields:
        signals.append(f"{n_fields} field{'s' if n_fields > 1 else ''}")
    if re.search(r"<(?:table|UTable|u-table|el-table|ElTable|VDataTable|v-data-table|mat-table|p-table|nz-table)\b", text):
        signals.append("table")
    elif (".map(" in text and re.search(r"<(?:li|article|tr)\b", text)) or "v-for=" in text or "{#each" in text or "@for (" in text or "*ngFor=" in text:
        signals.append("list")
    if re.search(r'role="dialog"|<dialog\b|<Dialog\b|<(?:UModal|USlideover|u-modal|el-dialog|ElDialog|VDialog|v-dialog|p-dialog|nz-modal)\b', text):
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
    ng_setter = None
    if how is None and stack.get("framework") == "Angular":
        found = angular_dark(root, css_files)
        if found:
            cls, where_ = found
            ng_setter = angular_dark_setter(root, src_files, cls)
            on = "`<html>`" if ng_setter and re.search(r"documentElement|htmlElement|\bhtml\b", read(root / ng_setter.split("`")[1], 200_000)) else "an ancestor"
            scheme = any(re.search(r"\." + re.escape(cls) + r"\b[^{]*\{[^}]*color-scheme\s*:\s*dark", read(c)) for c in css_files)
            how = f"`.{cls}` on {on}" + (" (`color-scheme: dark`: Material's `light-dark()` colours follow it)" if scheme and "@angular/material" in deps else "")
            where, plain = f"`{where_}`", True
    if how is None and "@astrojs/starlight" in deps:
        how, where, plain = "`[data-theme=dark]` on `<html>`", "Starlight's own CSS (`--sl-color-*` properties)", True
    if how is None:                                  # plain CSS: dark rules keyed on an attribute, a class, or the OS scheme
        for c in css_files:
            t = read(c)
            for pat, label in ((r"\[data-theme=['\"]?dark", "`[data-theme=dark]` on `<html>`"),
                               (r"(?:^|[\s,}])(?::root|html)?\.dark(?![\w-])", "`.dark` on `<html>`"),
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
    setter = ng_setter
    if setter:
        pass
    elif "mode-watcher" in deps:
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
    if setter is None and stack.get("framework") == "Angular":   # a theme service: classList.add('dark')
        cm = re.search(r"`\.([\w-]+)`", how)
        setter = angular_dark_setter(root, src_files, cm.group(1)) if cm else None
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


# -------------------------------------------------------------------- Angular
# An Angular page is a component a route names; its markup is a template file or an inline
# `template:`, its children are elements named by their selectors, and what stands before it is
# a guard in the route table, not a file beside it. The readers below follow the route table
# from provideRouter / RouterModule.forRoot through lazy children to the component files.
NG_STRUCTURAL = {"router-outlet", "ng-container", "ng-template", "ng-content"}
NG_LAZY = re.compile(r"import\(\s*['\"]([^'\"]+)['\"]\s*\)(?:\s*\.then\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*\2\.(\w+)\s*\))?")
NG_THEME_CLASS = re.compile(r"^(?:dark|dark[-_](?:theme|mode|scheme)|(?:theme|mode|scheme|is)[-_]dark)$", re.I)
NG_PREFIXED_THEME = re.compile(r"^[\w-]+[-_](?:theme|mode|scheme|app)[-_]dark$|^app[-_]dark$", re.I)   # a theme root only when its rule sets variables


def _no_comments(t: str) -> str:
    """TypeScript or JSON without comments; a `//` after a colon or a quote (a URL in a string) is kept."""
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"(?<![:\w'\"`\\])//[^\n]*", "", t)


def _balanced(t: str, i: int) -> str:
    """The text inside the bracket that opens at t[i], with strings respected."""
    depth, quote, j = 0, None, i
    while j < len(t):
        ch = t[j]
        if quote:
            if ch == "\\":
                j += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
            if depth == 0:
                return t[i + 1:j]
        j += 1
    return t[i + 1:]


def _split_top(s: str) -> list[str]:
    """Split at the commas that are not inside brackets or strings."""
    out, cur, depth, quote, i = [], [], 0, None, 0
    while i < len(s):
        ch = s[i]
        cur.append(ch)
        if quote:
            if ch == "\\" and i + 1 < len(s):
                cur.append(s[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            cur.pop()
            out.append("".join(cur))
            cur = []
        i += 1
    out.append("".join(cur))
    return [x.strip() for x in out if x.strip()]


def _fields(body: str) -> dict[str, str]:
    """The properties of an object literal's body: { path: 'x', children: [...] } → {path: "'x'", children: "[...]"}."""
    out = {}
    for part in _split_top(body):
        m = re.match(r"['\"]?([\w$]+)['\"]?\s*:\s*(.*)$", part, re.S)
        if m:
            out[m.group(1)] = m.group(2).strip()
        elif re.match(r"^[\w$]+$", part):
            out[part] = part
    return out


def _unquote(v: str | None) -> str | None:
    m = re.match(r"^\s*(['\"`])(.*)\1\s*$", v or "", re.S)
    return m.group(2) if m else None


def angular_workspace(root: Path) -> dict | None:
    """The application in angular.json: where its source is, its global stylesheets, how `ng serve` serves it."""
    f = root / "angular.json"
    if not f.is_file():
        return None
    try:
        d = json.loads(read(f))
    except json.JSONDecodeError:
        return None
    projects = d.get("projects") or {}
    apps = [k for k, v in projects.items() if isinstance(v, dict) and v.get("projectType") == "application"]
    name = d.get("defaultProject") if d.get("defaultProject") in projects else (apps[0] if apps else next(iter(projects), None))
    p = projects.get(name) or {}
    arch = p.get("architect") or p.get("targets") or {}
    build, serve = arch.get("build") or {}, arch.get("serve") or {}
    opts, sopts = build.get("options") or {}, serve.get("options") or {}
    bdev = (build.get("configurations") or {}).get("development") or {}
    sdev = (serve.get("configurations") or {}).get("development") or {}
    styles = [s if isinstance(s, str) else (s or {}).get("input") for s in opts.get("styles") or []]
    return {
        "name": name, "apps": apps, "src": p.get("sourceRoot") or os.path.join(p.get("root") or "", "src"),
        "styles": [s for s in styles if s], "port": sopts.get("port") or sdev.get("port"),
        "proxy": sopts.get("proxyConfig") or sdev.get("proxyConfig"), "ssr": bool(opts.get("ssr") or opts.get("server")),
        "env": [(r.get("replace"), r.get("with")) for r in bdev.get("fileReplacements") or [] if isinstance(r, dict)],
    }


def ts_aliases(root: Path) -> list[tuple[str, list[Path]]]:
    """compilerOptions.paths: `@core` → src/app/core, `@env/*` → src/environments/*."""
    for name in ("tsconfig.json", "tsconfig.base.json", "tsconfig.app.json"):
        f = root / name
        if not f.is_file():
            continue
        try:
            co = json.loads(re.sub(r",(\s*[}\]])", r"\1", _no_comments(read(f)))).get("compilerOptions") or {}
        except (json.JSONDecodeError, AttributeError):
            continue
        if co.get("paths"):
            base = root / (co.get("baseUrl") or ".")
            return [(k, [base / v for v in vs]) for k, vs in co["paths"].items() if isinstance(vs, list)]
    return []


def _ng_resolve(root: Path, from_file: Path, spec: str, aliases: list) -> Path | None:
    """The file an import specifier names: relative, a tsconfig alias, or a path from the base URL."""
    if spec.startswith("."):
        bases = [from_file.parent / spec]
    else:
        bases = []
        for pat, targets in aliases:
            if pat.endswith("/*") and spec.startswith(pat[:-1]):
                bases += [Path(str(t)[:-1] + spec[len(pat) - 1:]) if str(t).endswith("*") else t for t in targets]
            elif pat == spec:
                bases += targets
        bases = bases or [root / spec, root / "src" / spec]
    for b in bases:
        for ext in ("", ".ts", "/index.ts", ".js", "/index.js"):
            c = Path(str(b) + ext)
            if c.is_file():
                return Path(os.path.normpath(c))
    return None


def _ng_defines(root: Path, f: Path, name: str, aliases: list, depth: int = 0) -> Path | None:
    """The file that declares `name`, through a barrel's `export * from` and `export { name } from`."""
    t = read(f, 300_000)
    if re.search(r"export\s+(?:default\s+)?(?:abstract\s+)?(?:const|let|var|function|class|interface|type|enum)\s+" + re.escape(name) + r"\b", t) \
            or re.search(r"(?:const|let|var|function|class)\s+" + re.escape(name) + r"\b[\s\S]*export\s*\{[^}]*\b" + re.escape(name) + r"\b", t):
        return f
    if depth >= 4:
        return None
    if re.search(r"export\s*\{[^}]*\b" + re.escape(name) + r"\b[^}]*\}(?!\s*from)", t):     # export { X } of an imported X
        for names, spec in re.findall(r"import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", t):
            if re.search(r"(?:^|[\s,])" + re.escape(name) + r"\s*(?:,|$)", names):
                g = _ng_resolve(root, f, spec, aliases)
                return _ng_defines(root, g, name, aliases, depth + 1) if g else None
    for names, spec in re.findall(r"export\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", t):
        for part in names.split(","):
            bits = [x.strip() for x in part.split(" as ")]
            if bits[-1] == name:
                g = _ng_resolve(root, f, spec, aliases)
                return _ng_defines(root, g, bits[0], aliases, depth + 1) if g else None
    for spec in re.findall(r"export\s*\*\s*from\s*['\"]([^'\"]+)['\"]", t):
        g = _ng_resolve(root, f, spec, aliases)
        hit = _ng_defines(root, g, name, aliases, depth + 1) if g else None
        if hit:
            return hit
    return None


def _ng_source_of(root: Path, f: Path, t: str, name: str, aliases: list) -> Path | None:
    """Where an identifier used in file f is declared: an import, followed through barrels, or the file itself."""
    for names, spec in re.findall(r"import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", t):
        for part in names.split(","):
            bits = [x.strip() for x in part.split(" as ")]
            if bits[-1] == name:
                g = _ng_resolve(root, f, spec, aliases)
                return (_ng_defines(root, g, bits[0], aliases) or g) if g else None
    m = re.search(r"import\s+" + re.escape(name) + r"\s+from\s*['\"]([^'\"]+)['\"]", t)
    if m:
        return _ng_resolve(root, f, m.group(1), aliases)
    if re.search(r"(?:const|let|var|function|class)\s+" + re.escape(name) + r"\b", t):
        return f
    return None


def _ng_inline(meta: str, key: str) -> str | None:
    """An inline `template:` or `styles:` string of a decorator."""
    m = re.search(r"\b" + key + r"\s*:\s*\[?\s*(['\"`])", meta)
    if not m:
        return None
    q, i, j = m.group(1), m.end(), m.end()
    while j < len(meta):
        if meta[j] == "\\":
            j += 2
            continue
        if meta[j] == q:
            return meta[i:j]
        j += 1
    return meta[i:]


def _ng_io(body: str, meta: str) -> tuple[list[str], list[str]]:
    """Inputs and outputs of a component class: decorators, signal functions, and `inputs:` metadata."""
    ins: list[str] = []
    for m in re.finditer(r"@Input\(\s*(\{[^)]*\}|['\"]\w+['\"])?\s*\)\s*(?:(?:public|protected|private|readonly|override|declare)\s+)*(?:set\s+)?(\w+)", body):
        arg = m.group(1) or ""
        alias = re.search(r"(?:alias\s*:\s*)?['\"](\w+)['\"]", arg)
        ins.append((alias.group(1) if alias else m.group(2)) + (" (required)" if re.search(r"required\s*:\s*true", arg) else ""))
    for m in re.finditer(r"(?:^|[\s;{])(?:(?:public|protected|private|readonly|override)\s+)*(\w+)\s*=\s*(input|model)(\.required)?\s*(?:<[^;=]*?>)?\s*\(", body):
        ins.append(m.group(1) + (" (required)" if m.group(3) else "") + (" (two-way)" if m.group(2) == "model" else ""))
    im = re.search(r"\binputs\s*:\s*\[([^\]]*)\]", meta)
    if im:
        ins += [x.split(":")[0].strip() for x in re.findall(r"['\"]([^'\"]+)['\"]", im.group(1))]
    outs = [m.group(1) or m.group(2) for m in re.finditer(r"@Output\(\s*(?:['\"](\w+)['\"])?\s*\)\s*(?:(?:public|protected|private|readonly|override)\s+)*(\w+)", body)]
    outs += [m.group(1) for m in re.finditer(r"(?:^|[\s;{])(?:(?:public|protected|private|readonly|override)\s+)*(\w+)\s*=\s*(?:output|outputFromObservable)\s*(?:<[^;=]*?>)?\s*\(", body)]
    return list(dict.fromkeys(ins)), list(dict.fromkeys(outs))


def angular_components(root: Path, src_files: list[Path]) -> list[dict]:
    """Every @Component: class, selectors, template (its file or inline), stylesheets, inputs and outputs."""
    out = []
    for f in src_files:
        if f.suffix != ".ts" or re.search(r"\.(spec|test|stories)\.ts$", f.name):
            continue
        t = read(f, 300_000)
        if "@Component" not in t:
            continue
        code = _no_comments(t)
        for m in re.finditer(r"@Component\s*\(\s*\{", code):
            meta = _balanced(code, m.end() - 1)
            rest = code[m.end() - 1 + len(meta) + 2:]
            cm = re.search(r"export\s+(default\s+)?(?:abstract\s+)?class\s+(\w+)[^{]*\{", rest)
            if not cm:
                continue
            body = _balanced(rest, cm.end() - 1)
            sel = re.search(r"\bselector\s*:\s*['\"`]([^'\"`]+)", meta)
            turl = re.search(r"\btemplateUrl\s*:\s*['\"]([^'\"]+)", meta)
            tfile = Path(os.path.normpath(f.parent / turl.group(1))) if turl else None
            template = read(tfile, 200_000) if tfile and tfile.is_file() else (_ng_inline(meta, "template") or "")
            urls = re.findall(r"['\"]([^'\"]+\.(?:s?css|sass|less))['\"]", " ".join(re.findall(r"\bstyleUrls?\s*:\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", meta)))
            ins, outs = _ng_io(body, meta)
            out.append({
                "class": cm.group(2), "default": bool(cm.group(1)), "file": f, "selectors": [s.strip() for s in sel.group(1).split(",")] if sel else [],
                "templateFile": tfile, "template": template, "styles": [Path(os.path.normpath(f.parent / u)) for u in urls],
                "unscoped": bool(re.search(r"encapsulation\s*:\s*ViewEncapsulation\.(?:None|ShadowDom)", meta)),
                "standalone": (True if re.search(r"\bstandalone\s*:\s*true", meta) else False if re.search(r"\bstandalone\s*:\s*false", meta) else None),
                "inputs": ins, "outputs": outs, "code": code,
            })
    return out


def _ng_tag_re(selector: str) -> re.Pattern | None:
    """How a template uses a selector: `app-card` → <app-card, `[appTip]` / `button[appTip]` → an appTip attribute."""
    s = selector.strip()
    if re.match(r"^[a-z][\w-]*$", s):
        return re.compile(r"<" + re.escape(s) + r"(?=[\s/>])")
    m = re.match(r"^([a-z][\w-]*)?\[([\w-]+)\]$", s)
    if m:
        return re.compile(r"<" + (re.escape(m.group(1)) if m.group(1) else r"[\w-]+") + r"\b[^>]*?\s\[?\(?" + re.escape(m.group(2)) + r"\)?\]?(?=[\s=/>])")
    return None


def ng_template_tags(template: str) -> list[str]:
    """The elements a template uses that are components (a dash in the name), in order of first use."""
    return [t for t in dict.fromkeys(re.findall(r"<([a-z][\w]*-[\w-]*)(?=[\s/>])", template)) if t not in NG_STRUCTURAL]


def angular_selector_uses(comps: list[dict]) -> list[dict]:
    """The app's own components by how many templates use them: Angular's answer to 'imported most'."""
    templates = [(c["file"], c["template"]) for c in comps if c["template"]]
    ranked = []
    for c in comps:
        pats = [p for p in (_ng_tag_re(s) for s in c["selectors"]) if p]
        if not pats:
            continue
        n_templates = n_uses = 0
        for f, tmpl in templates:
            if f == c["file"]:
                continue
            k = sum(len(p.findall(tmpl)) for p in pats)
            if k:
                n_templates += 1
                n_uses += k
        if n_templates:
            ranked.append((c, n_templates, n_uses))
    ranked.sort(key=lambda x: (-x[1], -x[2], str(x[0]["file"])))
    return [{"component": c, "templates": n, "uses": u} for c, n, u in ranked]


def _ng_routes_body(root: Path, f: Path, name: str | None, aliases: list) -> tuple[Path, str] | None:
    """The body of a routes array: the one named `name` in file f (followed to the file that declares it),
    its default export, or the array an NgModule hands to RouterModule.forChild."""
    for _ in range(4):
        code = _no_comments(read(f, 300_000))
        if name is None:
            m = re.search(r"export\s+default\s+(\w+)\s*;", code) or re.search(r"export\s+default\s+(?=\[)", code)
            if not m:
                return None
            if m.lastindex:
                name = m.group(1)
            else:
                return f, _balanced(code, m.end())
        decl = re.search(r"(?:const|let|var)\s+" + re.escape(name) + r"\b[^=]*=\s*(?=\[)", code)
        if decl:
            return f, _balanced(code, decl.end())
        mod = re.search(r"class\s+" + re.escape(name) + r"\b", code)
        if mod:                                           # an NgModule: its forChild, here or in the routing module it imports
            fc = re.search(r"RouterModule\.forChild\(\s*(\w+|\[)", code)
            if fc:
                if fc.group(1) == "[":
                    return f, _balanced(code, fc.end() - 1)
                name = fc.group(1)
                continue
            for rm in re.findall(r"\b(\w*Routing\w*Module)\b", code):
                g = _ng_source_of(root, f, code, rm, aliases)
                if g and g != f:
                    f, name = g, rm
                    break
            else:
                return None
            continue
        g = _ng_source_of(root, f, code, name, aliases)
        if not g or g == f:
            return None
        f = g
    return None


def _ng_guard_names(v: str | None) -> list[str]:
    if not v:
        return []
    inner = _balanced(v, 0) if v.startswith("[") else v
    out = []
    for g in _split_top(inner):
        m = re.match(r"^(?:inject\()?\s*([A-Za-z_$][\w$]*)\s*\)?$", g)
        out.append(m.group(1) if m else "(inline)")
    return out


def angular_routes(root: Path, src_files: list[Path], aliases: list) -> dict:
    """The route table from provideRouter / RouterModule.forRoot, lazy children followed. Each record:
    path, the component's class and file, lazy, guards (inherited), redirect, and the layout it sits in."""
    start = None
    for f in src_files:
        if f.suffix != ".ts" or re.search(r"\.(spec|test)\.ts$", f.name):
            continue
        t = read(f, 300_000)
        m = re.search(r"(?:provideRouter|RouterModule\.forRoot)\(\s*(\w+|\[)", _no_comments(t))
        if m:
            start = (f, m)
            break
    if not start:
        return {"routes": [], "file": None}
    f, m = start
    code = _no_comments(read(f, 300_000))
    if m.group(1) == "[":
        found = (f, _balanced(code, m.end() - 1))
    else:
        found = _ng_routes_body(root, f, m.group(1), aliases)
    records: list[dict] = []
    _GUARD_FILES.clear()
    if found:
        _ng_walk(root, found[0], found[1], "", [], None, aliases, records, 0)
    return {"routes": records, "file": rel(root, found[0]) if found else None}


_GUARD_FILES: dict[str, Path] = {}   # guard name → the routes file that names it (filled by _ng_walk)


def _ng_walk(root: Path, f: Path, body: str, prefix: str, guards: list[str], layout: dict | None,
             aliases: list, out: list[dict], depth: int) -> None:
    if depth > 6 or len(out) > 200:
        return
    code = _no_comments(read(f, 300_000))
    for el in _split_top(body):
        if el.startswith("..."):                          # ...OTHER_ROUTES
            found = _ng_routes_body(root, f, el[3:].strip(), aliases)
            if found:
                _ng_walk(root, found[0], found[1], prefix, guards, layout, aliases, out, depth + 1)
            continue
        if not el.startswith("{"):
            continue
        fl = _fields(_balanced(el, 0))
        path = _unquote(fl.get("path")) or ""
        full = "/" + "/".join(x for x in (prefix.strip("/"), path.strip("/")) if x)
        g = guards + [n for k in ("canActivate", "canMatch", "canLoad", "canActivateChild") for n in _ng_guard_names(fl.get(k))]
        g = list(dict.fromkeys(g))
        for n in g:
            _GUARD_FILES.setdefault(n, f)
        rec = {"path": "**" if path == "**" else full, "guards": g, "layout": layout, "lazy": False, "cls": None, "file": None,
               "redirect": None, "title": _unquote(fl.get("title")), "outlet": _unquote(fl.get("outlet"))}
        if "redirectTo" in fl:
            rec["redirect"] = _unquote(fl["redirectTo"]) or "(computed)"
            out.append(rec)
            continue
        if "component" in fl:
            rec["cls"] = fl["component"].strip()
            rec["file"] = _ng_source_of(root, f, code, rec["cls"], aliases)
        elif "loadComponent" in fl:
            lm = NG_LAZY.search(fl["loadComponent"])
            if lm:
                rec["lazy"] = True
                rec["file"] = _ng_resolve(root, f, lm.group(1), aliases)
                dm = re.search(r"export\s+default\s+class\s+(\w+)", read(rec["file"], 300_000)) if rec["file"] and not lm.group(3) else None
                rec["cls"] = lm.group(3) or (dm.group(1) if dm else "(default export)")
        child_layout = {"cls": rec["cls"], "file": rec["file"], "path": rec["path"]} if rec["cls"] else layout
        kids = fl.get("children")
        if kids:
            if rec["cls"]:
                rec["hasChildren"] = True
                out.append(rec)
            if kids.startswith("["):
                _ng_walk(root, f, _balanced(kids, 0), full, g, child_layout, aliases, out, depth + 1)
            else:
                found = _ng_routes_body(root, f, kids, aliases)
                if found:
                    _ng_walk(root, found[0], found[1], full, g, child_layout, aliases, out, depth + 1)
            continue
        if "loadChildren" in fl:
            lc = fl["loadChildren"]
            lm = NG_LAZY.search(lc)
            spec, name = (lm.group(1), lm.group(3)) if lm else ((_unquote(lc) or "").split("#") + [None])[:2]
            target = _ng_resolve(root, f, spec, aliases) if spec else None
            found = _ng_routes_body(root, target, name, aliases) if target else None
            if rec["cls"]:
                rec["hasChildren"] = True
                out.append(rec)
            if found:
                n0 = len(out)
                _ng_walk(root, found[0], found[1], full, g, child_layout, aliases, out, depth + 1)
                for r in out[n0:]:
                    r["lazy"] = True
            continue
        if rec["cls"]:
            out.append(rec)


def _ng_injected(code: str) -> list[str]:
    """Classes a component or service asks for: inject(X), or constructor(private x: X)."""
    names = re.findall(r"\binject\(\s*([A-Z]\w*)", code)
    cm = re.search(r"constructor\s*\(", code)
    if cm:
        names += re.findall(r"(?:private|protected|public|readonly)\s+(?:readonly\s+)?\w+\s*:\s*([A-Z]\w*)", _balanced(code, cm.end() - 1))
    return list(dict.fromkeys(names))


def angular_env(root: Path, ws: dict | None) -> dict[str, str]:
    """String values of the environment file `ng serve` uses (the development replacement when there is one)."""
    src = root / (ws or {}).get("src", "src")
    cands = [root / w for r, w in (ws or {}).get("env", []) if w and "environment" in w] + [src / "environments" / "environment.development.ts", src / "environments" / "environment.ts"]
    for c in cands:
        if c.is_file():
            return dict(re.findall(r"(\w+)\s*:\s*['\"`]([^'\"`]*)['\"`]", _no_comments(read(c))))
    return {}


def _ng_url(expr: str, env: dict, fields: dict) -> str:
    """A request's URL argument as a path: template literals and `+` joins resolved where the parts are known."""
    expr = expr.strip()
    if expr.startswith("`"):
        s = expr.strip("`")
    else:
        parts = []
        for p in re.split(r"\s*\+\s*", expr):
            q = _unquote(p)
            parts.append(q if q is not None else "${" + p + "}")
        s = "".join(parts)

    def sub(m):
        name = m.group(1).strip()
        if not re.match(r"^[\w$.]+$", name):
            return "{…}"
        key = name.split(".")[-1]
        if name.startswith("environment."):
            return env.get(key, "{" + key + "}")
        if name.startswith("this.") and key in fields:
            return fields[key]
        return "{" + key + "}"
    return re.sub(r"\$\{([^}]*)\}", sub, s)


def angular_http(root: Path, src_files: list[Path], env: dict) -> dict[Path, dict]:
    """Services that call HttpClient: per file, the class and each method's requests (GET /api/x)."""
    out: dict[Path, dict] = {}
    for f in src_files:
        if f.suffix != ".ts" or re.search(r"\.(spec|test)\.ts$", f.name):
            continue
        t = read(f, 300_000)
        if "HttpClient" not in t:
            continue
        code = _no_comments(t)
        members = re.findall(r"(\w+)\s*=\s*inject\(\s*HttpClient\s*\)", code) + re.findall(r"(?:private|protected|public|readonly)\s+(?:readonly\s+)?(\w+)\s*:\s*HttpClient\b", code)
        if not members:
            continue
        fields = {k: _ng_url(v, env, {}) for k, v in re.findall(r"(?:private|protected|public|readonly|static)?\s*(\w+)\s*=\s*((?:environment\.\w+|['\"`][^'\"`]*['\"`])(?:\s*\+\s*['\"`][^'\"`]*['\"`])?)\s*;", code)}
        cls = re.search(r"export\s+class\s+(\w+)", code)
        methods: dict[str, list[str]] = {}
        call = re.compile(r"\b(?:this\.)?(?:" + "|".join(map(re.escape, dict.fromkeys(members))) + r")\s*\.\s*(get|post|put|patch|delete|request)\s*(?:<[^()]*?>)?\s*\(")
        for m in call.finditer(code):
            args = _split_top(_balanced(code, m.end() - 1))
            if not args:
                continue
            head = code[:m.start()]
            owner = None
            for om in re.finditer(r"\n\s+(?:(?:public|private|protected|async|static|override)\s+)*(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?::[^{]*)?\{", head):
                owner = om.group(1)
            if owner in {"if", "for", "while", "switch", "constructor", "catch", "function"}:
                owner = None
            methods.setdefault(owner or "?", []).append(f"{m.group(1).upper()} `{_ng_url(args[0], env, fields)}`")
        if methods:
            out[f] = {"class": cls.group(1) if cls else f.stem, "methods": {k: list(dict.fromkeys(v)) for k, v in methods.items()}}
    return out


def _ng_page_data(root: Path, comp: dict, http: dict[Path, dict], aliases: list) -> list[str]:
    """The requests a page's own code sets off: the service methods it calls, through what it injects."""
    code = comp["code"]
    calls = []
    for svc in _ng_injected(code):
        g = _ng_source_of(root, comp["file"], code, svc, aliases)
        if not g or g not in http:
            continue
        var = re.findall(r"(\w+)\s*=\s*inject\(\s*" + svc + r"\b", code) + re.findall(r"(\w+)\s*:\s*" + svc + r"\b", code)
        used = set(re.findall(r"inject\(\s*" + svc + r"\s*\)\s*\.\s*(\w+)\(", code))
        for v in var:
            used |= set(re.findall(r"\b(?:this\.)?" + re.escape(v) + r"\s*\.\s*(\w+)\s*\(", code))
        for meth, reqs in http[g]["methods"].items():
            if meth in used:
                calls += [f"{r} ({svc}.{meth})" for r in reqs]
    return list(dict.fromkeys(calls))


def _ng_session(root: Path, f: Path, aliases: list, depth: int = 0, seen: set | None = None) -> list[tuple[str, str]]:
    """Where a guard's service keeps the session: storage keys in it or in the services it injects."""
    seen = seen if seen is not None else set()
    if f in seen or depth > 3:
        return []
    seen.add(f)
    t = _no_comments(read(f, 200_000))
    found = [(f"localStorage `{k}`", rel(root, f)) for k in re.findall(r"(?:local|session)Storage(?:\.(?:getItem|setItem)\(\s*|\[\s*)['\"]([^'\"]+)['\"]", t)]
    for name, key in re.findall(r"(?:const|readonly|private|static)\s+(?:readonly\s+)?(\w*(?:key|KEY|Key))\s*=\s*['\"]([\w.:/-]+)['\"]", t):
        m = re.search(r"(\w*(?:Storage|store|storage)\w*)\s*\.\s*(?:get|set|getItem|setItem|remove|removeItem)\w*\(\s*(?:this\.)?" + re.escape(name) + r"\b", t)
        if m:
            found.append((f"{m.group(1)} `{key}`" if m.group(1) in ("localStorage", "sessionStorage") else f"storage key `{key}`", rel(root, f)))
    for svc in _ng_injected(t):
        g = _ng_source_of(root, f, t, svc, aliases)
        if g and g != f:
            found += _ng_session(root, g, aliases, depth + 1, seen)
    return list(dict.fromkeys(found))


def angular_guards(root: Path, routes: list[dict], routes_file: str | None, aliases: list) -> list[str]:
    """One line per guard: the pages it covers, where it redirects, and for a sign-in guard where the session lives."""
    covers: dict[str, list[str]] = collections.defaultdict(list)
    for r in routes:
        if r["cls"] and not r.get("hasChildren"):
            for g in r["guards"]:
                covers[g].append(r["path"])
    lines = []
    for g, paths in covers.items():
        src_file = _GUARD_FILES.get(g) or (root / routes_file if routes_file else None)
        if g == "(inline)" or not src_file:
            continue
        code = _no_comments(read(src_file, 300_000))
        gf = _ng_source_of(root, src_file, code, g, aliases)
        pkg = None
        if not gf:
            pm = re.search(r"import\s*\{[^}]*\b" + re.escape(g) + r"\b[^}]*\}\s*from\s*['\"]([^'\"]+)['\"]", code)
            pkg = pm.group(1) if pm else None
        gt = _no_comments(read(gf, 200_000)) if gf else ""
        if gf and gf == src_file:                        # a guard declared in the routes file: its own statement
            m = re.search(r"(?:const|function)\s+" + re.escape(g) + r"\b", gt)
            gt = gt[m.start(): m.start() + 900] if m else ""
        to = re.search(r"(?:createUrlTree|navigate)\(\s*\[\s*['\"]([^'\"]+)|(?:parseUrl|navigateByUrl)\(\s*['\"]([^'\"]+)", gt)
        target = (to.group(1) or to.group(2)) if to else None
        shown = ", ".join(f"`{p}`" for p in paths[:4]) + (f" and {len(paths) - 4} more" if len(paths) > 4 else "")
        line = f"guard `{g}`" + (f" (`{rel(root, gf)}`)" if gf and gf != src_file else f" (from `{pkg}`)" if pkg else "") + f" runs before {shown}"
        if target:
            line += f"; it can redirect to `{target}`"
        if re.search(r"login|sign-?in|auth", target or "", re.I) or re.search(r"auth|login|session|token", g, re.I):
            session = []
            for svc in _ng_injected(gt) if gf else []:
                sf = _ng_source_of(root, gf, _no_comments(read(gf, 200_000)), svc, aliases)
                if sf:
                    session += _ng_session(root, sf, aliases)
            line += " — a render there needs a session"
            if session:
                keys = list(dict.fromkeys(k for k, _ in session))
                line += ": " + ", ".join(keys[:2]) + f" (`{session[0][1]}`): seed it with `--init-script`, or sign in with `--act`"
            else:
                line += " (`--init-script` / `--storage-state`, or sign in with `--act`)"
        lines.append(line)
    return lines


def angular_bootstrap(root: Path, ws: dict | None, comps: list[dict], aliases: list) -> dict | None:
    """The root component: bootstrapApplication(App) in main.ts, or an NgModule's `bootstrap: [AppComponent]`."""
    src = root / (ws or {}).get("src", "src")
    main = next((m for m in (src / "main.ts", root / "src" / "main.ts") if m.is_file()), None)
    if not main:
        return None
    t = _no_comments(read(main))
    m = re.search(r"bootstrapApplication\(\s*(\w+)", t)
    f, name = main, None
    if m:
        name = m.group(1)
    else:
        mm = re.search(r"bootstrapModule\(\s*(\w+)", t)
        mf = _ng_source_of(root, main, t, mm.group(1), aliases) if mm else None
        if mf:
            mt = _no_comments(read(mf))
            bm = re.search(r"bootstrap\s*:\s*\[\s*(\w+)", mt)
            if bm:
                f, t, name = mf, mt, bm.group(1)
    if not name:
        return None
    cf = _ng_source_of(root, f, t, name, aliases)
    return next((c for c in comps if c["class"] == name and c["file"] == cf), None)


def _ng_comp(comps: list[dict], cls: str | None, file: Path | None) -> dict | None:
    if not file:
        return None
    same = [c for c in comps if c["file"] == file]
    return next((c for c in same if c["class"] == cls), None) or next((c for c in same if c["default"]), None) or (same[0] if len(same) == 1 else None)


def angular_material(root: Path, css_files: list[Path], ws: dict | None, comps: list[dict], deps: dict) -> dict | None:
    """Angular Material's theme: the mixin that builds it, palettes, typography, density, and its components by use."""
    if "@angular/material" not in deps:
        return None
    info: dict = {"file": None, "kind": None, "colors": {}, "typography": None, "density": None, "prebuilt": None, "overrides": []}
    for s in (ws or {}).get("styles", []):
        m = re.search(r"prebuilt-themes/([\w-]+)\.css", s)
        if m:
            info["prebuilt"] = m.group(1)
    themes = []
    src = root / (ws or {}).get("src", "src")
    for c in sorted((c for c in css_files if c.suffix in {".scss", ".sass"}),
                    key=lambda c: (0 if src in c.parents else 1, 0 if re.search(r"default|light|main|theme", c.stem, re.I) and "dark" not in c.stem.lower() and "black" not in c.stem.lower() else 1, str(c))):
        t = read(c)
        themes += [n for n in re.findall(r"\$([\w-]+)\s*:\s*(?:mat\.)?(?:m2-)?(?:define-(?:light-|dark-)?theme|mat-(?:light|dark)-theme)\(", t)]
        m = re.search(r"mat\.theme\(\s*\(", t) or re.search(r"mat\.(?:m2-)?define-(?:light-|dark-)?theme\(", t) or re.search(r"(?<![\w-])mat-(?:light|dark)-theme\(", t)
        if m and not info["file"]:
            body = _balanced(t, t.index("(", m.start()))
            info["file"] = f"{rel(root, c)}:{t[:m.start()].count(chr(10)) + 1}"
            info["kind"] = "M3" if "mat.theme(" in m.group(0) or (re.search(r"define-theme\($", m.group(0)) and "m2-" not in m.group(0)) else "M2"
            for role, pal in re.findall(r"(primary|secondary|tertiary|accent|warn|error|neutral)\s*:\s*(?:mat\.)?\$?(?:m2-)?([\w-]+?)(?:-palette)?(?![\w-])", body):
                info["colors"].setdefault(role, pal)
            if info["kind"] == "M2" and not info["colors"]:        # M2: palettes are variables defined above the call
                for var, pal in re.findall(r"\$([\w-]+)\s*:\s*(?:mat\.)?(?:m2-)?(?:define-)?(?:mat-)?palette\(\s*(?:mat\.)?\$(?:m2-|mat-)?([\w-]+?)(?:-palette)?(?![\w-])", t):
                    role = next((r for r in ("primary", "accent", "warn") if r in var), None)
                    if role:
                        info["colors"].setdefault(role, pal)
            ty = re.search(r"typography\s*:\s*([\w' -]+|\([^)]*\))", body)
            info["typography"] = ty.group(1).strip().strip("'\"") if ty else None
            dn = re.search(r"density\s*:\s*(-?\d)", body)
            info["density"] = dn.group(1) if dn else None
        info["overrides"] += re.findall(r"mat\.([\w-]+)-overrides\(", t)
    counts: collections.Counter = collections.Counter()
    sys_vars = 0
    for c in comps:
        counts.update(re.findall(r"<(mat-[\w-]+)(?=[\s/>])", c["template"]))
        counts.update("mat-" + re.sub(r"(?<!^)(?=[A-Z])", "-", a).lower() for a in re.findall(r"\smat(Button|IconButton|FlatButton|StrokedButton|RaisedButton|Fab|MiniFab|Input|Tooltip|Badge|Ripple|SortHeader)(?=[\s=>/])", c["template"]))
        counts.update(re.findall(r"\s(mat-(?:raised|flat|stroked|icon|mini-fab|fab)?-?button|mat-table|mat-sort-header|mat-list-item|mat-menu-item)(?=[\s=>/])", c["template"]))
        for s in c["styles"]:
            sys_vars += len(re.findall(r"var\(\s*--mat-sys-", read(s, 100_000)))
        sys_vars += len(re.findall(r"var\(\s*--mat-sys-", _ng_inline(c["code"], "styles") or ""))
    info["components"] = counts.most_common(14)
    info["sysVars"] = sys_vars
    info["overrides"] = list(dict.fromkeys(info["overrides"]))[:8]
    info["themes"] = list(dict.fromkeys(themes))[:6]
    return info


def angular_dark(root: Path, css_files: list[Path]) -> tuple[str, str] | None:
    """A class that switches the theme: named like one (.dark-theme, .theme-dark), setting `color-scheme: dark`,
    or wrapping a Material dark theme. Returns (class, file:line)."""
    dark_vars = set()
    for c in css_files:
        t = read(c)
        dark_vars |= set(re.findall(r"\$([\w-]+)\s*:\s*(?:mat\.)?(?:m2-)?(?:define-dark-theme|mat-dark-theme)\(", t))
        dark_vars |= {v for v, body in re.findall(r"\$([\w-]+)\s*:\s*mat\.define-theme\(\s*\((.*?)\)\s*\)\s*;", t, re.S) if re.search(r"theme-type\s*:\s*dark", body)}
    for c in css_files:
        t = read(c)
        for m in re.finditer(r"(?m)^[ \t]*((?:html|body|:root)?\.([\w-]+))(?![\w.:#\[-])[^{};]*\{", t):
            cls, block = m.group(2), block_after(t, m.start())
            if NG_THEME_CLASS.match(cls) or (NG_PREFIXED_THEME.match(cls) and re.search(r"--[\w-]+\s*:|color-scheme\s*:", block)) \
                    or re.search(r"color-scheme\s*:\s*dark\b", block) \
                    or any(re.search(r"\(\s*\$" + re.escape(v) + r"\s*\)", block) for v in dark_vars):
                return cls, f"{rel(root, c)}:{t[:m.start()].count(chr(10)) + 1}"
    return None


def angular_dark_setter(root: Path, src_files: list[Path], cls: str) -> str | None:
    """The TypeScript that puts the theme class on the page, and the storage key it remembers the choice in."""
    for f in src_files:
        if f.suffix != ".ts" or re.search(r"\.(spec|test)\.ts$", f.name):
            continue
        t = read(f, 200_000)
        if cls not in t:
            continue
        if re.search(r"(?:classList\.(?:add|toggle|replace)|addClass)\([^)]*['\"]" + re.escape(cls) + r"['\"]", t) or re.search(r"\[class\.\s*" + re.escape(cls), t):
            key = re.search(r"localStorage\.(?:getItem|setItem)\(\s*['\"]([^'\"]+)", t)
            kv = re.findall(r"(?:const|readonly|private|static)\s+(?:readonly\s+)?(\w*(?:key|KEY|Key))\s*=\s*['\"]([\w.:/-]+)['\"]", t)
            local = bool(kv) and bool(re.search(r"localStorage\.(?:getItem|setItem)\(\s*(?:this\.)?" + re.escape(kv[0][0]) + r"\b", t))
            where = f"localStorage `{key.group(1)}`" if key else (f"{'localStorage' if local else 'storage key'} `{kv[0][1]}`" if kv else None)
            follows = " — follows the OS until chosen" if "prefers-color-scheme" in t else ""
            key_name = key.group(1) if key else (kv[0][1] if kv and local else None)
            switch = f"; render dark through it: `--dark-storage {key_name}=dark`" if key_name and re.search(r"['\"]dark['\"]", t) else ""
            return f"set by `{rel(root, f)}`" + (f" ({where})" if where else "") + follows + switch
    return None


def angular_proxies(root: Path, ws: dict | None) -> list[tuple[str, str, str]]:
    """`ng serve`'s proxy file (proxy.conf.json, or a .js one): path → target."""
    f = root / ws["proxy"] if ws and ws.get("proxy") else None
    if not f or not f.is_file():
        return []
    t = _no_comments(read(f))
    out = []
    if f.suffix == ".json":
        try:
            d = json.loads(re.sub(r",(\s*[}\]])", r"\1", t))
        except json.JSONDecodeError:
            d = {}
        items = d.items() if isinstance(d, dict) else [((x.get("context") or ["?"])[0], x) for x in d if isinstance(x, dict)]
        out = [(k, (v or {}).get("target", "?"), rel(root, f)) for k, v in items if isinstance(v, dict)]
    else:
        out = [(p, tg, rel(root, f)) for p, tg in re.findall(r"['\"]([^'\"]+)['\"]\s*:\s*\{[^}]*?target\s*:\s*['\"]([^'\"]+)['\"]", t, re.S)]
    return out[:6]


def angular_interceptors(root: Path, src_files: list[Path], aliases: list) -> list[str]:
    """HTTP interceptors that change where requests go (a base URL) or add a session header; an in-browser fake backend."""
    lines = []
    for f in src_files:
        if f.suffix != ".ts" or re.search(r"\.(spec|test)\.ts$", f.name):
            continue
        t = read(f, 200_000)
        m = re.search(r"(\w*InMemoryWebApiModule)\.forRoot\(\s*(\w+)", t)
        if m:
            src = _ng_source_of(root, f, _no_comments(t), m.group(2), aliases)
            lines.append(f"`{rel(root, f)}` answers the app's HTTP calls in the browser (angular-in-memory-web-api, `{m.group(2)}`"
                         + (f" in `{rel(root, src)}`" if src else "") + "): nothing to mock or start")
        if "HttpInterceptor" not in t and "HttpHandlerFn" not in t:
            continue
        code = _no_comments(t)
        um = re.search(r"clone\(\s*\{[^}]*?\burl\s*:\s*(`[^`]*`|['\"][^'\"]*['\"])", code, re.S)
        name = re.search(r"export\s+(?:const|function|class)\s+(\w+)", code)
        if um:
            base = re.sub(r"\$\{[^}]*url[^}]*\}", "", um.group(1).strip("`'\""))
            if base and not base.startswith("${"):
                lines.append(f"interceptor `{name.group(1) if name else f.stem}` (`{rel(root, f)}`) sends every request to `{base}` + its path — mock that host, or let the requests through")
    return lines[:4]


def angular_start(root: Path, src_files: list[Path], css_files: list[Path], deps: dict) -> dict:
    """Start-here pieces for an Angular app: pages from the route table, layouts, what guards them, what they fetch."""
    ws = angular_workspace(root)
    aliases = ts_aliases(root)
    comps = angular_components(root, src_files)
    rt = angular_routes(root, src_files, aliases)
    routes = rt["routes"]
    env = angular_env(root, ws)
    http = angular_http(root, src_files, env)
    by_comp: dict[tuple, list[dict]] = {}
    for r in routes:
        if r["cls"] and r["file"] and not r.get("hasChildren"):
            by_comp.setdefault((r["file"], r["cls"]), []).append(r)
    pages = []
    for (file, cls), rs in by_comp.items():
        c = _ng_comp(comps, cls, file)
        tmpl = c["template"] if c else ""
        code = c["code"] if c else ""
        signals = _signals(tmpl)
        if re.search(r"\bMatDialog\b|\bDialogService\b|\bNzModalService\b|\bdialog\.open\(", code) and "dialog" not in signals:
            signals.append("opens dialogs")
        data = _ng_page_data(root, c, http, aliases) if c else []
        if data:
            signals.append("data: " + ", ".join(data[:3]) + (f", … {len(data) - 3} more" if len(data) > 3 else ""))
        lay = rs[0]["layout"]
        lc = _ng_comp(comps, lay["cls"], lay["file"]) if lay else None
        renders = {"name": lay["cls"], "file": rel(root, lay["file"]), "lines": (lc["template"].count("\n") + 1) if lc else 0,
                   "signals": [], "wrapper": True, "outlet": True} if lay and lay.get("file") else None
        paths = list(dict.fromkeys(r["path"] for r in rs))
        pages.append({
            "file": rel(root, file), "lines": tmpl.count("\n") + 1 if tmpl else 0, "signals": signals, "classes": [],
            "components": ng_template_tags(tmpl)[:6], "renders": renders,
            "route": ", ".join(f"`{p}`" for p in paths[:3]) + (" (lazy)" if rs[0]["lazy"] else ""),
            "template": (c["templateFile"].name if c and c["templateFile"] else "inline") if c else None,
            "guards": rs[0]["guards"],
        })
    pages.sort(key=lambda p: p["file"])
    shown_routes = []
    for r in routes:
        if r["redirect"] is not None:
            shown_routes.append((r["path"], f"`{r['redirect']}` (redirect)"))
        elif r["cls"]:
            shown_routes.append((r["path"], r["cls"] + (" (lazy)" if r["lazy"] else "") + (" (layout)" if r.get("hasChildren") else "")))
    root_comp = angular_bootstrap(root, ws, comps, aliases)
    layouts = []
    if root_comp:
        sel = next(iter(root_comp["selectors"]), "app-root")
        layouts.append({"file": rel(root, root_comp["file"]), "scopeText": f"is the root (`<{sel}>`): wraps every page",
                        "css": [s for s in (ws or {}).get("styles", [])][:4], "fonts": [], "providers": [],
                        "chrome": ng_template_tags(root_comp["template"])[:8]})
    seen = set()
    for r in routes:
        lay = r["layout"]
        if not lay or not lay.get("file") or (lay["cls"], lay["file"]) in seen:
            continue
        seen.add((lay["cls"], lay["file"]))
        under = [p["route"].split(",")[0].split(" ")[0] for p in pages if p["renders"] and p["renders"]["name"] == lay["cls"]]
        lc = _ng_comp(comps, lay["cls"], lay["file"])
        layouts.append({"file": rel(root, lay["file"]),
                        "scopeText": f"wraps the {len(under)} page{'s' if len(under) != 1 else ''} under `{lay['path']}`" + (f" ({', '.join(under[:4])}{', …' if len(under) > 4 else ''})" if under else ""),
                        "css": [], "fonts": [], "providers": [], "chrome": ng_template_tags(lc["template"])[:8] if lc else []})
    before = angular_guards(root, routes, rt["file"], aliases)
    before += angular_interceptors(root, src_files, aliases)
    for f, svc in list(http.items())[:4]:
        reqs = [r for rs_ in svc["methods"].values() for r in rs_]
        before.append(f"`{rel(root, f)}` ({svc['class']}) calls " + ", ".join(list(dict.fromkeys(reqs))[:5]) + (", …" if len(set(reqs)) > 5 else "")
                      + " — mock what the page needs (`--mock`), or start the backend")
    for s in (ws or {}).get("styles", []):
        if not (root / s).exists() and not s.startswith(("@", "node_modules")):
            before.append(f"`angular.json` lists the stylesheet `{s}`, which is not on disk" + (" (a git submodule: `git submodule update --init`)" if (root / ".gitmodules").is_file() and s.split("/")[0] in read(root / ".gitmodules") else "") + " — the build stops without it")
    if ws and ws.get("ssr"):
        before.append("server-side rendering (`@angular/ssr`): `ng serve` renders each page on the server first, then hydrates it")
    uses = angular_selector_uses(comps)
    pages_files = {p["file"] for p in pages}
    used = [{"file": rel(root, u["component"]["file"]), "selector": u["component"]["selectors"][0] if u["component"]["selectors"] else "?",
             "templates": u["templates"], "uses": u["uses"], "inputs": u["component"]["inputs"][:7], "outputs": u["component"]["outputs"][:4]}
            for u in uses if rel(root, u["component"]["file"]) not in pages_files][:10]
    major = re.search(r"(\d+)", deps.get("@angular/core", ""))
    major = int(major.group(1)) if major else 0
    modules = sum(1 for c in comps if c["standalone"] is False or (c["standalone"] is None and major and major < 19))
    scoped = {s for c in comps if not c["unscoped"] for s in c["styles"]}
    return {
        "pages": pages[:24], "routes": shown_routes[:30], "layouts": layouts[:6], "stackBefore": before,
        "ngUsed": used, "material": angular_material(root, css_files, ws, comps, deps),
        "router": ("NgModules" if modules > len(comps) / 2 else "standalone components") + (f"; routes in `{rt['file']}`" if rt["file"] else ""),
        "port": (ws or {}).get("port"), "proxies": angular_proxies(root, ws), "scopedCss": scoped, "components": len(comps),
        "inlineTemplates": [c["template"] for c in comps if not c["templateFile"] and c["template"]],
    }


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
        keys = re.findall(r"(?:localStorage|sessionStorage)(?:\.(?:getItem|setItem)\(\s*|\[\s*)['\"`]([^'\"`$]+)['\"`]", t)
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
    ng = angular_start(root, src_files, css_files, deps) if stack.get("framework") == "Angular" else None
    if ng:      # a component's own stylesheet is scoped to it: only the global ones make a vocabulary
        texts += ng["inlineTemplates"]
        vocab = css_vocabulary(root, [c for c in css_files if c not in ng["scopedCss"]], texts, skip=r"(?:mat|mdc|cdk)-")
        sig = {"pages": ng["pages"], "routes": ng["routes"]}
    else:
        vocab = css_vocabulary(root, css_files, texts)
        sig = page_signatures(root, src_files, [v["name"] for v in vocab], stack.get("framework"))
    is_next = stack.get("framework") == "Next.js"
    is_nuxt = stack.get("framework") == "Nuxt"
    is_kit, is_astro = stack.get("framework") == "SvelteKit", stack.get("framework") == "Astro"
    notes = {"Nuxt": "references/stacks/nuxt.md", "Vue": "references/stacks/vue.md", "SvelteKit": "references/stacks/sveltekit.md",
             "Svelte": "references/stacks/sveltekit.md", "Astro": "references/stacks/astro.md",
             "Angular": "references/stacks/angular.md"}.get(stack.get("framework") or "")
    dev = dev_setup(root)
    theme = theme_mechanism(root, css_files, stack, src_files)
    if ng:
        dev["proxies"] = ng["proxies"] + dev["proxies"]
    return {
        "vocabulary": vocab,
        "imported": [] if ng else import_fanin(root, src_files),
        **sig,
        "layouts": (next_layouts(root) if is_next else nuxt_layouts(root, src_files) if is_nuxt else sveltekit_layouts(root) if is_kit
                    else astro_layouts(root, src_files) if is_astro else ng["layouts"] if ng else []),
        "stackBefore": sveltekit_before(root, deps) if is_kit else astro_before(root, deps) if is_astro else ng["stackBefore"] if ng else [],
        "ngUsed": ng["ngUsed"] if ng else [],
        "material": ng["material"] if ng else None,
        "ng": {"port": ng["port"], "router": ng["router"], "components": ng["components"]} if ng else None,
        "astro": is_astro,
        "autoImported": vue_component_uses(root, src_files, nuxt_components(root)) if is_nuxt else [],
        "nuxtui": nuxt_ui(root, src_files, deps),
        "nuxtBefore": nuxt_before(root, deps, src_files) if is_nuxt else [],
        "nuxt": is_nuxt,
        "vite": "vite" in deps and not is_next and not is_nuxt and not is_astro and not ng,
        "stackNotes": notes,
        "theme": theme,
        "middleware": middleware_line(root) if is_next else None,
        "locale": locale_routing(root, src_files, sig["routes"]),
        "next": is_next,
        "contentlayer": any(k in deps for k in ("contentlayer", "contentlayer2", "next-contentlayer", "next-contentlayer2")),
        "copy": copy_mechanism(root, src_files, deps),
        "boot": boot_requests(root, src_files),
        "dev": dev,
        "gates": gates(root, src_files) + [s for s in storage_keys(root, src_files)      # a key a guard or the theme line already names
                                           if not ng or not any(s.split("`")[1] in b for b in ng["stackBefore"] + [theme or ""])],
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
    mt = sh.get("material")
    if mt and (mt["file"] or mt["prebuilt"] or mt["components"]):
        bits = []
        if mt["file"]:
            cols = ", ".join(f"{k} `{v}`" for k, v in mt["colors"].items())
            extra = [x for x in (cols, f"typography {mt['typography']}" if mt["typography"] else "", f"density {mt['density']}" if mt["density"] else "") if x]
            bits.append(f"{mt['kind']} theme at `{mt['file']}`" + (f" ({'; '.join(extra)})" if extra else ""))
        elif mt["prebuilt"]:
            bits.append(f"prebuilt theme `{mt['prebuilt']}` (angular.json)")
        if len(mt.get("themes") or []) > 1:
            bits.append("themes " + ", ".join(f"`${n}`" for n in mt["themes"]))
        if mt["sysVars"]:
            bits.append(f"component styles read its `--mat-sys-*` variables ({mt['sysVars']} uses)")
        if mt["overrides"]:
            bits.append("overrides for " + ", ".join(mt["overrides"]))
        out.append("- Angular Material — " + " · ".join(bits)
                   + (": its components by use, " + " · ".join(f"{n} ×{c}" for n, c in mt["components"]) if mt["components"] else "")
                   + ". A match task builds with these components and " + ("the `--mat-sys-*` variables" if mt["kind"] == "M3" else "the theme's palettes")
                   + ", not hand-picked colours.")
    if sh.get("ngUsed"):
        out.append("- Used most (by selector, counted by the templates that use them): " + " · ".join(
            f"`{u['file']}` `<{u['selector']}>` ({u['templates']}" + (f"; inputs {', '.join(u['inputs'])}" if u["inputs"] else "")
            + (f"; outputs {', '.join(u['outputs'])}" if u["outputs"] else "") + ")" for u in sh["ngUsed"]))
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
            if pg.get("route"):                     # Angular: the route, then the template the page draws with
                bits = [pg["route"], (f"template `{pg['template']}`, " if pg["template"] not in (None, "inline") else "inline template, ") + f"{pg['lines']} lines"]
            if pg["signals"]:
                bits.append(", ".join(pg["signals"]))
            if pg["classes"]:
                bits.append(", ".join(pg["classes"]))
            if pg["components"]:
                bits.append(("uses " if pg["file"].endswith((".vue", ".svelte", ".astro", ".md", ".mdx")) or pg.get("route") else "imports ") + ", ".join(pg["components"]))
            r = pg.get("renders")
            if r and r.get("wrapper"):
                bits.append(f"inside {r['name']}" + ("" if r["file"] in wrappers_named else f" (`{r['file']}` · {r['lines']} lines: the chrome, its "
                                                        + ("`<router-outlet>`" if r.get("outlet") else "slot") + " holds the page)"))
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
        elif sh.get("ng"):
            port = sh["ng"].get("port")
            line += f" — `ng serve` listens on :{port} (`angular.json`)" if port else " — `ng serve` listens on :4200 unless `--port` says otherwise"
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
    if f.get("iconFonts"):
        out.append("- icon font: " + ", ".join(f["iconFonts"]) + " (Google Fonts) — its icons are ligatures: where the font cannot load, each shows as its name (`menu`, `more_vert`)")
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
    sh = start_here(root, src_files, css_files, stack, stack.get("deps") or {}) if not stack.get("workspaceApps") else None
    if sh and sh.get("ng"):
        stack["router"] = sh["ng"]["router"]
    data = {
        "root": str(root), "stack": stack, "tokens": tokens, "fonts": fonts,
        "components": comps, "usage": usage, "docs": docs,
        "verdict": verdict(stack, tokens, fonts, comps, usage, docs, sh),
        "startHere": sh,
    }
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(md(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
