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
    "__pycache__", ".venv", "venv", "vendor", "Pods", ".expo",
}
SRC_EXT = {".tsx", ".jsx", ".ts", ".js", ".mjs", ".mdx", ".astro", ".vue", ".svelte", ".html"}
CSS_EXT = {".css", ".scss", ".pcss"}
MAX_SRC_FILES = 600
MAX_READ = 400_000

KNOWN_FRAMEWORKS = [
    ("next", "Next.js"), ("@remix-run/react", "Remix"), ("@umijs/max", "Umi"), ("umi", "Umi"), ("expo", "Expo"),
    ("react-native", "React Native"), ("react-router", "React Router"),
    ("react-router-dom", "React Router"), ("@tanstack/react-router", "TanStack Router"),
    ("nuxt", "Nuxt"), ("@sveltejs/kit", "SvelteKit"), ("@angular/core", "Angular"),
    ("astro", "Astro"), ("gatsby", "Gatsby"), ("vue", "Vue"), ("svelte", "Svelte"), ("solid-js", "Solid"),
    ("@11ty/eleventy", "Eleventy"), ("vite", "Vite"), ("react-scripts", "Create React App"),
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
    "react-native-paper": "React Native Paper", "tamagui": "Tamagui", "@tamagui/core": "Tamagui", "nativewind": "NativeWind",
    "uniwind": "Uniwind", "@gluestack-ui/themed": "gluestack-ui", "react-native-unistyles": "Unistyles", "@shopify/restyle": "Restyle",
    "@rneui/themed": "React Native Elements", "@ui-kitten/components": "UI Kitten", "native-base": "NativeBase", "heroui-native": "HeroUI Native",
}
KNOWN_ICONS = {
    "lucide-react": "Lucide", "@heroicons/react": "Heroicons", "@phosphor-icons/react": "Phosphor",
    "react-icons": "react-icons", "@tabler/icons-react": "Tabler", "@radix-ui/react-icons": "Radix Icons",
    "@iconify/react": "Iconify",
    "lucide-vue-next": "Lucide", "@iconify/vue": "Iconify", "@heroicons/vue": "Heroicons", "@phosphor-icons/vue": "Phosphor",
    "lucide-angular": "Lucide", "@ng-icons/core": "ng-icons", "@fortawesome/angular-fontawesome": "Font Awesome",
    "@expo/vector-icons": "Expo vector icons", "react-native-vector-icons": "react-native-vector-icons", "expo-symbols": "SF Symbols (expo-symbols)",
    "lucide-react-native": "Lucide", "phosphor-react-native": "Phosphor",
}
KNOWN_MOTION = {
    "framer-motion": "Framer Motion", "motion": "Motion", "gsap": "GSAP",
    "@react-spring/web": "react-spring", "@formkit/auto-animate": "AutoAnimate", "lottie-react": "Lottie",
    "react-native-reanimated": "Reanimated", "moti": "Moti", "lottie-react-native": "Lottie",
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
    fps = flutter_pubspec(root)
    if fps is not None:                              # Dart and Flutter: pubspec.yaml, not package.json
        return flutter_stack(root, fps)
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
    if pkg_path.exists() and not any(key in deps for key, _ in KNOWN_FRAMEWORKS) and "tailwindcss" not in deps:
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
    laravel = laravel_app(root)
    if laravel:
        framework = "Laravel"
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
    if framework in ("Expo", "React Native"):
        rn = rn_app(root, deps)
        router = rn["router"] if rn else None
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
        "reactNative": deps.get("react-native") if framework in ("Expo", "React Native") else None,
        "rnWeb": deps.get("react-native-web") if framework in ("Expo", "React Native") else None,
        "vue": deps.get("vue"),
        "svelte": deps.get("svelte"),
        "frameworkVersion": laravel["version"] if laravel else next((deps.get(key) for key, label in KNOWN_FRAMEWORKS if label == framework and key in deps), None),
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
SASS_KIT_DIRS = {"bootstrap", "foundation", "foundation-sites", "bulma", "bourbon", "neat", "font-awesome", "fontawesome",
                 "materialize", "uikit", "compass", "susy", "breakpoint"}
SASS_VAR = re.compile(r"\$([\w-]+)\s*:\s*(.+?)\s*;?\s*$")


def _scss_top_statements(text: str) -> list[str]:
    """The statements of an SCSS file outside every rule and block, a value that runs over lines joined."""
    out, buf, depth, paren, quote, i = [], [], 0, 0, "", 0
    while i < len(text):
        ch = text[i]
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and text[i + 1:i + 2] == "{":          # interpolation, not a block
            j = text.find("}", i)
            if depth == 0:
                buf.append(text[i:j + 1] if j > 0 else ch)
            i = j + 1 if j > 0 else i + 1
            continue
        elif ch == "{":
            depth, buf = depth + 1, [] if depth == 0 else buf
            i += 1
            continue
        elif ch == "}":
            depth, buf = max(0, depth - 1), []
            i += 1
            continue
        elif ch == "(":
            paren += 1
        elif ch == ")":
            paren = max(0, paren - 1)
        elif ch == ";" and depth == 0 and not paren:
            out.append(" ".join("".join(buf).split()))
            buf = []
            i += 1
            continue
        if depth == 0:
            buf.append(ch)
        i += 1
    return out


def sass_variables(text: str, indented: bool = False) -> list[tuple[str, str]]:
    """The top-level `$name: value` declarations of a Sass file: a project's tokens."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = "\n".join(re.sub(r"(?<!:)//.*$", "", line) for line in text.splitlines())
    stmts = ([line.strip() for line in text.splitlines() if line[:1] == "$"] if indented
             else _scss_top_statements(text))
    out = []
    for stmt in stmts:
        m = SASS_VAR.match(stmt)
        if not m:
            continue
        value = re.sub(r"\s*!(?:default|global)\b", "", m.group(2)).strip()
        # a value: a colour, a length, a font stack, another variable, a colour function; not a map, not a
        # module's call (a Material palette, which the theme line reads), not one cut off mid-expression
        if value and not value.startswith("(") and value.count("(") == value.count(")") \
                and not re.match(r"(?!color\.|math\.)[\w-]+\.[\w$-]+\(|map[-.]|mat-", value):
            out.append((m.group(1), value))
    return out


def collect_tokens(root: Path, css_files: list[Path], stack: dict) -> dict:
    theme_vars: list[tuple[str, str, str]] = []   # (file, name, value)
    root_vars: list[tuple[str, str, str]] = []
    sass_vars: list[tuple[str, str, str]] = []
    dark_block = False
    for p in css_files:
        if p.name.endswith(".min.css") and p.with_name(p.name[:-8] + ".css").is_file():
            continue                                   # the minified twin of a file read already
        text = read(p)
        if not text:
            continue
        if p.suffix in {".scss", ".sass"} and not ({x.lower() for x in p.relative_to(root).parts[:-1]} & SASS_KIT_DIRS):
            sass_vars += [(rel(root, p), f"${n}", v) for n, v in sass_variables(text, p.suffix == ".sass")]
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
        "sass": sass_vars[:120],
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
    ] + [
        (n, v.split(",")[0].strip().strip("\"'"))
        for _, n, v in tokens.get("sass", []) if not v.startswith("$")
        and ("font" in n and "," in v or re.search(r",\s*(?:sans-serif|serif|monospace|system-ui|cursive)\s*$", v))
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
    tokens_declared = bool(tokens["theme"] or tokens["root"] or tokens.get("sass") or tokens["configExtend"])
    sh = sh or {}
    ng, mt, site, lv, rn = sh.get("ng"), sh.get("material"), sh.get("site"), sh.get("laravel"), sh.get("rn")
    fl = sh.get("flutter")
    pages = len(sh.get("pages") or [])
    kk = sh.get("kits") or {}
    kit_list = kk.get("kits") or []
    tokens_declared = tokens_declared or any(k.get("colors") or k.get("scales") or k.get("tokens") or k.get("themes") for k in kit_list) \
        or bool((kk.get("styled") or {}).get("colors"))
    kit_look = (sh.get("kitLook") or bool(rn)) and (not stack.get("tailwind") or usage["rawTotal"] + usage["semanticTotal"] < 10)
    established = (
        usage["rawTotal"] + usage["semanticTotal"] >= 25
        or len(comps["primitives"]) + len(comps["composed"]) >= 4
        or tokens_declared
        or bool(ng and (ng["components"] >= 4 or (mt and (mt["file"] or mt["prebuilt"]))))
        # pages that share a kit, a layout, copied chrome or a stylesheet's classes have a look to match
        or bool(site and pages >= 2 and (site["kits"] or site["copies"] or sh.get("layouts") or len(sh.get("vocabulary") or []) >= 5))
        or bool(lv and pages >= 2 and (sh.get("bladeUsed") or sh.get("bladeKit") or sh.get("layouts")))
        or any(k.get("uses") and sum(c for _, c in k["uses"]) >= 6 for k in kit_list)
        or bool((kk.get("styled") or {}).get("files", 0) >= 5) or bool((kk.get("modules") or {}).get("importers", 0) >= 3)
        or bool(rn and (rn["theme"]["maps"] or any(sum(c for _, c in uses) >= 6 for _, uses in rn["kits"]) or rn["usage"]["themeColors"] >= 10))
        or bool(fl and (fl["theme"]["schemes"] or (fl["theme"]["seeds"] and not fl.get("template")) or fl["theme"]["textStyles"]
                        or len(sh.get("widgets") or []) >= 4 or fl["usage"]["themeColorTotal"] >= 10))
    )
    lines = []
    if mt and (mt["file"] or mt["prebuilt"]):
        cols = ", ".join(f"{k} {v}" for k, v in list(mt["colors"].items())[:2])
        lines.append(f"UI kit: **Angular Material** ({mt['kind'] or 'prebuilt'} theme" + (f", {cols}" if cols else "") + ") — build with its components, not hand-rolled ones")
    if site and site["kits"]:
        lines.append(f"UI kit: **{site['kits']}** — build with its classes, not new CSS")
    if sh.get("bladeKit"):
        lines.append(f"UI kit: **{sh['bladeKit']['name']}** — build with its components, not hand-rolled ones")
    for k in kit_list:
        first = (k.get("colors") or [None])[0] or (k.get("scales") or [None])[0] or (k.get("tokens") or [None])[0] \
            or next((t["colors"][0] for t in k.get("themes") or [] if t["colors"]), None)
        detail = f" ({first[0]} {first[1]})" if first else f" (default theme, primary {KIT_DEFAULT_PRIMARY.get(k['kit'], '?')})"
        lines.append(f"UI kit: **{k['kit']}**{detail} — build with its components and the theme's values, not hand-picked colours")
    if kk.get("styled"):
        lines.append(f"Styling: **{kk['styled']['kit']}** with a theme object — new components are styled components reading the theme")
    if kk.get("modules"):
        lines.append("Styling: **CSS Modules**, one per component — a new component gets its own module")
    if fl:
        th, fu = fl["theme"], fl["usage"]
        if th["schemes"]:
            lines.append(f"Theme: **ColorScheme `{th['schemes'][0]['name'] or '(unnamed)'}`** in `{th['schemes'][0]['file']}`"
                         + (" (light and dark)" if th["schemes"][0]["light"] and th["schemes"][0]["dark"] else "")
                         + " — widgets read `Theme.of(context).colorScheme`, not `Color(0x…)`")
        elif th["seeds"] and fl.get("template"):
            lines.append("Theme: the `flutter create` counter's seed (`Colors.deepPurple`), not a choice yet — pick the app's own direction")
        elif th["seeds"]:
            seed = next((x["seed"] for x in th["seeds"] if re.match(r"^#[0-9A-F]{6}", x["seed"])), "chosen at run time")
            lines.append(f"Theme: **a seed colour ({seed})** — Material 3 generates the scheme; widgets read `colorScheme`, not literals")
        if th["m3"] is False:
            lines.append("Material **2** (`useMaterial3: false`): new widgets keep to it")
        if fu["radius"]:
            lines.append(f"Radius: **{fu['radius'][0][0]}** dominant (`BorderRadius.circular`)")
        if fu.get("steps") and fu["stepTotal"] >= fu.get("spacingTotal", 0):
            lines.append(f"Spacing: **`{fu['steps'][0][0].split('.')[0]}`** steps (`{fu['steps'][0][0]}` ×{fu['steps'][0][1]} most used)"
                         f" against {fu.get('spacingTotal', 0)} bare numbers — new widgets use the steps")
        elif fu["spacing"]:
            lines.append(f"Spacing: **{fu['spacing'][0][0]}** most used (EdgeInsets, SizedBox)")
        if fu["literal"] >= 10 and fu["literal"] > fu["themeColorTotal"]:
            lines.append(f"Colour drift: {fu['literal']} literal colours in widgets against {fu['themeColorTotal']} read from the theme")
    if rn:
        for label, uses in rn["kits"]:
            lines.append(f"UI kit: **{label}** — build with its components and its theme, not hand-rolled views")
        m = (rn["theme"]["maps"] or [None])[0]
        if m:
            lines.append(f"Theme: **`{m['name']}`** in `{m['file']}`" + (" (light and dark)" if m.get("dark") else "")
                         + " — new components take their colours from it, not literals")
        ru = rn["usage"]
        if ru["radius"]:
            lines.append(f"Radius: **{ru['radius'][0][0]}** dominant (StyleSheet)")
        if ru["fontSize"]:
            lines.append(f"Most-used font size: **{ru['fontSize'][0][0]}**")
        if ru["literalColors"] >= 10 and ru["literalColors"] > ru["themeColors"]:
            lines.append(f"Colour drift: {ru['literalColors']} literal colours in components against {ru['themeColors']} read from the theme")
    total_color = 0 if kit_look else usage["rawTotal"] + usage["semanticTotal"]
    if total_color:
        sem_pct = round(100 * usage["semanticTotal"] / total_color)
        if usage["colorFamilies"]:
            fam, n = usage["colorFamilies"][0]
            lines.append(f"Dominant hue family: **{fam}** ({n} uses)")
        lines.append(f"Color naming: {sem_pct}% semantic tokens (`bg-primary`) vs {100 - sem_pct}% raw palette (`bg-indigo-600`)")
    if usage["radius"] and not kit_look:
        lines.append(f"Radius: **rounded-{usage['radius'][0][0]}** dominant" if usage["radius"][0][0] != "default" else "Radius: **rounded** (default) dominant")
    if usage["shadow"] and not kit_look:
        lines.append(f"Shadow: **shadow-{usage['shadow'][0][0]}** dominant" if usage["shadow"][0][0] != "default" else "Shadow: **shadow** (default) dominant")
    if usage["textSize"] and not kit_look:
        lines.append(f"Most-used text size: **text-{usage['textSize'][0][0]}**")
    all_fonts = fonts["nextFont"] + fonts["googleLinks"] + fonts["fontFace"] + [v for _, v in fonts["tokenFonts"]]
    if all_fonts:
        lines.append("Fonts: " + ", ".join(dict.fromkeys(all_fonts))[:160])
    dark_on = sh.get("kitDark") if sh.get("kitDark") is not None else rn["darkOn"] if rn else \
        bool(usage["dark"] or tokens["darkBlock"] or (ng and sh.get("theme")) or (kit_look and sh.get("theme")))
    lines.append("Dark mode: " + ("present" if dark_on else "not used"))
    if usage["arbitraryTotal"] >= 8 and not kit_look:
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
    m = re.search(r"return\s*\(?\s*(?:<>|<(?:React\.)?Fragment>)?\s*(?:<title>[\s\S]{0,200}?</title>\s*|<(?:meta|link)\b[^>]*>\s*|<Helmet\b[\s\S]{0,400}?</Helmet>\s*)*<([A-Z]\w*)", text)
    if not m:
        return None
    name = m.group(1)
    im = re.search(r"import\s+(?:\{[^}]*\b" + re.escape(name) + r"\b[^}]*\}|" + re.escape(name) + r"\b[^;'\"]*)\s*from\s*['\"]([^'\"]+)['\"]", text)
    if not im:
        return None
    target = _resolve_import(root, page, im.group(1))
    if target and target.suffix in {".ts", ".js"}:           # a barrel: sections/blog/view/index.ts
        orig = re.search(r"\b(\w+)\s+as\s+" + re.escape(name) + r"\b", im.group(0))
        target = _ng_defines(root, target, orig.group(1) if orig else name, ts_aliases(root), exts=JS_EXTS)
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
    uses_dark = any("dark:" in read(p, 200_000) for p in src_files[:MAX_SRC_FILES] if p.suffix in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".mdx"} or p.name.endswith(".blade.php"))
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
    if how is None and stack.get("framework") in ("Angular", "Laravel", None, "Eleventy", "Jekyll", "Hugo", "static HTML"):
        found = angular_dark(root, css_files)
        if found:
            cls, where_ = found
            ng_setter = angular_dark_setter(root, src_files, cls)
            on = "`<html>`" if ng_setter and ("`<html class>`" in ng_setter or re.search(r"documentElement|htmlElement|\bhtml\b", read(root / ng_setter.split("`")[1], 200_000))) else "an ancestor"
            scheme = any(re.search(r"\." + re.escape(cls) + r"\b[^{]*\{[^}]*color-scheme\s*:\s*dark", read(c)) for c in css_files)
            how = f"`.{cls}` on {on}" + (" (`color-scheme: dark`: Material's `light-dark()` colours follow it)" if scheme and "@angular/material" in deps else "")
            where, plain = f"`{where_}`", True
    if how is None and "@astrojs/starlight" in deps:
        how, where, plain = "`[data-theme=dark]` on `<html>`", "Starlight's own CSS (`--sl-color-*` properties)", True
    if how is None and "element-plus" in deps:       # Element Plus's own dark variables, under html.dark
        for p in src_files:
            if p.suffix in {".ts", ".js", ".mjs"} and "element-plus/theme-chalk/dark/css-vars.css" in read(p, 200_000):
                how, where, plain = "`.dark` on `<html>`", f"Element Plus's dark variables (`element-plus/theme-chalk/dark/css-vars.css`, imported in `{rel(root, p)}`)", True
                break
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
    if setter is None and stack.get("framework") == "Laravel" and any("@fluxAppearance" in read(p, 100_000) for p in src_files if p.name.endswith(".blade.php")):
        setter = "set before paint by Flux's `@fluxAppearance` (localStorage `flux.appearance`: light, dark or system); render dark through it: `--dark-storage flux.appearance=dark`"
    if setter is None and "@vueuse/core" in deps:   # VueUse's useDark(): .dark on <html>, the choice in localStorage
        for p in src_files:
            if p.suffix not in {".ts", ".js", ".vue", ".mjs"}:
                continue
            t = read(p, 200_000)
            m = re.search(r"\buseDark\(\s*(\{[^)]*\})?\s*\)", t)
            if m and "@vueuse" in t:
                key = re.search(r"storageKey\s*:\s*['\"]([^'\"]+)", m.group(1) or "")
                k = key.group(1) if key else "vueuse-color-scheme"
                setter = f"set by VueUse's `useDark()` in `{rel(root, p)}` (localStorage `{k}`): render dark with `--dark-storage {k}=dark`"
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
    aliases = ts_aliases(root)
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
            c = re.search(r"component\s*:\s*(?:\(\)\s*=>\s*import\(\s*(?:/\*.*?\*/\s*)?['\"]([^'\"]+)['\"]\s*\)|(\w+))", chunk)
            if c:
                spec = c.group(1) or imports.get(c.group(2), "")
                target = _js_resolve(root, p, spec, aliases) if spec else None           # `@/views/login` is login.vue
                if target is None:
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


_STRING_OR_COMMENT = re.compile(r"(\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)|/\*.*?\*/|(?<![:\w'\"`\\])//[^\n]*", re.S)


def _no_comments(t: str) -> str:
    """TypeScript or JSON without comments. Strings are kept whole: the `/*` in a tsconfig path ("#/*") opens no
    comment, and a `//` in a URL ends none; a `//` after a colon or a backslash (a regex literal) is kept too."""
    return _STRING_OR_COMMENT.sub(lambda m: m.group(1) or "", t)


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


NG_EXTS = ("", ".ts", "/index.ts", ".js", "/index.js")


def _ng_resolve(root: Path, from_file: Path, spec: str, aliases: list, exts: tuple = NG_EXTS) -> Path | None:
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
        for ext in exts:
            c = Path(str(b) + ext)
            if c.is_file():
                return Path(os.path.normpath(c))
    return None


def _ng_defines(root: Path, f: Path, name: str, aliases: list, depth: int = 0, exts: tuple = NG_EXTS) -> Path | None:
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
                g = _ng_resolve(root, f, spec, aliases, exts)
                return _ng_defines(root, g, name, aliases, depth + 1, exts) if g else None
    for names, spec in re.findall(r"export\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", t):
        for part in names.split(","):
            bits = [x.strip() for x in part.split(" as ")]
            if bits[-1] == name:
                g = _ng_resolve(root, f, spec, aliases, exts)
                return _ng_defines(root, g, bits[0], aliases, depth + 1, exts) if g else None
    for spec in re.findall(r"export\s*\*\s*from\s*['\"]([^'\"]+)['\"]", t):
        g = _ng_resolve(root, f, spec, aliases, exts)
        hit = _ng_defines(root, g, name, aliases, depth + 1, exts) if g else None
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
    for c in sorted(css_files, key=lambda c: -read(c).count(".dark")):
        t = read(c)
        for m in re.finditer(r"(?m)^[ \t]*((?:html|body|:root)?\.([\w-]+))(?![\w.:#\[-])[^{};]*\{", t):
            cls, block = m.group(2), block_after(t, m.start())
            if NG_THEME_CLASS.match(cls) or (NG_PREFIXED_THEME.match(cls) and re.search(r"--[\w-]+\s*:|color-scheme\s*:", block)) \
                    or re.search(r"color-scheme\s*:\s*dark\b", block) \
                    or any(re.search(r"\(\s*\$" + re.escape(v) + r"\s*\)", block) for v in dark_vars):
                return cls, f"{rel(root, c)}:{t[:m.start()].count(chr(10)) + 1}"
    return None


def angular_dark_setter(root: Path, src_files: list[Path], cls: str) -> str | None:
    """What puts the theme class on the page: a server template writing it into <html class> (a Blade layout),
    or a script (a theme service), with the storage key it remembers the choice in."""
    for f in src_files:
        if f.name.endswith(".blade.php"):
            hm = re.search(r"<html\b(?:(?<=[-=])>|[^>])*?\bclass\s*=\s*\"[^\"]*" + re.escape(cls), read(f, 100_000))   # `->` inside {{ }} is not the tag's end
            if hm and re.search(r"\{\{|@if|@class", hm.group(0)):
                return f"written into `<html class>` by the server in `{rel(root, f)}` from a setting: render dark signed in with it on, or with `--dark`"
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


# ------------------------------------------------- static sites and site generators
# A site with no framework: hand-written HTML pages, or templates a generator (Eleventy, Jekyll,
# Hugo) turns into pages. What a match task needs is the same as elsewhere (the page to copy, what
# wraps it, where the styles are, how to serve it) plus one thing only hand-written sites have:
# the header, nav or footer copied into every page, where one change is an edit to every file.
SITE_SKIP = {"vendor", "vendors", "lib", "libs", "bower_components", "third-party", "third_party", "_site", "public/build"}
STATIC_KITS = [   # (pattern over a <link>/<script> URL or a vendored path, label, version group)
    (r"cdn\.tailwindcss\.com", "Tailwind (Play CDN)", None),
    (r"@tailwindcss/browser@?(\d[\w.]*)?", "Tailwind (browser build)", 1),
    (r"tailwindcss@\^?(\d[\w.]*)[^\s\"']*?/tailwind(?:\.min)?\.css", "Tailwind (prebuilt CSS)", 1),
    (r"bootstrap@\^?(\d[\w.]*)|/bootstrap/(\d[\w.]*)/|bootstrap(?:\.bundle)?(?:\.min)?\.(?:css|js)", "Bootstrap", 1),
    (r"bulma@?(\d[\w.]*)?[^\s\"']*?bulma(?:\.min)?\.css|/bulma(?:\.min)?\.css", "Bulma", 1),
    (r"@picocss/pico@?(\d[\w.]*)?|/pico(?:\.classless)?(?:\.min)?\.css", "Pico", 1),
    (r"foundation(?:-sites)?@?(\d[\w.]*)?[^\s\"']*?foundation(?:\.min)?\.css", "Foundation", 1),
    (r"uikit@?(\d[\w.]*)?[^\s\"']*?uikit(?:\.min)?\.css", "UIkit", 1),
    (r"materialize(?:-css)?@?(\d[\w.]*)?[^\s\"']*?materialize(?:\.min)?\.css", "Materialize", 1),
]
STATIC_LIBS = [(r"jquery", "jQuery"), (r"alpinejs|/alpine(?:\.min)?\.js", "Alpine.js"), (r"htmx(?:\.org)?(?:@|/|\.min)", "htmx"),
               (r"font-?awesome|fontawesome", "Font Awesome"), (r"chart\.js|/chart(?:\.umd)?(?:\.min)?\.js", "Chart.js"),
               (r"bootstrap-icons", "Bootstrap Icons")]
SITE_TEMPLATE_EXT = {".md", ".njk", ".liquid", ".html", ".webc", ".hbs", ".mustache", ".ejs", ".pug", ".markdown"}


def site_generator(root: Path, deps: dict) -> str | None:
    if "@11ty/eleventy" in deps or any((root / n).is_file() for n in ("eleventy.config.js", "eleventy.config.mjs", "eleventy.config.cjs", ".eleventy.js")):
        return "Eleventy"
    if (root / "_config.yml").is_file() and ((root / "_layouts").is_dir() or (root / "_posts").is_dir() or "jekyll" in read(root / "Gemfile").lower()):
        return "Jekyll"
    if any((root / n).is_file() for n in ("hugo.toml", "hugo.yaml", "hugo.json")) or ((root / "config.toml").is_file() and (root / "layouts").is_dir() and (root / "content").is_dir()):
        return "Hugo"
    return None


def _site_files(root: Path) -> list[Path]:
    return [p for p in iter_files(root) if not ({x.lower() for x in p.relative_to(root).parts[:-1]} & SITE_SKIP)]


def front_matter(text: str) -> dict:
    """Simple keys of a page's front matter: YAML (`layout: post`) or Eleventy's `---js` object."""
    m = re.match(r"\s*---(js|json)?\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    body = m.group(2)
    if m.group(1):
        return {k: v for k, v in re.findall(r"\b(layout|permalink|title|tags)\s*[:=]\s*['\"`]([^'\"`]+)", body)}
    out = {}
    for k, v in re.findall(r"(?m)^([\w-]+)\s*:\s*(.*)$", body):
        out.setdefault(k, v.strip().strip("'\""))
    return out


def _page_title(text: str, fm: dict) -> str | None:
    title = fm.get("title")
    if not title:
        m = re.search(r"<title>\s*([^<{]+?)\s*</title>", text) or re.search(r"<h1[^>]*>\s*([^<{]+?)\s*</h1>", text) or re.search(r"(?m)^#\s+(.+)$", text)
        title = m.group(1) if m else None
    return (title[:57].rstrip() + "…" if len(title) > 58 else title) if title else None


def site_assets(root: Path, files: list[Path]) -> dict:
    """The kits and libraries a site loads from a CDN or keeps vendored, with versions where they show."""
    urls: list[str] = []
    for f in files:
        if f.suffix in SITE_TEMPLATE_EXT or f.suffix == ".htm":
            t = read(f, 200_000)
            urls += re.findall(r"<(?:link|script)\b[^>]*?(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", t)
    vendored = [rel(root, d) for base in ("vendor", "vendors", "lib", "libs", "assets/vendor", "assets/lib") if (root / base).is_dir()
                for d in sorted((root / base).iterdir()) if d.is_dir()]
    kits, libs = {}, []
    for pat, label, vg in STATIC_KITS:
        for u in urls + vendored:
            m = re.search(pat, u, re.I)
            if m:
                ver = next((g for g in m.groups() if g), None) if vg else None
                where = ("vendored" if u in vendored or re.match(r"(\./)?(vendor|vendors|lib|libs)/", u)
                         else "CDN" if re.match(r"(https?:)?//", u) else "local")
                if label not in kits or (ver and not kits[label][0]):
                    kits[label] = (ver, where, u)
    if "Bootstrap" in kits and not kits["Bootstrap"][0]:                  # a vendored copy names its version in its header
        for cand in [*root.glob("**/bootstrap*.css"), *root.glob("**/bootstrap*.js")]:
            if "node_modules" in cand.parts:
                continue
            vm = re.search(r"Bootstrap v(\d[\d.]*)", read(cand, 2_000))
            if vm:
                kits["Bootstrap"] = (vm.group(1), kits["Bootstrap"][1], kits["Bootstrap"][2])
                break
    for pat, label in STATIC_LIBS:
        if any(re.search(pat, u, re.I) for u in urls + vendored):
            libs.append(label)
    return {"kits": [(k, v, w) for k, (v, w, _) in kits.items()], "libs": libs}


def _element_at(text: str, i: int) -> str:
    """The outer HTML of the element whose start tag begins at text[i], nested same-name tags counted."""
    m = re.match(r"<([a-zA-Z][\w-]*)", text[i:])
    if not m:
        return ""
    tag, depth, j = m.group(1).lower(), 0, i
    for t in re.finditer(r"<(/?)" + re.escape(tag) + r"\b[^>]*>", text[i:], re.I):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return text[i:i + t.end()]
    return text[i:i + 4000]


def _chrome_blocks(text: str) -> dict[str, tuple[str, int, str]]:
    """The page's header, nav, sidebar and footer: label → (normalised markup, line, how to find it)."""
    out, raw = {}, {}
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    cands = [("header", r"<header\b"), ("footer", r"<footer\b"),
             ("sidebar", r"<(?:ul|div|nav|aside)\b[^>]*\b(?:id|class)\s*=\s*['\"][^'\"]*\bsidebar\b"),
             ("nav", r"<nav\b"), ("modal", r"<div\b[^>]*\bclass\s*=\s*['\"][^'\"]*\bmodal\b|<dialog\b")]
    for label, pat in cands:
        m = re.search(pat, body, re.I)
        if not m:
            continue
        el = _element_at(body, m.start())
        if any(el and el in outer for outer in raw.values()):       # a nav inside the header is the header's
            continue
        raw[label] = el
        head = re.match(r"<([a-zA-Z][\w-]*)([^>]*)>", el)
        ident = head.group(1).lower() if head else label
        if head:
            idm = re.search(r"\bid\s*=\s*['\"]([^'\"]+)", head.group(2))
            cm = re.search(r"\bclass\s*=\s*['\"]([^'\"]+)", head.group(2))
            ident += f"#{idm.group(1)}" if idm else (f".{'.'.join(cm.group(1).split()[:2])}" if cm else "")
        norm = _norm_chrome(el)
        line = text[: text.find(el[:80]) if el[:80] in text else m.start()].count("\n") + 1
        out[label] = (norm, line, ident)
    return out


CHROME_STATE = {"active", "show", "collapsed", "current", "is-active", "selected", "open"}


def _norm_chrome(el: str) -> str:
    """A block's markup with the page's own state set aside: which item is current, which menu is open."""
    def attr(m: re.Match) -> str:
        name, q, val = m.group(1), m.group(2), m.group(3)
        if name.lower() in {"aria-current", "aria-expanded", "aria-selected"}:
            return ""
        toks = [x for x in val.split() if name.lower() != "class" or x not in CHROME_STATE]
        return f" {name}={q}{' '.join(toks)}{q}"
    s = re.sub(r"\s+", " ", el)
    s = re.sub(r"\s+([\w:-]+)\s*=\s*([\"'])(.*?)\2", attr, s)
    return re.sub(r"\s*>\s*", ">", s)


def copied_chrome(root: Path, pages: list[Path]) -> list[str]:
    """Blocks repeated across hand-written pages: each is one edit per page, not one edit."""
    if len(pages) < 3:
        return []
    per: dict[str, list[tuple[Path, str, int, str]]] = collections.defaultdict(list)
    for p in pages:
        for label, (norm, line, ident) in _chrome_blocks(read(p, 300_000)).items():
            per[label].append((p, norm, line, ident))
    lines = []
    for label in ("sidebar", "header", "nav", "footer", "modal"):
        found = per.get(label, [])
        if len(found) < 3:
            continue
        groups = collections.Counter(norm for _, norm, _, _ in found)
        same = groups.most_common(1)[0][1]
        typical = [x for x in found if x[1] == groups.most_common(1)[0][0]]
        first = next((x for x in typical if x[0].name == "index.html"), typical[0])
        lines.append(f"the {label} `{first[3]}` is in {len(found)} of {len(pages)} pages"
                     + (", identical in all" if same == len(found) else f", identical in {same} once the current item is set aside" if same > 1 else ", different in each")
                     + f" (`{rel(root, first[0])}:{first[2]}`)")
    return lines


def _without_chrome(text: str) -> str:
    """A page less its header, nav, sidebar, footer and modals: what the page itself holds."""
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for _ in range(8):
        m = None
        for pat in (r"<header\b", r"<footer\b", r"<nav\b", r"<(?:ul|div|aside)\b[^>]*\b(?:id|class)\s*=\s*['\"][^'\"]*\bsidebar\b",
                    r"<div\b[^>]*\bclass\s*=\s*['\"][^'\"]*\bmodal\b"):
            m = re.search(pat, body, re.I)
            if m:
                el = _element_at(body, m.start())
                body = body[:m.start()] + body[m.start() + len(el):]
                break
        if not m:
            break
    return body


def static_pages(root: Path, files: list[Path], vocab_names: list[str]) -> tuple[Path, list[dict]]:
    """Hand-written pages: every .html under the site's root folder, with its route and title."""
    htmls = [p for p in files if p.suffix in {".html", ".htm"}]
    roots = [d for d in (root, root / "public", root / "src", root / "docs", root / "site", root / "www", root / "html") if (d / "index.html").is_file()]
    site = max(roots, key=lambda d: sum(1 for p in htmls if d in p.parents or p.parent == d), default=root)
    pages = []
    for p in sorted(htmls):
        if not (site in p.parents or p.parent == site):
            continue
        t = read(p, 300_000)
        if not re.search(r"<(?:html|body|head)\b", t, re.I):          # a fragment, not a page
            continue
        r_ = p.relative_to(site).as_posix()
        route = "/" + (r_[:-len("index.html")] if r_.endswith("index.html") else r_)
        css = [h for h in re.findall(r"<link\b[^>]*?href\s*=\s*['\"]([^'\"]+\.css)[^'\"]*['\"]", t) if not re.match(r"(https?:)?//", h)]
        own = _without_chrome(t)
        used = sorted(((n, _cls_uses(n, [own])) for n in vocab_names), key=lambda x: -x[1])
        pages.append({"file": rel(root, p), "lines": t.count("\n") + 1, "signals": _signals(own), "route": f"`{route}`",
                      "title": _page_title(t, {}), "classes": [f"{n} ×{c}" for n, c in used if c][:3], "components": [],
                      "renders": None, "template": None, "css": css[:3]})
    return site, pages


def _site_layout_file(base: Path, name: str) -> Path | None:
    for c in (base / name, *(base / f"{name}{e}" for e in (".njk", ".liquid", ".html", ".md", ".webc", ".hbs", ".11ty.js"))):
        if c.is_file():
            return c
    return None


def _layout_chain(base: Path, name: str | None, root: Path) -> list[Path]:
    chain, seen = [], set()
    while name and len(chain) < 5:
        f = _site_layout_file(base, name)
        if not f or f in seen:
            break
        seen.add(f)
        chain.append(f)
        name = front_matter(read(f, 50_000)).get("layout")
    return chain


def _template_code(text: str) -> str:
    """A template without its comments ({# #}, {% comment %}, <!-- -->)."""
    t = re.sub(r"\{#.*?#\}", "", text, flags=re.S)
    t = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "", t, flags=re.S)
    return re.sub(r"<!--.*?-->", "", t, flags=re.S)


def _includes_of(text: str) -> list[str]:
    found = re.findall(r"\{%-?\s*(?:include|render|includeCached)\s+['\"]?([\w./-]+?)['\"]?(?:\s|%)", _template_code(text))
    return [x for x in dict.fromkeys(found) if not x.endswith((".css", ".js"))]


def generator_site(root: Path, kind: str, files: list[Path], vocab_names: list[str]) -> dict:
    """Eleventy and Jekyll: the pages the templates make, their routes, the layout chain each sits in."""
    pages, layouts_used = [], collections.Counter()
    dirs: dict = {}
    if kind == "Eleventy":
        cfg = next((root / n for n in ("eleventy.config.js", "eleventy.config.mjs", "eleventy.config.cjs", ".eleventy.js") if (root / n).is_file()), None)
        ct = read(cfg) if cfg else ""
        dm = re.search(r"\bdir\s*:\s*\{", ct)
        d = dict(re.findall(r"(input|includes|layouts|data|output)\s*:\s*['\"]([^'\"]+)", block_after(ct, dm.start()))) if dm else {}
        for key, fn in (("input", "setInputDirectory"), ("includes", "setIncludesDirectory"), ("layouts", "setLayoutsDirectory"), ("data", "setDataDirectory"), ("output", "setOutputDirectory")):
            am = re.search(fn + r"\(\s*['\"]([^'\"]+)", ct)
            if am:
                d[key] = am.group(1)
        inp = Path(os.path.normpath(root / d.get("input", ".")))
        inc = Path(os.path.normpath(inp / d.get("includes", "_includes")))
        lay = Path(os.path.normpath(inp / d["layouts"])) if d.get("layouts") else inc
        data = Path(os.path.normpath(inp / d.get("data", "_data")))
        dirs = {"input": inp, "includes": inc, "layouts": lay, "data": data, "output": d.get("output", "_site"), "config": cfg}
        skip = {inc, lay, data, root / "node_modules", root / dirs["output"]}
        dir_data: dict[Path, dict] = {}
        for f in files:                                        # directory data: blog/blog.11tydata.js sets layout and tags for blog/
            if re.search(r"\.11tydata\.(js|cjs|mjs|json)$", f.name):
                t = read(f, 50_000)
                vals = dict(re.findall(r"['\"]?(layout|permalink)['\"]?\s*:\s*['\"]([^'\"]+)", t))
                tags = re.findall(r"['\"]?tags['\"]?\s*:\s*\[?\s*['\"]([^'\"]+)", t)
                if tags:
                    vals["tags"] = tags[0]
                dir_data[f.parent if f.name.split(".")[0] == f.parent.name or f.name.startswith(f.parent.name) else f] = vals
        for f in sorted(files):
            if f.suffix not in SITE_TEMPLATE_EXT or not (inp in f.parents or f.parent == inp) or any(s in f.parents for s in skip):
                continue
            if f.name.startswith("_") or re.search(r"\.11tydata\.", f.name):
                continue
            t = read(f, 200_000)
            fm = front_matter(t)
            inherited: dict = {}
            for anc in reversed([f.parent, *f.parent.parents]):
                if anc in dir_data:
                    inherited.update(dir_data[anc])
                if anc == inp.parent:
                    pass
            vals = {**inherited, **fm}
            if vals.get("permalink") in ("false", False):
                continue
            relp = f.relative_to(inp).with_suffix("")
            parts = list(relp.parts)
            if parts[-1] == "index" or (len(parts) > 1 and parts[-1] == parts[-2]):
                parts = parts[:-1]
            route = vals.get("permalink") or "/" + "/".join(parts) + ("/" if parts else "")
            if not route.startswith("/"):
                route = "/" + route
            if re.search(r"\.(xml|json|txt|xsl|rss|atom)$", route) or re.search(r"\.(xml|json|txt)\.\w+$", f.name):
                continue
            tags = [x for x in re.findall(r"['\"]([^'\"]+)['\"]", fm.get("tags", "")) or ([fm["tags"]] if fm.get("tags") else [])]
            if inherited.get("tags"):
                tags = [inherited["tags"]] + [x for x in tags if x != inherited["tags"]]
            vals["tags"] = ", ".join(tags) if tags else None
            chain = _layout_chain(lay, vals.get("layout"), root)
            for c in chain:
                layouts_used[c] += 1
            pages.append(_generator_page(root, f, t, route, chain, vals, vocab_names))
    elif kind == "Jekyll":
        cfg = read(root / "_config.yml")
        permalink = (re.search(r"(?m)^permalink:\s*(\S+)", cfg) or [None, "date"])[1]
        defaults = {}
        dm = re.search(r"(?ms)^defaults:\s*\n(.*?)(?=^\S)", cfg + "\nEND")
        if dm:
            for scope, layout in re.findall(r"type:\s*['\"]?(\w+)['\"]?.*?layout:\s*['\"]?([\w-]+)", dm.group(1), re.S):
                defaults[scope] = layout
        lay = root / "_layouts"
        dirs = {"input": root, "includes": root / "_includes", "layouts": lay, "data": root / "_data", "output": "_site", "config": root / "_config.yml"}
        for f in sorted(files):
            relp = f.relative_to(root)
            if f.suffix not in {".md", ".html", ".markdown"} or relp.parts[0] in {"_site", "_layouts", "_includes", "_sass", "_data", "vendor", "node_modules"}:
                continue
            t = read(f, 200_000)
            fm = front_matter(t)
            post = relp.parts[0] == "_posts"
            if not fm and not post:
                continue                                          # no front matter: Jekyll copies it as it is
            if relp.parts[0].startswith("_") and not post:
                continue
            if post:
                pm = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})-(.+)$", f.stem)
                slug = pm.group(4) if pm else f.stem
                pat = {"pretty": "/:year/:month/:day/:title/", "date": "/:year/:month/:day/:title.html", "none": "/:title.html"}.get(permalink, permalink)
                route = fm.get("permalink") or pat.replace(":title", slug).replace(":categories/", "").replace(":year", pm.group(1) if pm else "YYYY") \
                    .replace(":month", (pm.group(2) if pm else "MM").zfill(2)).replace(":day", (pm.group(3) if pm else "DD").zfill(2))
                layout = fm.get("layout") or defaults.get("posts")
            else:
                parts = list(relp.with_suffix("").parts)
                pretty = permalink == "pretty" or permalink.endswith("/")          # pages get folder routes too
                route = fm.get("permalink") or (("/" + "/".join(parts[:-1]) + "/").replace("//", "/") if parts[-1] == "index"
                                                else "/" + "/".join(parts) + ("/" if pretty else ".html"))
                layout = fm.get("layout") or defaults.get("pages")
            chain = _layout_chain(lay, layout, root)
            for c in chain:
                layouts_used[c] += 1
            pages.append(_generator_page(root, f, t, route, chain, fm, vocab_names))
    return {"pages": pages, "dirs": dirs, "layoutsUsed": layouts_used}


def _generator_page(root: Path, f: Path, t: str, route: str, chain: list[Path], vals: dict, vocab_names: list[str]) -> dict:
    body = re.sub(r"^\s*---.*?\n---", "", t, count=1, flags=re.S)
    used = sorted(((n, _cls_uses(n, [body])) for n in vocab_names), key=lambda x: -x[1])
    renders = None
    if chain:
        renders = {"name": " → ".join(rel(chain[0].parent.parent if chain[0].parent.name == "layouts" else chain[0].parent, c) for c in chain),
                   "file": rel(root, chain[0]), "lines": read(chain[0], 200_000).count("\n") + 1, "signals": [], "wrapper": True,
                   "holder": "`{{ content }}`"}
    sig = _signals(body)
    if vals.get("tags"):
        sig.append(f"tag `{vals['tags']}`")
    return {"file": rel(root, f), "lines": t.count("\n") + 1, "signals": sig, "route": f"`{route}`", "title": _page_title(t, vals),
            "classes": [f"{n} ×{c}" for n, c in used if c][:3], "components": _includes_of(body)[:4], "renders": renders, "template": None,
            "usesWord": "includes"}


def site_start(root: Path, src_files: list[Path], css_files: list[Path], stack: dict, deps: dict, vocab_names: list[str]) -> dict | None:
    """Start-here pieces for a site without a framework: its pages, what wraps them, where the styles are, how to serve it."""
    kind = site_generator(root, deps)
    files = _site_files(root)
    if not kind and not any(p.suffix in {".html", ".htm"} for p in files):
        return None
    assets = site_assets(root, files)
    before: list[str] = []
    layouts: list[dict] = []
    if kind in ("Eleventy", "Jekyll"):
        g = generator_site(root, kind, files, vocab_names)
        pages, dirs = g["pages"], g["dirs"]
        for lf, n in sorted(g["layoutsUsed"].items(), key=lambda kv: (-kv[1], str(kv[0]))):
            t = _template_code(read(lf, 200_000))
            parent = front_matter(t).get("layout")
            css = re.findall(r"<link\b[^>]*?href\s*=\s*['\"]([^'\"{]+\.css)", t) + re.findall(r"\{%-?\s*include\s+['\"]([^'\"]+\.css)['\"]", t)
            layouts.append({"file": rel(root, lf), "scopeText": f"wraps {n} page{'s' if n != 1 else ''}" + (f" (then sits in `{parent}`)" if parent else ""),
                            "css": css[:3], "fonts": [], "providers": [], "chrome": _includes_of(t)[:6]})
        where = {k: rel(root, v) for k, v in dirs.items() if isinstance(v, Path) and k != "config"}
        src = "the root" if where.get("input") in (".", "") else f"`{where.get('input')}/`"
        sass = [rel(root, f) for f in files if f.suffix in {".scss", ".sass"} and not f.name.startswith("_")
                and not ({x for x in f.relative_to(root).parts} & {"_sass", "node_modules"}) and re.match(r"\s*---", read(f, 200))]
        site_line = (f"{kind}: pages from {src}, layouts in `{where.get('layouts')}/`, includes in `{where.get('includes')}/`"
                     + (f", data in `{where.get('data')}/`" if (root / where.get("data", "_data")).is_dir() else "") + f", built into `{dirs.get('output')}/`"
                     + (f"; styles: {', '.join(f'`{s}`' for s in sass)}, which Jekyll compiles with the partials in `_sass/`" if kind == "Jekyll" and sass else ""))
        data_files = sorted(p.stem for p in (dirs["data"].glob("*") if dirs.get("data") and dirs["data"].is_dir() else []) if p.suffix in {".js", ".json", ".yml", ".yaml", ".cjs", ".mjs"})
        if data_files:
            before.append(f"site data: {', '.join(f'`{d}`' for d in data_files[:6])} (`{where.get('data')}/`) — titles, nav and metadata come from there, not the templates")
        if kind == "Eleventy":
            serve = "`npx @11ty/eleventy --serve` builds and serves on :8080"
        else:
            cfg = read(root / "_config.yml")
            listed = re.search(r"(?m)^(?:plugins|gems):\s*\n((?:[ \t]+-.*\n?)+)", cfg)          # the plugins _config.yml loads
            gems = re.findall(r"-\s*(jekyll-[\w-]+)", listed.group(1)) if listed else []
            serve = ("`bundle exec jekyll serve` builds and serves on :4000 (`bundle install` first)" if (root / "Gemfile").is_file()
                     else "no Gemfile: `gem install jekyll" + (" " + " ".join(gems) if gems else "") + " webrick kramdown-parser-gfm` (the last two for Ruby 3), then `jekyll serve` builds and serves on :4000")
        before.append(f"serve: {serve}; render the built page, not the template file")
        copies = []
    elif kind == "Hugo":
        pages, copies = [], []
        site_line = "Hugo: content in `content/`, templates in `layouts/` (and the theme's in `themes/<name>/layouts/`), built into `public/`"
        before.append("serve: `hugo server` builds and serves on :1313")
    else:
        site, pages = static_pages(root, files, vocab_names)
        copies = copied_chrome(root, [root / p["file"] for p in pages])
        where = rel(root, site) if site != root else "the root"
        builders = [n for n in ("gulpfile.js", "Gruntfile.js", "webpack.config.js", "vite.config.js", "vite.config.mjs") if (root / n).is_file()]
        scss = [rel(root, d) for d in (root / "scss", root / "sass", root / "src" / "scss", root / "assets" / "scss") if d.is_dir()]
        site_line = (f"static HTML: {len(pages)} page{'s' if len(pages) != 1 else ''} in {where if where == 'the root' else f'`{where}/`'}, no templates"
                     + (": shared markup is copied into each page" if copies else "")
                     + (f"; `{scss[0]}/` is compiled to CSS by `{builders[0]}`" if scss and builders else ""))
        before.append(f"serve the folder: `python3 -m http.server 8000`" + (f" in `{where}/`" if where != "the root" else "")
                      + " and render `http://localhost:8000/<page>.html` (a `file://` path works too, unless the pages link `/css/…` from the root)")
    kits = ", ".join(f"{k}{f' {v}' if v else ''} ({w})" for k, v, w in assets["kits"])
    return {"kind": kind or "static HTML", "siteLine": site_line, "kits": kits, "libs": assets["libs"], "pages": pages[:24],
            "routes": [], "layouts": layouts[:6], "stackBefore": before, "copies": copies}


# -------------------------------------------------------------------- Laravel
# A Laravel page is a Blade view a route names, directly (Route::view), through a controller that
# returns view('x.y'), as a Livewire page component, or as an Inertia page (a Vue or React file).
# What wraps it is an @extends chain or a layout component (<x-layouts::app>, <x-app-layout>);
# what guards it is the `auth` middleware on the route or its group.
FORTIFY_PATHS = {"loginView": "/login", "registerView": "/register", "requestPasswordResetLinkView": "/forgot-password",
                 "resetPasswordView": "/reset-password/{token}", "verifyEmailView": "/email/verify",
                 "confirmPasswordView": "/user/confirm-password", "twoFactorChallengeView": "/two-factor-challenge"}


def laravel_app(root: Path) -> dict | None:
    cj = root / "composer.json"
    if not (root / "artisan").is_file() or not cj.is_file():
        return None
    try:
        c = json.loads(read(cj))
    except json.JSONDecodeError:
        return None
    req = {**(c.get("require") or {}), **(c.get("require-dev") or {})}
    if "laravel/framework" not in req:
        return None
    psr4 = {**((c.get("autoload") or {}).get("psr-4") or {})}
    return {"version": req["laravel/framework"], "req": req, "psr4": psr4 or {"App\\": "app/"}, "scripts": c.get("scripts") or {}}


def _php_code(t: str) -> str:
    """PHP without comments; `#[Attribute]` and `//` inside strings are kept."""
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"(?<![:'\"\\w])//[^\n]*", "", t)
    return re.sub(r"(?m)^\s*#(?!\[)[^\n]*", "", t)


def _php_statements(body: str) -> list[str]:
    """Top-level statements: split at `;` outside strings and brackets."""
    out, cur, depth, quote, i = [], [], 0, None, 0
    while i < len(body):
        ch = body[i]
        cur.append(ch)
        if quote:
            if ch == "\\" and i + 1 < len(body):
                cur.append(body[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == ";" and depth == 0:
            out.append("".join(cur[:-1]).strip())
            cur = []
        i += 1
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return [s for s in out if s]


def _php_uses(code: str) -> dict[str, str]:
    """`use A\\B\\C;`, `use A\\B\\C as D;` and `use A\\{B, C};` → short name → full name."""
    out = {}
    for full, alias in re.findall(r"(?m)^\s*use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;", code):
        out[alias or full.split("\\")[-1]] = full
    for prefix, names in re.findall(r"(?m)^\s*use\s+([\w\\]+)\\\{([^}]*)\}\s*;", code):
        for n in names.split(","):
            n = n.strip()
            if n:
                full, _, alias = n.partition(" as ")
                out[(alias or full).strip().split("\\")[-1]] = prefix + "\\" + full.strip()
    return out


def _php_class_file(root: Path, app: dict, code: str, ref: str, namespace: str | None = None) -> Path | None:
    """The file of a class named in `code`: through its `use` imports and composer's PSR-4 map."""
    ref = ref.lstrip("\\")
    uses = _php_uses(code)
    head, _, rest = ref.partition("\\")
    full = (uses[head] + ("\\" + rest if rest else "")) if head in uses else (f"{namespace}\\{ref}" if namespace and not rest else ref)
    for prefix, base in sorted(app["psr4"].items(), key=lambda kv: -len(kv[0])):
        if full.startswith(prefix):
            bases = base if isinstance(base, list) else [base]
            for b in bases:
                f = root / b / (full[len(prefix):].replace("\\", "/") + ".php")
                if f.is_file():
                    return f
    return None


def blade_file(root: Path, name: str) -> Path | None:
    """A view name as a file: `settings.profile`, `pages::settings.profile` (a namespace folder), `livewire.counter`."""
    views = root / "resources" / "views"
    ns, _, rest = name.rpartition("::")
    path = rest.replace(".", "/")
    cands = ([views / ns / f"{path}.blade.php", views / ns / path / "index.blade.php"] if ns else []) \
        + [views / f"{path}.blade.php", views / path / "index.blade.php", views / "livewire" / f"{path}.blade.php",
           views / "components" / f"{path}.blade.php"]
    return next((c for c in cands if c.is_file()), None)


def _route_target(root: Path, app: dict, f: Path, code: str, method: str, args: list[str]) -> dict:
    """What a route shows: a view, a controller's view, a Livewire page, an Inertia page, or a redirect."""
    if method == "redirect" or method == "permanentRedirect":
        return {"redirect": _unquote(args[1]) if len(args) > 1 else None}
    if method == "view" and len(args) > 1:
        v = _unquote(args[1])
        return {"view": v, "file": blade_file(root, v) if v else None}
    if method in ("livewire",) or (method == "route" and len(args) > 1):              # Route::livewire / Volt::route
        v = _unquote(args[1]) if len(args) > 1 else None
        if v:
            return {"view": v, "file": blade_file(root, v), "livewire": True}
    if method == "inertia" and len(args) > 1:
        return {"inertia": _unquote(args[1])}
    if len(args) < 2:
        return {}
    target = args[1].strip()
    body = None
    cm = re.match(r"^\[\s*([\w\\]+)::class\s*,\s*['\"](\w+)['\"]\s*\]$", target)
    im = re.match(r"^([\w\\]+)::class$", target)
    if cm or im:
        cls, meth = (cm.group(1), cm.group(2)) if cm else (im.group(1), "__invoke")
        cf = _php_class_file(root, app, code, cls)
        if not cf:
            return {"controller": f"{cls}@{meth}"}
        ct = _php_code(read(cf, 300_000))
        if re.search(r"extends\s+(?:\\?Livewire\\)?Component\b", ct):          # a Livewire class page: its render()
            mm = re.search(r"function\s+render\s*\([^)]*\)[^{]*\{", ct)
            body = _balanced(ct, mm.end() - 1) if mm else ""
            v = re.search(r"\bview\(\s*['\"]([^'\"]+)", body)
            return {"view": v.group(1) if v else None, "file": blade_file(root, v.group(1)) if v else None, "livewire": True, "controller": rel(root, cf)}
        mm = re.search(r"function\s+" + re.escape(meth) + r"\s*\([^)]*\)[^{]*\{", ct)
        body = _balanced(ct, mm.end() - 1) if mm else ""
        out = {"controller": f"{rel(root, cf)}@{meth}", "controllerFile": cf, "controllerMiddleware": _controller_middleware(ct, meth)}
    elif target.startswith(("function", "fn")):
        body = target
        out = {}
    else:
        return {}
    v = re.search(r"\b(?:view|View::make)\(\s*['\"]([^'\"]+)", body or "")
    ir = re.search(r"Inertia::render\(\s*['\"]([^'\"]+)", body or "") or re.search(r"\binertia\(\s*['\"]([^'\"]+)", body or "")
    if v:
        out.update({"view": v.group(1), "file": blade_file(root, v.group(1))})
    elif ir:
        out["inertia"] = ir.group(1)
    return out


def _controller_middleware(ct: str, meth: str) -> list[str]:
    """Middleware a controller applies to one of its methods: in its constructor, its static middleware(), or an attribute."""
    out = []
    def names(s: str) -> list[str]:
        return [("auth" if (a or b) in ("Authenticate",) else (a or b)) for a, b in re.findall(r"['\"]([\w:.,-]+)['\"]|(\w+)::class", s)]
    def applies(tail: str) -> bool:     # ->only([...]), only: [...], or the older ['except' => [...]] argument
        only = re.search(r"only['\"]?\s*(?:=>|:|\()\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", tail)
        exc = re.search(r"except['\"]?\s*(?:=>|:|\()\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", tail)
        return (not only or meth in re.findall(r"['\"](\w+)['\"]", only.group(1))) and (not exc or meth not in re.findall(r"['\"](\w+)['\"]", exc.group(1)))
    for m in re.finditer(r"\$this->middleware\(([^;]*?)\)((?:\s*->\s*(?:only|except)\([^)]*\))*)\s*;", ct):
        args = _split_top(m.group(1))
        if applies(m.group(2) + " " + " ".join(args[1:])):
            out += names(args[0] if args else "")
    sm = re.search(r"static\s+function\s+middleware\s*\(\s*\)[^{]*\{", ct)
    if sm:
        for item in _split_top(_balanced(_balanced(ct, sm.end() - 1), _balanced(ct, sm.end() - 1).find("["))) if "[" in _balanced(ct, sm.end() - 1) else []:
            mw = re.match(r"(?:new\s+Middleware\(\s*)?(['\"][\w:.,-]+['\"]|\w+::class)(.*)", item.strip(), re.S)
            if mw and applies(mw.group(2)):
                out += names(mw.group(1))
    for m in re.finditer(r"#\[Middleware\(([^\]]*)\)\]", ct):
        out += names(m.group(1))
    return list(dict.fromkeys(out))


def laravel_routes(root: Path, app: dict) -> list[dict]:
    """GET routes from routes/web.php and the files it requires, with the middleware and prefix of their groups."""
    out: list[dict] = []

    def walk(f: Path, body: str, ctx: dict, code: str, depth: int) -> None:
        if depth > 6 or len(out) > 300:
            return
        for st in _php_statements(body):
            rq = re.match(r"^require(?:_once)?\s*\(?\s*__DIR__\s*\.\s*['\"]/?([^'\"]+)['\"]", st)
            if rq:
                g = Path(os.path.normpath(f.parent / rq.group(1)))
                if g.is_file():
                    gc = _php_code(read(g, 300_000))
                    walk(g, gc, ctx, gc, depth + 1)
                continue
            m = re.match(r"^(Route|Volt)::", st)
            if not m:
                continue
            gm = re.search(r"->group\(\s*(?:function\s*\([^)]*\)\s*(?:use\s*\([^)]*\)\s*)?|fn\s*\(\)\s*=>\s*)\{", st) \
                or re.search(r"->group\(\s*(?=['\"])", st)
            if gm:                                                 # a group: its middleware, prefix and controller, then its body
                head = st[:gm.start()]
                sub = dict(ctx)
                sub["middleware"] = ctx["middleware"] + _mw(head)
                pm = re.search(r"prefix\(\s*['\"]([^'\"]*)", head)
                if pm:
                    sub["prefix"] = "/".join(x for x in (ctx["prefix"].strip("/"), pm.group(1).strip("/")) if x)
                cm = re.search(r"controller\(\s*([\w\\]+)::class", head)
                if cm:
                    sub["controller"] = cm.group(1)
                if st[gm.end() - 1] == "{":
                    walk(f, _balanced(st, gm.end() - 1), sub, code, depth + 1)
                else:
                    gf = re.match(r"\s*['\"]([^'\"]+)", st[gm.end():])
                    g = (root / gf.group(1)) if gf else None
                    if g and g.is_file():
                        gc = _php_code(read(g, 300_000))
                        walk(g, gc, sub, gc, depth + 1)
                continue
            rm = re.match(r"^(?:Route|Volt)::(get|view|livewire|redirect|permanentRedirect|inertia|any|match|resource|route)\s*\(", st)
            if not rm:
                continue
            method = rm.group(1)
            args = _split_top(_balanced(st, rm.end() - 1))
            if method == "match":
                if "get" not in (args[0] if args else "").lower():
                    continue
                args = args[1:]
                method = "get"
            uri = _unquote(args[0]) if args else None
            if uri is None:
                continue
            if method == "resource":
                cls = args[1] if len(args) > 1 else ""
                for suffix, meth in (("", "index"), ("/create", "create"), ("/{id}", "show"), ("/{id}/edit", "edit")):
                    tgt = _route_target(root, app, f, code, "get", [args[0], f"[{cls.replace('::class', '')}::class, '{meth}']"])
                    out.append({"uri": _join_uri(ctx["prefix"], uri + suffix), "method": "get",
                                "middleware": list(dict.fromkeys(ctx["middleware"] + _mw(st[rm.end():]) + tgt.pop("controllerMiddleware", []))), **tgt})
                continue
            if ctx.get("controller") and len(args) > 1 and re.match(r"^['\"]\w+['\"]$", args[1].strip()):
                args = [args[0], f"[{ctx['controller']}::class, {args[1]}]"]
            tgt = _route_target(root, app, f, code, method, args)
            out.append({"uri": _join_uri(ctx["prefix"], uri), "method": method,
                        "middleware": list(dict.fromkeys(ctx["middleware"] + _mw(st[rm.end():]) + tgt.pop("controllerMiddleware", []))), **tgt})

    web = root / "routes" / "web.php"
    if web.is_file():
        code = _php_code(read(web, 300_000))
        walk(web, code, {"middleware": [], "prefix": "", "controller": None}, code, 0)
    prov = next((p for p in (root / "app" / "Providers").glob("*.php") if "Fortify::" in read(p, 100_000)), None) if (root / "app" / "Providers").is_dir() else None
    if prov:                                                       # Fortify registers the sign-in pages itself
        pt = _php_code(read(prov, 100_000))
        for fn, path in FORTIFY_PATHS.items():
            m = re.search(r"Fortify::" + fn + r"\(\s*(?:fn\s*\(\)\s*=>|function\s*\(\)\s*\{\s*return)\s*view\(\s*['\"]([^'\"]+)", pt)
            if m:
                out.append({"uri": path, "method": "get", "middleware": ["guest"], "view": m.group(1), "file": blade_file(root, m.group(1)), "fortify": True})
    return out


def _mw(chain: str) -> list[str]:
    """Middleware named in a route or group chain: ->middleware(['auth', 'verified']) or Route::middleware('auth')."""
    out = []
    for arg in re.findall(r"middleware\(\s*(\[[^\]]*\]|['\"][^'\"]+['\"]|[\w\\]+::class)", chain):
        out += re.findall(r"['\"]([^'\"]+)['\"]", arg) or [re.sub(r"::class$", "", arg).split("\\")[-1]]
    return [("auth" if x in ("Authenticate", "auth:sanctum", "auth:web") else x) for x in out]


def _join_uri(prefix: str, uri: str) -> str:
    return "/" + "/".join(x for x in (prefix.strip("/"), uri.strip("/")) if x)


def blade_layout(root: Path, app: dict, view: Path) -> list[tuple[str, Path]]:
    """The layout chain a view sits in: @extends('layouts.app'), or a layout component around it."""
    chain, seen, cur = [], set(), view
    while cur and cur not in seen and len(chain) < 5:
        seen.add(cur)
        t = read(cur, 200_000)
        body = re.sub(r"\{\{--.*?--\}\}", "", re.sub(r"<\?php.*?\?>", "", t, flags=re.S), flags=re.S)
        m = re.search(r"@extends\(\s*['\"]([^'\"]+)", body)
        if m:
            nxt, label = blade_file(root, m.group(1)), m.group(1)
        else:
            lm = re.match(r"\s*(?:@\w+[^\n]*\n\s*)*<x-([\w.:-]+)", body)       # the outermost tag is a component: a layout
            if not lm or not re.search(r"layout", lm.group(1), re.I):
                lay = re.search(r"#\[Layout\(\s*['\"]([^'\"]+)", t) or re.search(r"->layout\(\s*['\"]([^'\"]+)", t)
                if not lay:
                    break
                nxt, label = blade_file(root, lay.group(1)), lay.group(1)
            else:
                label = lm.group(1)
                nxt = blade_component_file(root, app, label)
        if not nxt:
            break
        chain.append((label, nxt))
        cur = nxt
    return chain


def blade_component_file(root: Path, app: dict, tag: str) -> Path | None:
    """<x-app-layout> → a class in app/View/Components (its render() names the view) or components/app-layout.blade.php;
    <x-layouts.app> → components/layouts/app.blade.php; <x-layouts::app> → the `layouts` namespace folder."""
    views = root / "resources" / "views"
    if "::" in tag:
        ns, _, rest = tag.partition("::")
        return next((c for c in (views / ns / f"{rest.replace('.', '/')}.blade.php", views / ns / rest.replace(".", "/") / "index.blade.php",
                                 views / "components" / ns / f"{rest.replace('.', '/')}.blade.php") if c.is_file()), None)
    path = tag.replace(".", "/")
    cls = root / "app" / "View" / "Components" / ("/".join(_pascal(p) for p in path.split("/")) + ".php")
    if cls.is_file():
        v = re.search(r"\bview\(\s*['\"]([^'\"]+)", read(cls, 50_000))
        if v and blade_file(root, v.group(1)):
            return blade_file(root, v.group(1))
    return next((c for c in (views / "components" / f"{path}.blade.php", views / "components" / path / "index.blade.php",
                             views / "components" / path / f"{path.split('/')[-1]}.blade.php") if c.is_file()), None)


def blade_components(root: Path, views: list[Path]) -> list[dict]:
    """Anonymous components (resources/views/components) and class components, by how many views use them."""
    comp_dir = root / "resources" / "views" / "components"
    comps: dict[str, dict] = {}
    for f in sorted(comp_dir.rglob("*.blade.php")) if comp_dir.is_dir() else []:
        tag = f.relative_to(comp_dir).as_posix()[: -len(".blade.php")].replace("/", ".")
        if tag.endswith(".index"):
            tag = tag[: -len(".index")]
        props = re.search(r"@props\(\s*\[(.*?)\]\s*\)", read(f, 50_000), re.S)
        names = [re.match(r"\s*['\"]?([\w-]+)", x).group(1) for x in _split_top(props.group(1)) if re.match(r"\s*['\"]?[\w-]+", x)] if props else []
        comps[tag] = {"tag": f"x-{tag}", "file": f, "props": names[:7]}
    for f in sorted((root / "app" / "View" / "Components").rglob("*.php")) if (root / "app" / "View" / "Components").is_dir() else []:
        parts = f.relative_to(root / "app" / "View" / "Components").with_suffix("").parts
        tag = ".".join(re.sub(r"(?<!^)(?=[A-Z])", "-", p).lower() for p in parts)
        ct = _php_code(read(f, 50_000))
        cm = re.search(r"function\s+__construct\s*\(", ct)
        names = re.findall(r"\$(\w+)", _balanced(ct, cm.end() - 1)) if cm else []
        comps.setdefault(tag, {"tag": f"x-{tag}", "file": f, "props": names[:7]})
    counts: collections.Counter = collections.Counter()
    for v in views:
        t = read(v, 200_000)
        for tag in dict.fromkeys(re.findall(r"<x-([\w.:-]+)", t)):
            if tag in comps and comps[tag]["file"] != v:
                counts[tag] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{**comps[t], "views": n} for t, n in ranked]


def laravel_start(root: Path, src_files: list[Path], css_files: list[Path], deps: dict) -> dict:
    app = laravel_app(root) or {"req": {}, "psr4": {"App\\": "app/"}, "version": "?", "scripts": {}}
    req = app["req"]
    routes = laravel_routes(root, app)
    views = [p for p in src_files if p.name.endswith(".blade.php")]
    pages: list[dict] = []
    by_file: dict[Path, list[dict]] = {}
    for r in routes:
        if r.get("file"):
            by_file.setdefault(r["file"], []).append(r)
    lw_cfg = read(root / "config" / "livewire.php")
    lw_major = int((re.search(r"(\d+)", req.get("livewire/livewire", "")) or [0, "0"])[1])
    lw_default = (re.search(r"['\"](?:component_layout|layout)['\"]\s*=>\s*['\"]([^'\"]+)", lw_cfg) or [None, "layouts::app" if lw_major >= 4 else "components.layouts.app"])[1]
    for vf, rs in by_file.items():
        t = read(vf, 200_000)
        chain = blade_layout(root, app, vf)
        if not chain and any(r.get("livewire") for r in rs):
            lf = blade_file(root, lw_default) or blade_component_file(root, app, lw_default)
            if lf:
                chain = [(lw_default, lf)] + blade_layout(root, app, lf)
        body = re.sub(r"<\?php.*?\?>", "", t, flags=re.S)
        tags = list(dict.fromkeys(re.findall(r"<(x-[\w.:-]+|flux:[\w.-]+|livewire:[\w.-]+)", body)))
        tags = [x for x in tags if not chain or x != f"x-{chain[0][0]}"]
        tags += [f"@include {i}" for i in dict.fromkeys(re.findall(r"@include(?:If|When)?\(\s*['\"]([^'\"]+)", body))][:2]
        signals = _signals(body)
        mw = sorted({m for r in rs for m in r["middleware"]})
        kind = "Livewire page" if any(r.get("livewire") for r in rs) else "Fortify view" if any(r.get("fortify") for r in rs) else None
        renders = {"name": " → ".join(lbl for lbl, _ in chain), "file": rel(root, chain[0][1]), "lines": read(chain[0][1], 200_000).count("\n") + 1,
                   "signals": [], "wrapper": True, "holder": "`@yield`" if "@extends" in body else "`{{ $slot }}`"} if chain else None
        pages.append({"file": rel(root, vf), "lines": t.count("\n") + 1, "signals": signals + ([kind] if kind else []) + ([f"middleware {', '.join(mw)}"] if mw else []),
                      "route": ", ".join(f"`{u}`" for u in dict.fromkeys(r["uri"] for r in rs)), "classes": [], "components": tags[:6],
                      "renders": renders, "template": None})
    pages.sort(key=lambda p: p["file"])
    shown = []
    for r in routes:
        if r.get("redirect") is not None:
            shown.append((r["uri"], f"`{r['redirect']}` (redirect)"))
        elif r.get("view"):
            shown.append((r["uri"], f"view `{r['view']}`" + (" (Livewire)" if r.get("livewire") else "")))
        elif r.get("inertia"):
            shown.append((r["uri"], f"Inertia `{r['inertia']}`"))

    layouts = []
    seen: collections.Counter = collections.Counter()
    for pg in pages:
        if pg["renders"]:
            seen[pg["renders"]["file"]] += 1
    for lf, n in seen.most_common(6):
        t = read(root / lf, 200_000)
        vite = re.search(r"@vite\(\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", t)
        layouts.append({"file": lf, "scopeText": f"wraps {n} page{'s' if n != 1 else ''}",
                        "css": re.findall(r"['\"]([^'\"]+\.(?:css|scss))['\"]", vite.group(1)) if vite else [], "fonts": [], "providers": [],
                        "chrome": list(dict.fromkeys(re.findall(r"<(x-[\w.:-]+|flux:[\w.-]+|livewire:[\w.-]+)", t)))[:6]
                        + [f"@include {i}" for i in dict.fromkeys(re.findall(r"@include\(\s*['\"]([^'\"]+)", t))][:3]})
    before = []
    guarded = [r["uri"] for r in routes if "auth" in r["middleware"] and (r.get("file") or r.get("inertia"))]
    if guarded:
        login = next((r["uri"] for r in routes if r["uri"] in ("/login", "/signin") or r.get("view", "").endswith("login")), "/login")
        before.append(f"the `auth` middleware guards {', '.join(f'`{u}`' for u in guarded[:4])}" + (f" and {len(guarded) - 4} more" if len(guarded) > 4 else "")
                      + f": a render there needs a signed-in session. Sign in once on `{login}` with `--act` and `--save-state`, then render with `--storage-state`"
                      + " (a fresh install has no users: register one, or `php artisan tinker`)")
    inertia = [r for r in routes if r.get("inertia")]
    if inertia:
        pdir = next((d for d in (root / "resources" / "js" / "pages", root / "resources" / "js" / "Pages") if d.is_dir()), None)
        first = inertia[0]["inertia"] or "?"
        found = next((f for f in ((pdir / f"{first}{e}") for e in (".vue", ".tsx", ".jsx", ".svelte")) if pdir and f.is_file()), None)
        before.append(f"Inertia: {len(inertia)} route{'s render' if len(inertia) != 1 else ' renders'} a Vue or React page from `{rel(root, pdir) if pdir else 'resources/js/pages'}/` "
                      f"(`{first}` → `{rel(root, found) if found else first + '.vue / .tsx'}`): those pages are components, read them as a Vue or React project")
    vite_css = [c for lay in layouts for c in lay["css"]]
    head = next((p for p in views if "@vite" in read(p, 100_000)), None)
    if head:
        before.append(f"`{rel(root, head)}` loads its assets through `@vite`: run `npm run dev` beside the server (or `npm run build` once) — without either the page fails with *Vite manifest not found*")
    env = root / ".env"
    if not env.is_file():
        before.append("first run: `cp .env.example .env`, `php artisan key:generate`, then the database (`touch database/database.sqlite` and `php artisan migrate` with the default SQLite)")
    dev = app["scripts"].get("dev")
    before.append(("`composer run dev` starts the project's dev processes together (the server and Vite at least); " if dev else "")
                  + "`php artisan serve` listens on :8000 unless `--port` says otherwise")
    kit = None
    if "livewire/flux" in req or "livewire/flux-pro" in req:
        counts: collections.Counter = collections.Counter()
        for v in views:
            counts.update(re.findall(r"<(flux:[\w.-]+)", read(v, 200_000)))
        kit = {"name": "Flux", "components": counts.most_common(12)}
    mode = ", ".join(x for x in ("Livewire " + re.sub(r"[^\d.]", "", req["livewire/livewire"]).split(".")[0] if "livewire/livewire" in req else "",
                                 "Inertia" if "inertiajs/inertia-laravel" in req else "", "Filament" if "filament/filament" in req else "",
                                 "Fortify" if "laravel/fortify" in req else "") if x)
    return {"pages": pages[:24], "routes": shown[:30], "layouts": layouts, "stackBefore": before,
            "used": [{**u, "file": rel(root, u["file"])} for u in blade_components(root, views)[:10]], "kit": kit,
            "router": "Blade" + (f"; {mode}" if mode else "") + "; routes in `routes/web.php`",
            "version": re.sub(r"[^\d.]", "", app["version"]).split(".")[0] if app["version"] != "?" else None}


# ------------------------------------------------------------- React route tables
# A React app names its pages in a route table: objects (useRoutes, createBrowserRouter, a RouteObject[]),
# <Route> elements (v6 element=, v5 component=), or umi's config/routes.ts. Each route is followed to the
# file that renders it, through lazy imports and barrels, with the layout and guards around it.
JS_EXTS = ("", ".tsx", ".ts", ".jsx", ".js", ".vue", "/index.tsx", "/index.ts", "/index.jsx", "/index.js", "/index.vue",
           # React Native's platform files, after the plain ones: `Foo.web.tsx` stands in where there is no `Foo.tsx`
           ".web.tsx", ".web.ts", ".native.tsx", ".native.ts", ".ios.tsx", ".android.tsx", ".web.js", ".native.js", ".ios.js", ".android.js",
           "/index.web.tsx", "/index.native.tsx", "/index.ios.tsx", "/index.android.tsx")
ROUTE_NOT_PAGES = {"Suspense", "Outlet", "Fragment", "React.Fragment", "ErrorBoundary", "StrictMode", "Navigate", "Redirect", "Switch",
                   "Routes", "Route", "DelayedMount"}
GUARD_NAME = re.compile(r"Guard|Protected|Private|Require|Authenticated|Authorized|Auth(?:Route|Wrapper|Check)?$")


def _js_resolve(root: Path, from_file: Path, spec: str, aliases: list) -> Path | None:
    """A local import's file, for a React or Vue app: relative, a tsconfig alias, `@/` or `~/`, or from the root or src/."""
    hit = _ng_resolve(root, from_file, spec, aliases, JS_EXTS)
    if hit is None and re.match(r"^[@~]/", spec):
        for base in ("src", "app"):
            hit = _ng_resolve(root, from_file, f"{base}/{spec[2:]}", [], JS_EXTS)
            if hit:
                break
    return hit


def _js_source_of(root: Path, f: Path, code: str, name: str | None, aliases: list, depth: int = 0) -> Path | None:
    """Where a component a routes file names is defined: a lazy import, an import (through barrels), or the file itself."""
    if not name or depth > 3:
        return None
    parts = name.split(".")
    base = parts[0]
    ns = re.search(r"import\s*\*\s*as\s+" + re.escape(base) + r"\s+from\s*['\"]([^'\"]+)['\"]", code) if len(parts) > 1 else None
    if ns:                                                   # import * as Scenes; Scenes.Drafts.Component
        g = _js_resolve(root, f, ns.group(1), aliases)
        return _js_source_of(root, g, _no_comments(read(g, 300_000)), ".".join(parts[1:]), aliases, depth + 1) if g else None
    m = re.search(r"(?:const|let|var)\s+" + re.escape(base) + r"\s*=\s*[^;]{0,160}?\bimport\(\s*['\"]([^'\"]+)['\"]", code)
    if m:
        return _js_resolve(root, f, m.group(1), aliases)
    for names, spec in re.findall(r"import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", code):
        for part in names.split(","):
            bits = [x.strip() for x in part.split(" as ")]
            if bits[-1] == base:
                g = _js_resolve(root, f, spec, aliases)
                return (_ng_defines(root, g, bits[0], aliases, exts=JS_EXTS) or g) if g else None
    m = re.search(r"import\s+" + re.escape(base) + r"\s*(?:,\s*\{[^}]*\})?\s+from\s*['\"]([^'\"]+)['\"]", code)
    if m:
        return _js_resolve(root, f, m.group(1), aliases)
    if re.search(r"(?:const|let|var|function|class)\s+" + re.escape(base) + r"\b", code):
        return f
    return None


def _js_array_of(root: Path, f: Path, code: str, name: str, aliases: list, depth: int = 0) -> tuple[Path, str, str] | None:
    """The array literal a name holds: declared in this file, or imported (through barrels)."""
    m = re.search(r"(?:const|let|var)\s+" + re.escape(name) + r"\b[^=\n]*=\s*\[", code)
    if m:
        return f, code, _balanced(code, m.end() - 1)
    m = re.search(r"export\s+default\s+\[", code) if name == "default" else None
    if m:
        return f, code, _balanced(code, m.end() - 1)
    if depth >= 3:
        return None
    src = _js_source_of(root, f, code, name, aliases)
    if src and src != f:
        c2 = _no_comments(read(src, 300_000))
        found = _js_array_of(root, src, c2, name, aliases, depth + 1)
        if found:
            return found
        dm = re.search(r"export\s+default\s+(\w+)\s*;?\s*$", c2, re.M)       # const routes = [...]; export default routes
        if dm and dm.group(1) != name:
            return _js_array_of(root, src, c2, dm.group(1), aliases, depth + 1)
    return None


def _jsx_tags(jsx: str) -> list[str]:
    return [t for t in re.findall(r"<([A-Z][\w.]*)", jsx) if t not in ROUTE_NOT_PAGES]


def _join_route(prefix: str, path: str) -> str:
    if path.startswith("/"):
        return path
    return "/" + "/".join(x for x in (prefix.strip("/"), path.strip("/")) if x)


def _route_path(v: str | None) -> str:
    """A path attribute or field: a string, a template literal with ${…} shown as {…}, or a call shown as {call}."""
    if not v:
        return ""
    v = v.strip()
    if v.startswith("{") and v.endswith("}"):
        v = v[1:-1].strip()
    s = _unquote(v)
    if s is not None:
        return re.sub(r"\$\{\s*([^}]*?)\s*\}", r"{\1}", s)
    return "{" + v[:40] + "}"


def _layout_rec(root: Path, f: Path, code: str, name: str | None, aliases: list) -> dict | None:
    if not name:
        return None
    lf = _js_source_of(root, f, code, name, aliases)
    return {"name": name, "file": lf}


def _react_walk(root: Path, f: Path, code: str, body: str, prefix: str, layout: dict | None, guards: list[str],
                aliases: list, out: list[dict], depth: int) -> None:
    if depth > 6 or len(out) > 200:
        return
    for el in _split_top(body):
        if el.startswith("..."):                                 # ...authRoutes
            found = _js_array_of(root, f, code, el[3:].strip(), aliases)
            if found:
                _react_walk(root, *found, prefix, layout, guards, aliases, out, depth + 1)
            continue
        if not el.startswith("{"):
            continue
        fl = _fields(_balanced(el, 0))
        path = _route_path(fl.get("path"))
        lay_prefix = _unquote(fl.get("layout")) or ""                 # { layout: '/admin', path: '/default' }: a menu table
        if lay_prefix.startswith("/") and path:                        # the menu's layout path always prefixes the route's
            full = _join_route(prefix, lay_prefix.rstrip("/") + "/" + path.lstrip("/"))
        else:
            full = _join_route(prefix, path) if path else (prefix or "/")
        elem = fl.get("element") or ""
        comps = _jsx_tags(elem)
        for key in ("Component", "component"):
            c = (fl.get(key) or "").strip()
            if c:
                comps += _jsx_tags(c) if "<" in c else [c] if re.match(r"^[A-Z][\w.]*$", c) else []
        g = guards + [c for c in comps if GUARD_NAME.search(c)]
        comps = [c for c in comps if not GUARD_NAME.search(c)]
        nav = re.search(r"<Navigate\b[^>]*\bto=\{?\s*['\"`]([^'\"`]+)", elem)
        kids = fl.get("children") or (fl.get("items") if (fl.get("items") or "").startswith("[") else None)
        if kids:
            lay = _layout_rec(root, f, code, comps[0], aliases) if comps else layout
            if kids.startswith("["):
                _react_walk(root, f, code, _balanced(kids, 0), full, lay, g, aliases, out, depth + 1)
            else:
                found = _js_array_of(root, f, code, kids.strip(), aliases)
                if found:
                    _react_walk(root, *found, full, lay, g, aliases, out, depth + 1)
            continue
        rec = {"path": full, "name": None, "file": None, "layout": layout, "guards": list(dict.fromkeys(g)), "redirect": None}
        if nav:
            rec["redirect"] = nav.group(1)
        elif comps:
            rec["name"] = comps[-1]
            rec["file"] = _js_source_of(root, f, code, comps[-1], aliases)
            if len(comps) > 1:                                     # <AuthLayout><SignInPage /></AuthLayout>
                rec["layout"] = _layout_rec(root, f, code, comps[0], aliases)
        elif fl.get("lazy"):                                       # lazy: () => import('./routes/x')
            lm = re.search(r"import\(\s*['\"]([^'\"]+)['\"]", fl["lazy"])
            rec["file"] = _js_resolve(root, f, lm.group(1), aliases) if lm else None
            rec["name"] = rec["file"].stem if rec["file"] else None
        else:
            continue
        out.append(rec)


def _jsx_attrs(code: str, i: int) -> tuple[str, int, bool]:
    """The attributes of the JSX tag whose name ends at i, where the tag ends, and whether it closes itself."""
    depth, quote, j = 0, None, i
    while j < len(code):
        ch = code[j]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"`" and depth:
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ">" and depth == 0:
            return code[i:j], j + 1, code[j - 1] == "/"
        j += 1
    return code[i:], len(code), True


def _jsx_attr(attrs: str, name: str) -> str | None:
    m = re.search(r"(?<![\w-])" + name + r"\s*=\s*", attrs)
    if not m:
        return None
    rest = attrs[m.end():]
    if rest[:1] in "'\"":
        end = rest.find(rest[0], 1)
        return rest[:end + 1]
    if rest[:1] == "{":
        return "{" + _balanced(rest, 0) + "}"
    return None


def _jsx_routes(root: Path, f: Path, code: str, aliases: list, out: list[dict]) -> None:
    """<Route path element|component|render> in JSX, nested <Route>s joined to their parent's path and layout."""
    stack: list[tuple[str, dict | None, list[str]]] = []
    for m in re.finditer(r"<(/?)Route\b(?![\w.])", code):
        if m.group(1):
            if stack:
                stack.pop()
            continue
        attrs, _end, closed = _jsx_attrs(code, m.end())
        prefix, layout, guards = stack[-1] if stack else ("", None, [])
        path = _route_path(_jsx_attr(attrs, "path"))
        index = re.search(r"(?<![\w-])index(?![\w-])", attrs) is not None
        full = _join_route(prefix, path) if path else (prefix or "/")
        comps = []
        for key in ("element", "render", "component", "Component"):
            v = _jsx_attr(attrs, key)
            if v:
                inner = v[1:-1].strip() if v.startswith("{") else v
                comps += _jsx_tags(inner) if "<" in inner else [inner] if re.match(r"^[A-Z][\w.]*$", inner) else []
        g = guards + [c for c in comps if GUARD_NAME.search(c)]
        comps = [c for c in comps if not GUARD_NAME.search(c)]
        if not closed:                                   # a parent route: a layout for the routes inside it
            lay = _layout_rec(root, f, code, comps[0], aliases) if comps else layout
            stack.append((full, lay, g))
            continue
        if not comps or not (path or index):
            continue
        out.append({"path": full, "name": comps[-1], "file": _js_source_of(root, f, code, comps[-1], aliases),
                    "layout": _layout_rec(root, f, code, comps[0], aliases) if len(comps) > 1 else layout,
                    "guards": list(dict.fromkeys(g)), "redirect": None})


def _umi_routes(root: Path, aliases: list) -> list[dict]:
    """umi / Ant Design Pro: config/routes.ts, or `routes:` in .umirc.ts or config/config.ts."""
    out: list[dict] = []
    for name in ("config/routes.ts", "config/routes.js", ".umirc.ts", ".umirc.js", "config/config.ts", "config/config.js"):
        f = root / name
        if not f.is_file():
            continue
        code = _no_comments(read(f, 300_000))
        m = re.search(r"export\s+default\s+\[", code) if "routes" in f.stem else re.search(r"\broutes\s*:\s*\[", code)
        if not m:
            continue

        def walk(body: str, prefix: str, layout: bool, guards: list[str], depth: int) -> None:
            for el in _split_top(body):
                if not el.startswith("{") or depth > 6:
                    continue
                fl = _fields(_balanced(el, 0))
                path = _unquote(fl.get("path")) or ""
                full = _join_route(prefix, path) if path else prefix or "/"
                g = guards + ([f"access {_unquote(fl['access'])}"] if _unquote(fl.get("access")) else []) \
                    + [f"wrapper {Path(w).stem}" for w in re.findall(r"['\"]([^'\"]+)['\"]", fl.get("wrappers") or "")]
                lay = layout and fl.get("layout") != "false"
                comp = _unquote(fl.get("component"))
                if fl.get("routes", "").startswith("["):
                    walk(_balanced(fl["routes"], 0), full, lay, g, depth + 1)
                    continue
                if _unquote(fl.get("redirect")):
                    out.append({"path": full, "name": None, "file": None, "layout": None, "guards": g, "redirect": _unquote(fl["redirect"])})
                    continue
                if comp:
                    spec = comp if comp.startswith("@") else "src/pages/" + comp.lstrip("./")
                    target = _js_resolve(root, root / "src" / "pages" / "x", spec, aliases)
                    out.append({"path": full, "name": Path(comp).name, "file": target, "guards": g, "redirect": None,
                                "layout": {"name": "the umi layout (ProLayout)", "file": None} if lay else None})

        walk(_balanced(code, m.end() - 1), "", True, [], 0)
        if out:
            return out
    return out


def react_route_table(root: Path, src_files: list[Path], deps: dict) -> dict:
    """The route table of a React app that is not Next.js: routes with their files, layouts and guards."""
    aliases = ts_aliases(root)
    out: list[dict] = []
    kind = None
    if "@umijs/max" in deps or "umi" in deps:
        out = _umi_routes(root, aliases)
        kind = "umi (`config/routes.ts`)" if out else None
    if not out:
        for p in src_files:
            if p.suffix not in {".tsx", ".jsx", ".ts", ".js"} or re.search(r"\.(test|spec|stories)$", p.stem):
                continue
            code = read(p, 300_000)
            if not re.search(r"createBrowserRouter|createHashRouter|createMemoryRouter|useRoutes\(|<Route\b", code):
                continue
            code = _no_comments(code)
            for m in re.finditer(r"\b(?:createBrowserRouter|createHashRouter|createMemoryRouter|useRoutes)\(\s*", code):
                rest = code[m.end():]
                if rest.startswith("["):
                    _react_walk(root, p, code, _balanced(rest, 0), "", None, [], aliases, out, 0)
                else:
                    nm = re.match(r"[\w$]+", rest)
                    found = _js_array_of(root, p, code, nm.group(0), aliases) if nm else None
                    if found:
                        _react_walk(root, *found, "", None, [], aliases, out, 0)
                kind = kind or "objects"
            if "<Route" in code:
                n0 = len(out)
                _jsx_routes(root, p, code, aliases, out)
                if len(out) > n0:
                    kind = kind or "<Route> elements"
    if not out or all(r["path"].endswith("/*") for r in out if r["file"]):
        for p in src_files:                                    # a menu table: routes.js with { layout, path, component }
            if p.stem.lower() not in {"routes", "router", "route", "routeconfig", "menu", "menus"} or p.suffix not in {".tsx", ".jsx", ".ts", ".js"}:
                continue
            code = _no_comments(read(p, 300_000))
            for m in re.finditer(r"(?:const|let|var)\s+(\w+)\s*(?::[^=\n]+)?=\s*\[", code):
                body = _balanced(code, m.end() - 1)
                if re.search(r"\bpath\s*:", body) and re.search(r"\b(?:component|element|Component)\s*:", body):
                    n0 = len(out)
                    _react_walk(root, p, code, body, "", None, [], aliases, out, 0)
                    kind = kind or f"a route table in `{rel(root, p)}`" if len(out) > n0 else kind
    mounts = [(r["path"][:-2], r) for r in out if r["path"].endswith("/*") and r["path"] != "/*" and r["file"]]
    for r in out:                                              # /admin/* → AdminLayout holds /admin/default
        if not r["layout"] and not r["path"].endswith("/*"):
            for pre, mr in mounts:
                if r["path"].startswith(pre + "/"):
                    r["layout"] = {"name": mr["name"], "file": mr["file"]}
                    break
    out = [r for r in out if not (r["path"].endswith("/*") and r["path"] != "/*" and r["file"] and mounts)]
    for r in out:                                              # scenes/Login/index.ts: export { default } from "./Login"
        f = r["file"]
        for _ in range(3):
            if not f or f.suffix not in {".ts", ".js"}:
                break
            dm = re.search(r"export\s*\{\s*default(?:\s+as\s+\w+)?\s*\}\s*from\s*['\"]([^'\"]+)['\"]", read(f, 20_000))
            nxt = _js_resolve(root, f, dm.group(1), aliases) if dm else None
            if not nxt:
                break
            f = nxt
        r["file"] = f
    seen, routes = set(), []
    for r in out:
        key = (r["path"], str(r["file"]), r["redirect"])
        if key not in seen:
            seen.add(key)
            routes.append(r)
    return {"routes": routes, "kind": kind}


# ---------------------------------------------------------------- component kits
# MUI, Chakra, Ant Design, styled-components / Emotion, CSS Modules, Element Plus and Vuetify keep the look
# in a theme object, not in utility classes: where it is, its values, the kit's components by use, how the
# code styles itself, and how dark mode switches. A match task builds with these, not with new colours.
KIT_INFRA = {"ThemeProvider", "CssBaseline", "StyledEngineProvider", "ChakraProvider", "ColorModeScript", "ConfigProvider", "App",
             "GlobalStyles", "CssVarsProvider", "InitColorSchemeScript", "Global", "ColorModeProvider", "Provider", "LocaleProvider"}
KIT_DEFAULT_PRIMARY = {"MUI": "#1976d2", "Chakra UI": "blue.500 #3182ce", "Ant Design": "#1677ff", "Element Plus": "#409eff",
                       "Vuetify": "#1867c0"}
COLOR_LIT = r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)"


def _code_files(src_files: list[Path], exts=(".ts", ".tsx", ".js", ".jsx", ".mjs")) -> list[Path]:
    return [p for p in src_files if p.suffix in exts and not re.search(r"\.(test|spec|stories|d)$", p.stem)]


def _react_kit_uses(src_files: list[Path], pkgs: tuple[str, ...]) -> list[tuple[str, int]]:
    """A React kit's components, counted by the files that import them (`import { Button } from 'antd'`, `@mui/material/Button`)."""
    counts: collections.Counter = collections.Counter()
    for p in _code_files(src_files, (".tsx", ".jsx", ".ts", ".js")):
        t = read(p, 200_000)
        if not any(k in t for k in pkgs):
            continue
        names = set()
        for body, spec in re.findall(r"import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", t):
            if any(spec == k or spec.startswith(k + "/") for k in pkgs):
                for part in body.split(","):
                    n = part.strip().split(" as ")[0].strip()
                    if re.match(r"^[A-Z]\w+$", n) and n not in KIT_INFRA and not re.search(r"(Props|Classes|Theme|Options|Type|Ref)$", n):
                        names.add(n)
        for n, spec in re.findall(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", t):
            if any(spec.startswith(k + "/") for k in pkgs):
                last = spec.rsplit("/", 1)[-1]
                if re.match(r"^[A-Z]\w+$", last) and last not in KIT_INFRA:
                    names.add(last)
        counts.update(sorted(names))              # sorted: ties keep one order from run to run
    return counts.most_common(12)


def _vue_kit_uses(src_files: list[Path], prefix: str) -> list[tuple[str, int]]:
    """A Vue kit's components, counted by the templates that use them: <el-button> or <ElButton> → el-button."""
    counts: collections.Counter = collections.Counter()
    kebab = re.compile(r"<(" + prefix + r"-[a-z][a-z0-9-]*)")
    pascal = re.compile(r"<(" + prefix.capitalize() + r"[A-Z]\w*)")
    for p in src_files:
        if p.suffix not in {".vue", ".tsx", ".jsx"}:
            continue
        t = read(p, 200_000)
        tags = set(kebab.findall(t)) | {re.sub(r"(?<!^)(?=[A-Z])", "-", x).lower() for x in pascal.findall(t)}
        counts.update(sorted(tags))
    return counts.most_common(12)


def _obj_block(code: str, key: str) -> str | None:
    """The body of `key: { … }` (the first one), braces balanced."""
    m = re.search(r"(?<![\w$])['\"]?" + re.escape(key) + r"['\"]?\s*:\s*\{", code)
    return _balanced(code, m.end() - 1) if m else None


def _lit(v: str | None) -> str | None:
    """A literal value: a string's content, or a number."""
    if v is None:
        return None
    s = _unquote(v)
    if s is not None:
        return s
    return v.strip() if re.match(r"^-?[\d.]+$", v.strip()) else None


def _theme_files(src_files: list[Path], pat: str, in_theme_dir: str | None = None) -> list[Path]:
    out = []
    for p in _code_files(src_files):
        t = read(p, 200_000)
        dirs = {x.lower() for x in p.parts[:-1]}
        if re.search(pat, t) or (in_theme_dir and dirs & {"theme", "themes", "styles"} and re.search(in_theme_dir, t)):
            out.append(p)
    return out


def mui_theme(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    if not any(k in deps for k in ("@mui/material", "@mui/joy")):
        return None
    files = _theme_files(src_files, r"\b(?:createTheme|extendTheme|experimental_extendTheme)\s*\(",
                         r"\bmain\s*:\s*['\"]#|\bpalette\b|\bcolorSchemes\b|\bMui[A-Z]\w+\s*:\s*\{")
    code = "\n".join(_no_comments(read(p, 200_000)) for p in files)
    colors = []
    for role in ("primary", "secondary", "info", "success", "warning", "error"):
        for m in re.finditer(r"(?<![\w$])" + role + r"\s*:\s*\{", code):
            mm = re.search(r"\bmain\s*:\s*['\"]([^'\"]+)['\"]", _balanced(code, m.end() - 1))
            if mm:
                colors.append((role, mm.group(1)))
                break
    bg = _obj_block(code, "background") or ""
    extra = [(f"background {k}", _lit(v)) for k, v in _fields(bg).items() if k in ("default", "paper") and _lit(v)]
    txt = next((b for b in (_obj_block(code, "text"),) if b and "primary" in b), "") or ""
    extra += [(f"text {k}", _lit(v)) for k, v in _fields(txt).items() if k in ("primary", "secondary") and _lit(v) and re.match(COLOR_LIT, _lit(v) or "")]
    schemes = []
    cs = _obj_block(code, "colorSchemes")
    if cs is not None:
        schemes = [k for k in ("light", "dark") if re.search(r"(?<![\w$])" + k + r"\s*[:,}]", cs)]
    mode = re.search(r"\bmode\s*:\s*['\"](light|dark)['\"]", code)
    toggled = re.search(r"\bmode\s*:\s*(?:\w+\s*\?|\w+\s*,|\w+\s*\})", code) is not None or re.search(r"\bmode\s*,", code) is not None
    radius = re.search(r"shape\s*:\s*\{\s*borderRadius\s*:\s*([\d.]+)", code)
    fonts = []
    for m in re.finditer(r"fontFamily\s*:\s*(\{[^}]*\}|(['\"`])(?:(?!\2).)+\2)", code):
        v = m.group(1)
        strs = re.findall(r"(['\"`])((?:(?!\1).)+)\1", v) if v.startswith("{") else [(m.group(2), v[1:-1])]
        for _q, s2 in strs:
            fam = s2.split(",")[0].strip().strip("'\"")
            if fam and not fam.startswith("$") and fam not in fonts:
                fonts.append(fam)
    overrides = list(dict.fromkeys(re.findall(r"\b(Mui[A-Z][A-Za-z]+)\s*:\s*\{", code)
                                   + re.findall(r"(?:const|let)\s+(Mui[A-Z][A-Za-z]+)\s*[:=]", code)))
    selector = re.search(r"colorSchemeSelector\s*:\s*['\"]([^'\"]+)['\"]", code)
    uses = _react_kit_uses(src_files, ("@mui/material", "@mui/lab", "@mui/joy"))
    sx = sum(1 for p in _code_files(src_files, (".tsx", ".jsx")) if "sx={" in read(p, 200_000))
    styled = sum(1 for p in _code_files(src_files) if re.search(r"\bstyled\(", read(p, 200_000)))
    setter = next((rel(root, p) for p in _code_files(src_files, (".tsx", ".jsx", ".ts", ".js"))
                   if re.search(r"\buseColorScheme\(\)", read(p, 200_000))), None)
    valued = [p for p in files if re.search(r"\bmain\s*:\s*['\"]|\bcreateTheme\s*\(|\bextendTheme\s*\(", read(p, 200_000))]
    return {"kit": "MUI", "version": deps.get("@mui/material") or deps.get("@mui/joy"),
            "files": [rel(root, p) for p in valued or files][:3], "colors": colors + extra, "schemes": schemes,
            "mode": mode.group(1) if mode else None, "toggled": toggled, "radius": radius.group(1) if radius else None,
            "fonts": fonts[:4], "overrides": overrides[:14], "overridesCount": len(overrides),
            "selector": selector.group(1) if selector else None, "uses": uses, "setter": setter,
            "styling": ", ".join(x for x in (f"`sx` in {sx} files" if sx else "", f"`styled()` in {styled}" if styled else "") if x)}


def chakra_theme(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    v = deps.get("@chakra-ui/react")
    if not v:
        return None
    major = int((re.findall(r"\d+", v) or ["2"])[0])
    files = _theme_files(src_files, r"\b(?:extendTheme|createSystem|defineConfig|extendBaseTheme)\s*\(",
                         r"@chakra-ui|\bcolors\s*:\s*\{|\bcomponents\s*:\s*\{")
    code = "\n".join(_no_comments(read(p, 200_000)) for p in files)
    scales = []
    for m in re.finditer(r"(?<![\w$])colors\s*:\s*\{", code):
        for name, val in _fields(_balanced(code, m.end() - 1)).items():
            if not val.startswith("{"):
                continue
            steps = dict(re.findall(r"(\d{2,3})\s*:\s*(?:\{\s*value\s*:\s*)?['\"](#[0-9a-fA-F]{3,8})['\"]", val))
            if steps:
                mid = steps.get("500") or steps[sorted(steps, key=int)[len(steps) // 2]]
                if name not in [s for s, _ in scales]:
                    scales.append((name, mid))
    fonts = []
    fb = _obj_block(code, "fonts")
    if fb:
        fonts += [(_lit(v) or "").split(",")[0].strip("'\" ") for v in _fields(fb).values() if _lit(v)]
    fonts += [m.split(",")[0].strip() for m in re.findall(r"fontFamily\s*:\s*['\"]([^'\"]+)['\"]", code)]
    overrides = []
    for m in re.finditer(r"(?<![\w$])components\s*:\s*\{", code):
        overrides += [k for k in _fields(_balanced(code, m.end() - 1)) if re.match(r"^[A-Z]", k)]
    init = re.search(r"initialColorMode\s*:\s*['\"](\w+)", code)
    system = re.search(r"useSystemColorMode\s*:\s*(true)", code)
    mode_files = sum(1 for p in _code_files(src_files, (".tsx", ".jsx", ".js", ".ts"))
                     if re.search(r"\buseColorModeValue\(|\buseColorMode\(\)", read(p, 200_000)))
    return {"kit": "Chakra UI", "version": v, "major": major, "files": [rel(root, p) for p in files][:4], "scales": scales[:10],
            "fonts": list(dict.fromkeys(f for f in fonts if f))[:3], "overrides": list(dict.fromkeys(overrides))[:14],
            "initial": init.group(1) if init else None, "system": bool(system), "modeFiles": mode_files,
            "uses": _react_kit_uses(src_files, ("@chakra-ui/react",))}


def antd_theme(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    v = deps.get("antd")
    if not v:
        return None
    cands = list(dict.fromkeys(_code_files(src_files) + [f for f in (root / "config" / "config.ts", root / "config" / "defaultSettings.ts",
                                                                    root / ".umirc.ts", root / "config" / "config.js", root / ".umirc.js") if f.is_file()]))
    tokens, files, comps, algos = [], [], [], set()
    for p in cands:
        t = read(p, 200_000)
        if "token" not in t and "Algorithm" not in t and "colorPrimary" not in t:
            continue
        code = _no_comments(t)
        hit = False
        for m in re.finditer(r"(?<![\w$])token\s*:\s*\{", code):
            for k, val in _fields(_balanced(code, m.end() - 1)).items():
                lv = _lit(val)
                if lv and k not in [x for x, _ in tokens]:
                    tokens.append((k, lv))
                    hit = True
        cm = re.search(r"theme\s*:\s*\{[\s\S]{0,400}?(?<![\w$])components\s*:\s*\{", code)
        if cm:
            comps += [k for k in _fields(_balanced(code, cm.end() - 1)) if re.match(r"^[A-Z]", k)]
            hit = True
        for a in re.findall(r"\b(dark|compact)Algorithm\b", code):
            algos.add(a)
            hit = True
        if p.name.startswith("defaultSettings"):                   # Ant Design Pro's ProLayout settings
            for k in ("colorPrimary", "navTheme", "layout"):
                mm = re.search(r"(?<![\w$])" + k + r"\s*:\s*['\"]([^'\"]+)['\"]", code)
                if mm and k not in [x for x, _ in tokens]:
                    tokens.append((k, mm.group(1)))
                    hit = True
        if hit and rel(root, p) not in files:
            files.append(rel(root, p))
    styling = []
    n_style = sum(1 for p in _code_files(src_files) if re.search(r"\bcreateStyles\(|\buseStyles\(|antd-style", read(p, 200_000)))
    if n_style:
        styling.append(f"`createStyles` (antd-style) in {n_style} files")
    less = [c for c in iter_files(root) if c.suffix == ".less"]
    if less:
        styling.append(f"{len(less)} `.less` file" + ("s" if len(less) != 1 else ""))
    fonts = [x.split(",")[0].strip() for k2, x in tokens if k2 == "fontFamily"]
    return {"kit": "Ant Design", "version": v, "files": files[:4], "tokens": tokens[:12], "components": list(dict.fromkeys(comps))[:10], "fonts": fonts,
            "algorithms": sorted(algos), "pro": "@ant-design/pro-components" in deps or "@ant-design/pro-layout" in deps,
            "uses": _react_kit_uses(src_files, ("antd", "@ant-design/pro-components", "@ant-design/pro-layout", "@ant-design/pro-table",
                                                "@ant-design/pro-form")),
            "styling": ", ".join(styling)}


def styled_theme(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    libs = [k for k in ("styled-components", "@emotion/styled", "@emotion/react") if k in deps]
    if not libs:
        return None
    code_files = _code_files(src_files, (".tsx", ".jsx", ".ts", ".js"))
    styled_files, globals_, theme_keys = [], [], collections.Counter()
    direct = ("styled-components", "@emotion/styled", "@emotion/react", "@emotion/css")
    for p in code_files:
        t = read(p, 200_000)
        if not any(f"'{k}'" in t or f'"{k}"' in t for k in direct):
            continue
        styled_files.append(p)
        if re.search(r"\bcreateGlobalStyle\b|<Global\b", t):
            globals_.append(rel(root, p))
        theme_keys.update(re.findall(r"\btheme\.(\w+)", t))
    kit_engine = any(k in deps for k in ("@mui/material", "@mui/joy", "@chakra-ui/react"))
    if not styled_files or (kit_engine and "styled-components" not in deps and len(styled_files) < 5):
        return None                                             # Emotion as MUI's or Chakra's engine, not the project's own
    best, best_n = None, 0
    for p in code_files:                                      # the theme: the styles/theme file with the most colour literals
        dirs = {x.lower() for x in p.parts[:-1]}
        if not (dirs & {"theme", "themes", "styles", "style"} or re.search(r"theme", p.stem, re.I)):
            continue
        t = _no_comments(read(p, 200_000))
        n = len(re.findall(r"['\"](?:" + COLOR_LIT + r")['\"]", t))
        if n > best_n:
            best, best_n = p, n
    colors, darks = [], []
    if best:
        t = _no_comments(read(best, 200_000))
        for k, val in re.findall(r"(?<![\w$])([A-Za-z_]\w*)\s*:\s*['\"](" + COLOR_LIT + r")['\"]", t):
            if k not in [x for x, _ in colors]:
                colors.append((k, val))
        used = {k for k, _ in theme_keys.most_common(20)}
        semantic = re.compile(r"accent|primary|secondary|brand|danger|error|warning|success|info|text|background|surface|border|link", re.I)
        colors.sort(key=lambda kv: (kv[0] not in used, not semantic.search(kv[0]), len(kv[0])))
        darks = list(dict.fromkeys(re.findall(r"(?:const|function|let)\s+(\w*[Dd]ark\w*)", t)))
    return {"kit": " / ".join("styled-components" if k == "styled-components" else "Emotion" for k in libs if k != "@emotion/react"
                              or "@emotion/styled" not in libs) or "Emotion",
            "files": len(styled_files), "globals": globals_[:3], "theme": rel(root, best) if best else None,
            "colors": colors[:12], "darkThemes": darks[:3], "themeKeys": theme_keys.most_common(8)}


def css_modules(root: Path, src_files: list[Path], css_files: list[Path]) -> dict | None:
    mods = [c for c in css_files if re.search(r"\.module\.(?:css|scss|sass|less)$", c.name)]
    if len(mods) < 2:
        return None
    importers = []
    for p in _code_files(src_files, (".tsx", ".jsx", ".ts", ".js")):
        m = re.search(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+\.module\.(?:css|scss|sass|less))['\"]", read(p, 200_000))
        if m:
            importers.append((p, m.group(2)))
    example = next(((rel(root, p), spec) for p, spec in importers if p.stem.lower() not in {"page", "index", "layout"}), None) \
        or ((rel(root, importers[0][0]), importers[0][1]) if importers else None)
    glob = [rel(root, c) for c in css_files if ".module." not in c.name and re.search(r":root\s*\{[^}]*--", read(c))]
    return {"modules": len(mods), "importers": len(importers), "example": example, "globals": glob[:2]}


def element_theme(root: Path, src_files: list[Path], css_files: list[Path], deps: dict) -> dict | None:
    v = deps.get("element-plus")
    if not v:
        return None
    code = "\n".join(read(p, 200_000) for p in _code_files(src_files, (".ts", ".js", ".mjs", ".vue")))
    default_css = re.search(r"element-plus/(?:dist/index\.css|theme-chalk/index\.css|theme-chalk/src/index\.scss)", code) is not None
    dark_vars = re.search(r"element-plus/theme-chalk/dark/css-vars\.css", code) is not None
    colors = []
    for c in css_files:                                        # --el-color-primary in :root, or the SCSS map passed to @forward
        t = read(c)
        for k, val in re.findall(r"--el-color-(primary|success|warning|danger|error|info)\s*:\s*([^;}\n]+)", t):
            if k not in [x for x, _ in colors]:
                colors.append((k, val.strip()))
        for k, val in re.findall(r"['\"](primary|success|warning|danger|error|info)['\"]\s*:\s*\(\s*['\"]base['\"]\s*:\s*(#[0-9a-fA-F]{3,8})", t):
            if k not in [x for x, _ in colors]:
                colors.append((k, val))
    runtime = next((rel(root, p) for p in _code_files(src_files, (".ts", ".js", ".vue"))
                    if re.search(r"setProperty\(\s*[`'\"]--el-color-|--el-color-\$\{", read(p, 200_000))
                    or re.search(r"--el-color-primary", read(p, 200_000)) and "setProperty" in read(p, 200_000)), None)
    loc = re.search(r"element-plus/(?:es|lib|dist)/locale/lang/([\w-]+)", code)
    size = re.search(r"use\(\s*ElementPlus\s*,\s*\{[^}]*\bsize\s*:\s*['\"](\w+)", code)
    return {"kit": "Element Plus", "version": v, "defaultCss": default_css, "darkVars": dark_vars, "colors": colors[:6],
            "runtime": runtime, "locale": loc.group(1) if loc else None, "size": size.group(1) if size else None,
            "uses": _vue_kit_uses(src_files, "el")}


def vuetify_theme(root: Path, src_files: list[Path], deps: dict) -> dict | None:
    v = deps.get("vuetify")
    if not v:
        return None
    files = _theme_files(src_files, r"\bcreateVuetify\s*\(|ThemeDefinition", None)
    code = "\n".join(_no_comments(read(p, 200_000)) for p in files)
    default = re.search(r"defaultTheme\s*:\s*['\"]([\w-]+)['\"]", code)
    themes = []
    for m in re.finditer(r"(?:const|let)\s+(\w+)\s*(?::\s*ThemeDefinition)?\s*=\s*\{", code):
        body = _balanced(code, m.end() - 1)
        if re.search(r"(?<![\w$])colors\s*:\s*\{", body):
            dark = re.search(r"(?<![\w$])dark\s*:\s*(true|false)", body)
            cols = [(k, _lit(val)) for k, val in _fields(_obj_block(body, "colors") or "").items()
                    if k in ("primary", "secondary", "error", "warning", "info", "success", "surface", "background") and _lit(val)]
            themes.append({"name": m.group(1), "dark": dark.group(1) == "true" if dark else False, "colors": cols[:8]})
    tb = _obj_block(code, "themes")
    if tb:                                                     # themes: { light: { dark: false, colors: {...} } } inline
        for k, val in _fields(tb).items():
            if val.startswith("{") and k not in [t["name"] for t in themes]:
                body = _balanced(val, 0)
                dark = re.search(r"(?<![\w$])dark\s*:\s*(true|false)", body)
                cols = [(kk, _lit(vv)) for kk, vv in _fields(_obj_block(body, "colors") or "").items()
                        if kk in ("primary", "secondary", "error", "surface", "background") and _lit(vv)]
                themes.append({"name": k, "dark": dark.group(1) == "true" if dark else k == "dark", "colors": cols[:8]})
    defaults = []
    db = _obj_block(code, "defaults")
    if db:
        for comp, val in _fields(db).items():
            if val.startswith("{"):
                inner = ", ".join(f"{k} {_lit(x)}" for k, x in _fields(_balanced(val, 0)).items() if _lit(x))
                if inner:
                    defaults.append(f"{comp} {inner}")
    switch = next((rel(root, p) for p in _code_files(src_files, (".ts", ".js", ".vue"))
                   if re.search(r"theme\.global\.name(?:\.value)?\s*=|\.change\(\s*['\"`]?\w|theme\.global\.name\.value\s*===", read(p, 200_000))), None)
    return {"kit": "Vuetify", "version": v, "files": [rel(root, p) for p in files][:3], "default": default.group(1) if default else None,
            "themes": themes[:4], "defaults": defaults[:8], "switch": switch, "uses": _vue_kit_uses(src_files, "v")}


def runtime_routes(root: Path, src_files: list[Path]) -> str | None:
    """Routes added at runtime from a menu the backend sends (RuoYi, vue-element-admin): a new page needs a server-side entry."""
    adders = [p for p in _code_files(src_files, (".ts", ".js", ".vue", ".tsx", ".jsx")) if re.search(r"\brouter\.addRoutes?\(", read(p, 200_000))]
    if not adders:
        return None
    api = None
    for p in _code_files(src_files):
        m = re.search(r"export\s+(?:const|function|async\s+function)\s+(\w*(?:[Rr]outers?|[Rr]outes|[Mm]enus?)\w*)[\s\S]{0,300}?url\s*:\s*['\"`]([^'\"`]+)",
                      read(p, 200_000))
        if m:
            api = (m.group(1), m.group(2), rel(root, p))
            break
    return (f"routes are also added at runtime: `{rel(root, adders[0])}` calls `router.addRoute`"
            + (f" with the menu the backend returns (`{api[0]}` → `{api[1]}` in `{api[2]}`); those pages are loaded by the menu's "
               "`component` names, so a new page also needs a menu entry on the server, and without the backend only the static routes render"
               if api else ""))


def hash_history(root: Path, src_files: list[Path]) -> str | None:
    """A router on hash history serves every page at /#/<route>: a render of /dashboard shows the home page."""
    for p in _code_files(src_files, (".ts", ".js", ".tsx", ".jsx", ".mjs")):
        t = read(p, 200_000)
        if re.search(r"\bcreateWebHashHistory\(|\bcreateHashRouter\(|<HashRouter\b", t):
            return f"`{rel(root, p)}` routes on the URL's hash: render `http://localhost:PORT/#/<route>`, not `/<route>`"
    return None


def kit_start(root: Path, src_files: list[Path], css_files: list[Path], deps: dict) -> dict:
    """Every kit the project styles itself with, read."""
    found = [k for k in (mui_theme(root, src_files, deps), chakra_theme(root, src_files, deps), antd_theme(root, src_files, deps),
                         element_theme(root, src_files, css_files, deps), vuetify_theme(root, src_files, deps)) if k]
    return {"kits": found, "styled": styled_theme(root, src_files, deps), "modules": css_modules(root, src_files, css_files)}


def _theme_storage_key(root: Path, src_files: list[Path]) -> str | None:
    """The localStorage key an app keeps its theme choice under: getItem('theme'), or a THEME_STORAGE_KEY constant."""
    for p in _code_files(src_files, (".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue")):
        t = read(p, 200_000)
        if "localStorage" not in t and "Storage" not in t:
            continue
        m = re.search(r"localStorage\.(?:get|set)Item\(\s*['\"]([^'\"]*(?:theme|mode|scheme)[^'\"]*)['\"]", t, re.I) \
            or re.search(r"(?:const|let)\s+\w*THEME\w*KEY\w*\s*=\s*['\"]([\w.:-]+)['\"]", t)
        if m:
            return m.group(1)
    return None


def kit_dark(k: dict, root: Path, src_files: list[Path]) -> tuple[str | None, bool | None]:
    """How the kit's dark mode switches: (the theme line, whether there is a dark mode at all); (None, None) when no kit says."""
    for kit in k["kits"]:
        name = kit["kit"]
        if name == "MUI":
            if "dark" in kit["schemes"]:
                sel = kit["selector"]
                where = ("`.dark` on `<html>`" if sel == "class" else "`[data-dark]` on `<html>`" if sel == "data"
                         else f"`[{sel}=dark]` on `<html>`" if sel and sel.startswith("data-") else f"`{sel}`" if sel
                         else "the OS scheme (`prefers-color-scheme`) until one is chosen")
                return (f"MUI's dark color scheme applies under {where} — `{kit['files'][0]}`; "
                        + (f"`useColorScheme()` in `{kit['setter']}` switches it and keeps" if kit["setter"] else "`useColorScheme()` keeps")
                        + " the choice in localStorage `mui-mode`: render dark with `--dark-storage mui-mode=dark`", True)
            if kit["toggled"] or kit["mode"] == "dark":
                key = _theme_storage_key(root, src_files)
                return (f"MUI's `palette.mode` is chosen in JS (`{kit['files'][0]}`)"
                        + (f"; the app keeps the choice in localStorage `{key}`: render dark with `--dark-storage {key}=dark`" if key
                           else ": render dark through the app's own switch"), True)
            return (None, False)
        if name == "Chakra UI" and kit["major"] < 3 and (kit["modeFiles"] or kit["initial"] == "dark" or kit["system"]):
            return (f"Chakra's color mode (`useColorModeValue` or `useColorMode` in {kit['modeFiles']} files; starts `{kit['initial'] or 'light'}`"
                    + (", follows the OS" if kit["system"] else "") + "): kept in localStorage `chakra-ui-color-mode`, shown as `.chakra-ui-dark` "
                    "on `<body>` and `data-theme` on `<html>`: render dark with `--dark-storage chakra-ui-color-mode=dark`", True)
        if name == "Ant Design":
            if "dark" in kit["algorithms"]:
                return ("Ant Design's `darkAlgorithm`, switched in JS by the app: render dark through the app's own switch", True)
            return (None, False)
        if name == "Vuetify":
            darks = [t["name"] for t in kit["themes"] if t["dark"]]
            if not darks:
                return (None, False)
            key = _theme_storage_key(root, src_files)
            return (f"Vuetify's theme `{darks[0]}` (dark) beside `{kit['default'] or 'light'}`"
                    + (f", switched in `{kit['switch']}`" if kit["switch"] else "")
                    + (f"; the app keeps the choice in localStorage `{key}`: render dark with `--dark-storage {key}=dark`" if key else ""), True)
    st = k.get("styled")
    if st and st["darkThemes"]:
        key = _theme_storage_key(root, src_files)
        return (f"a dark theme (`{st['darkThemes'][0]}` in `{st['theme']}`) goes to the `ThemeProvider` at runtime"
                + (f"; the app keeps the choice in localStorage `{key}`: render dark with `--dark-storage {key}=dark`" if key
                   else ": render dark through the app's own switch"), True)
    return (None, None)


KIT_MATCH = {
    "MUI": "A match task builds with these and the theme's values (`color=\"primary\"`, `sx={{ color: 'text.secondary', borderRadius: 1 }}`), not hex values or pixel radii.",
    "Chakra UI": "A match task builds with these and the theme's scales (`colorScheme`, `color=\"brand.500\"`, `useColorModeValue` for both modes), not hex values.",
    "Ant Design": "A match task builds with these and the theme's tokens (`theme.useToken()`), not hand-picked colours.",
    "Element Plus": "A match task builds with these (`type=\"primary\"`, `size`), not hand-rolled controls; colours come from the `--el-color-*` variables.",
    "Vuetify": "A match task builds with these and the theme's colours (`color=\"primary\"`, `bg-surface`), not hex values; the defaults apply to every instance.",
}


def md_kit_lines(k: dict) -> list[str]:
    """Start-here lines: each kit's components by use, how the code styles itself, and what a match task builds with."""
    out = []
    for kit in k.get("kits") or []:
        if kit.get("uses"):
            word = "templates" if kit["kit"] in ("Element Plus", "Vuetify") else "files"
            pro = " (with Pro components: pages start from `PageContainer`)" if kit.get("pro") else ""
            out.append(f"- {kit['kit']}{pro} — its components by use (counted by the {word} that use them): "
                       + " · ".join(f"{n} ×{c}" for n, c in kit["uses"])
                       + (f"; styled through {kit['styling']}" if kit.get("styling") else "") + ". " + KIT_MATCH[kit["kit"]])
    st = k.get("styled")
    if st:
        keys = " · ".join(f"{n} ×{c}" for n, c in st["themeKeys"])
        out.append(f"- {st['kit']} in {st['files']} files" + (f" (global styles in {', '.join(f'`{g}`' for g in st['globals'])})" if st["globals"] else "")
                   + (f"; they read the theme as `theme.x`, most used: {keys}" if keys else "")
                   + ". A new component is a styled component that takes its colours from the theme, not literals.")
    mo = k.get("modules")
    if mo:
        ex = f" (e.g. `{mo['example'][0]}` imports `{mo['example'][1]}`)" if mo["example"] else ""
        out.append(f"- CSS Modules: {mo['modules']} `.module.*` files, imported by {mo['importers']} components{ex}. A new component gets its own module"
                   + (f"; colours and spacing come from the variables in {', '.join(f'`{g}`' for g in mo['globals'])}, not literals" if mo["globals"] else "")
                   + ". The class names are local to each module, so the vocabulary below leaves them out.")
    return out


def md_kit_tokens(k: dict) -> list[str]:
    """Declared-tokens sections for the kits' themes."""
    out = []
    for kit in k.get("kits") or []:
        name = kit["kit"]
        if name == "MUI":
            out.append(f"### MUI theme" + (" — " + ", ".join(f"`{f}`" for f in kit["files"]) if kit["files"] else ""))
            if kit["colors"]:
                out.append("- palette: " + " · ".join(f"{r} {v}" for r, v in kit["colors"]))
            else:
                out.append(f"- palette: MUI's defaults (primary {KIT_DEFAULT_PRIMARY['MUI']})")
            bits = ([f"shape.borderRadius {kit['radius']}"] if kit["radius"] else []) + ([f"fonts {', '.join(kit['fonts'])}"] if kit["fonts"] else []) \
                + ([f"color schemes: {', '.join(kit['schemes'])}" + (f" (selector `{kit['selector']}`)" if kit["selector"] else "")] if kit["schemes"] else [])
            if bits:
                out.append("- " + " · ".join(bits))
            if kit["overrides"]:
                out.append(f"- component overrides ({kit['overridesCount']}): " + ", ".join(kit["overrides"]) + (" …" if kit["overridesCount"] > len(kit["overrides"]) else ""))
        elif name == "Chakra UI":
            out.append(f"### Chakra UI theme (v{kit['major']})" + (" — " + ", ".join(f"`{f}`" for f in kit["files"][:3]) if kit["files"] else ""))
            out.append("- colour scales (500 or middle step): " + (" · ".join(f"{n} {v}" for n, v in kit["scales"]) if kit["scales"]
                                                                    else f"Chakra's defaults ({KIT_DEFAULT_PRIMARY['Chakra UI']})"))
            bits = ([f"fonts {', '.join(kit['fonts'])}"] if kit["fonts"] else []) + ([f"component styles: {', '.join(kit['overrides'])}"] if kit["overrides"] else [])
            if bits:
                out.append("- " + " · ".join(bits))
        elif name == "Ant Design":
            out.append("### Ant Design theme" + (" — " + ", ".join(f"`{f}`" for f in kit["files"]) if kit["files"] else ""))
            out.append("- tokens: " + (" · ".join(f"{k2} {v}" for k2, v in kit["tokens"]) if kit["tokens"] else f"the defaults (colorPrimary {KIT_DEFAULT_PRIMARY['Ant Design']})"))
            if kit["components"]:
                out.append("- component tokens: " + ", ".join(kit["components"]))
            if kit["algorithms"]:
                out.append("- algorithms: " + ", ".join(kit["algorithms"]))
        elif name == "Element Plus":
            out.append("### Element Plus theme")
            src = "the default theme (`element-plus/dist/index.css`)" if kit["defaultCss"] else "its own build of the theme"
            out.append(f"- {src}" + (": " + " · ".join(f"{k2} {v}" for k2, v in kit["colors"]) if kit["colors"] else f", primary {KIT_DEFAULT_PRIMARY['Element Plus']}")
                       + (f" · locale {kit['locale']}" if kit["locale"] else "") + (f" · size {kit['size']}" if kit["size"] else ""))
            if kit["runtime"]:
                out.append(f"- `{kit['runtime']}` sets the `--el-color-*` variables at runtime (a theme picker): a colour change goes there too")
        elif name == "Vuetify":
            out.append("### Vuetify theme" + (" — " + ", ".join(f"`{f}`" for f in kit["files"]) if kit["files"] else ""))
            for t in kit["themes"]:
                out.append(f"- `{t['name']}` ({'dark' if t['dark'] else 'light'}{', the default' if t['name'] == kit['default'] else ''}): "
                           + (" · ".join(f"{k2} {v}" for k2, v in t["colors"]) or "no colours of its own"))
            if not kit["themes"]:
                out.append(f"- the default themes (primary {KIT_DEFAULT_PRIMARY['Vuetify']})")
            if kit["defaults"]:
                out.append("- component defaults: " + " · ".join(kit["defaults"]))
    st = k.get("styled")
    if st and st["theme"]:
        out.append(f"### {st['kit']} theme — `{st['theme']}`")
        if st["colors"]:
            out.append("- colours: " + " · ".join(f"{n} {v}" for n, v in st["colors"]))
        if st["darkThemes"]:
            out.append("- dark theme: " + ", ".join(f"`{d}`" for d in st["darkThemes"]))
    return out


# ------------------------------------------------------------------ Flutter
# A Flutter app is Dart under lib/: its pages are widgets that a router (go_router, auto_route, the
# Navigator's named routes) or a page folder names; its look is ThemeData and a ColorScheme per
# brightness, a TextTheme, and the numbers in EdgeInsets, SizedBox and BorderRadius. There is no DOM:
# the renderer for it is a widget test (flutter_render.mjs) that pumps the app at each size, in light
# and dark, saves the frames and runs Flutter's own contrast and tap-target guidelines.
FL_WIDGET_BASE = re.compile(r"class\s+(\w+)\s+extends\s+(Stateless|Stateful|Consumer|ConsumerStateful|Hook|HookConsumer|StatelessHook)?Widget\b")
FL_WRAPPERS = {"Builder", "FadeTransitionPage", "MaterialPage", "CupertinoPage", "CustomTransitionPage", "NoTransitionPage", "Scaffold",
               "SafeArea", "Padding", "Center", "Container", "SizedBox", "Material", "Consumer", "BlocProvider", "ChangeNotifierProvider",
               "Provider", "MultiProvider", "ProviderScope", "BlocBuilder", "Directionality", "Theme", "DefaultTabController", "PopScope",
               "WillPopScope", "MaterialPageRoute", "CupertinoPageRoute", "PageRouteBuilder", "Hero", "AnimatedBuilder", "ValueListenableBuilder",
               "ListenableBuilder", "StreamBuilder", "FutureBuilder", "LayoutBuilder", "Semantics", "Text", "Icon", "Column", "Row", "Stack"}
FL_COLORS = {     # the Material swatches' primary (500) values, and the black / white opacities
    "red": "#F44336", "pink": "#E91E63", "purple": "#9C27B0", "deepPurple": "#673AB7", "indigo": "#3F51B5", "blue": "#2196F3",
    "lightBlue": "#03A9F4", "cyan": "#00BCD4", "teal": "#009688", "green": "#4CAF50", "lightGreen": "#8BC34A", "lime": "#CDDC39",
    "yellow": "#FFEB3B", "amber": "#FFC107", "orange": "#FF9800", "deepOrange": "#FF5722", "brown": "#795548", "grey": "#9E9E9E",
    "blueGrey": "#607D8B", "white": "#FFFFFF", "black": "#000000", "transparent": "#00000000",
    "black87": "#000000DD", "black54": "#0000008A", "black45": "#00000073", "black38": "#00000061", "black26": "#00000042", "black12": "#0000001F",
    "white70": "#FFFFFFB3", "white60": "#FFFFFF99", "white54": "#FFFFFF8A", "white38": "#FFFFFF62", "white30": "#FFFFFF4D", "white24": "#FFFFFF3D",
    "white12": "#FFFFFF1F", "white10": "#FFFFFF1A",
}
FL_STATE = {"provider": "provider", "flutter_riverpod": "Riverpod", "hooks_riverpod": "Riverpod", "riverpod": "Riverpod", "flutter_bloc": "bloc",
            "get": "GetX", "mobx": "MobX", "flutter_mobx": "MobX", "refena_flutter": "Refena", "signals": "signals", "redux": "Redux",
            "flutter_redux": "Redux", "stacked": "Stacked"}
FL_ROUTERS = {"go_router": "go_router", "auto_route": "auto_route", "beamer": "Beamer", "routemaster": "Routemaster", "get": "GetX routes",
              "routerino": "Routerino"}
FL_KITS = {"cupertino_icons": None, "flex_color_scheme": "FlexColorScheme", "shadcn_ui": "shadcn_ui", "forui": "Forui", "fluent_ui": "Fluent UI",
           "macos_ui": "macos_ui", "yaru": "Yaru", "getwidget": "GetWidget", "flutter_neumorphic": "Neumorphic", "moon_design": "Moon Design"}


def _yaml(text: str) -> dict:
    """A pubspec's YAML: maps, lists of scalars and of maps, quoted scalars; folded blocks are skipped."""
    lines = []
    for raw in text.splitlines():
        s = re.sub(r"\s+#.*$", "", raw) if "#" in raw and not re.search(r"['\"][^'\"]*#", raw) else raw
        if s.strip() and not s.strip().startswith("#"):
            lines.append((len(s) - len(s.lstrip(" ")), s.strip()))

    def scalar(v: str):
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            return v[1:-1]
        return v

    def block(i: int, indent: int):
        if i < len(lines) and lines[i][1].startswith("- "):
            out = []
            while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                item = lines[i][1][2:]
                m = re.match(r"^([\w.-]+)\s*:\s*(.*)$", item)
                if m:                                  # - family: X, followed by the map's other keys
                    sub, i = block_map(i + 1, lines[i + 1][0] if i + 1 < len(lines) and lines[i + 1][0] > indent else indent + 2,
                                       {m.group(1): scalar(m.group(2)) if m.group(2) else None}, first_empty=m.group(1) if not m.group(2) else None)
                    out.append(sub)
                else:
                    out.append(scalar(item))
                    i += 1
            return out, i
        return block_map(i, indent, {})

    def block_map(i: int, indent: int, out: dict, first_empty: str | None = None):
        if first_empty and i < len(lines) and lines[i][0] > indent - 2:
            val, i = block(i, lines[i][0])
            out[first_empty] = val
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
            m = re.match(r"^([\w.-]+)\s*:\s*(.*)$", lines[i][1])
            if not m:
                i += 1
                continue
            key, val = m.group(1), m.group(2)
            if val in (">", ">-", "|", "|-", ">+", "|+"):
                i += 1
                while i < len(lines) and lines[i][0] > indent:
                    i += 1
                out[key] = ""
            elif val:
                out[key] = scalar(val)
                i += 1
            elif i + 1 < len(lines) and lines[i + 1][0] > indent:
                out[key], i = block(i + 1, lines[i + 1][0])
            elif i + 1 < len(lines) and lines[i + 1][0] == indent and lines[i + 1][1].startswith("- "):
                out[key], i = block(i + 1, indent)
            else:
                out[key] = None
                i += 1
        return out, i

    try:
        return block_map(0, lines[0][0] if lines else 0, {})[0]
    except (IndexError, RecursionError):
        return {}


def flutter_pubspec(root: Path) -> dict | None:
    """The app's pubspec when it is a Flutter app (`flutter: sdk: flutter` among the dependencies)."""
    ps = root / "pubspec.yaml"
    if not ps.is_file():
        return None
    y = _yaml(read(ps))
    deps = y.get("dependencies") if isinstance(y.get("dependencies"), dict) else {}
    if "flutter" not in deps and not isinstance(y.get("workspace"), list):
        return None
    return y


def flutter_workspace_apps(root: Path) -> list[str]:
    """A pub workspace, or a repository whose Flutter app is a folder or two down."""
    y = _yaml(read(root / "pubspec.yaml")) if (root / "pubspec.yaml").is_file() else {}
    cands = [root / w for w in y.get("workspace") or [] if isinstance(w, str)]
    if not cands:
        for d in sorted(root.iterdir()) if root.is_dir() else []:
            if d.is_dir() and not d.name.startswith(".") and d.name not in SKIP_DIRS:
                cands += [d] + [e for e in sorted(d.iterdir()) if e.is_dir() and not e.name.startswith(".") and e.name not in SKIP_DIRS]
    out = []
    for d in cands:
        ps = d / "pubspec.yaml"
        if ps.is_file() and (d / "lib").is_dir():
            deps = _yaml(read(ps)).get("dependencies") or {}
            if isinstance(deps, dict) and "flutter" in deps and ((d / "lib" / "main.dart").is_file() or any((d / "lib").glob("main*.dart"))):
                out.append(os.path.relpath(d, root))
    return out


def _dart_files(root: Path) -> list[Path]:
    lib = root / "lib"
    return sorted(p for p in lib.rglob("*.dart") if not set(p.relative_to(root).parts) & SKIP_DIRS
                  and not re.search(r"\.(g|freezed|gr|config|mocks|gen)\.dart$", p.name)) if lib.is_dir() else []


def _fl_color(expr: str, consts: dict[str, str], depth: int = 0) -> str | None:
    """A Dart colour expression as a hex: Color(0xFF101010), Color.fromARGB/RGBO, Colors.blue, a const that holds one."""
    e = expr.strip().rstrip(",").strip()
    e = re.sub(r"^const\s+", "", e)
    m = re.match(r"^Color\(\s*0x([0-9a-fA-F]{8})\s*\)$", e)
    if m:
        h = m.group(1).upper()
        return f"#{h[2:]}" + ("" if h[:2] == "FF" else h[:2])
    m = re.match(r"^Color\.fromARGB\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", e)
    if m:
        a, r, g, b = (int(x) for x in m.groups())
        return f"#{r:02X}{g:02X}{b:02X}" + ("" if a == 255 else f"{a:02X}")
    m = re.match(r"^Color\.fromRGBO\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)$", e)
    if m:
        r, g, b = (int(x) for x in m.groups()[:3])
        a = round(float(m.group(4)) * 255)
        return f"#{r:02X}{g:02X}{b:02X}" + ("" if a == 255 else f"{a:02X}")
    m = re.match(r"^(?:Colors|CupertinoColors)\.(\w+)$", e)
    if m:
        return FL_COLORS.get(m.group(1))
    if depth < 4 and e in consts:
        return _fl_color(consts[e], consts, depth + 1)
    m = re.match(r"^(\w+)\.(\w+)$", e)
    if m and depth < 4 and m.group(2) in consts and m.group(1)[:1].isupper():
        return _fl_color(consts[m.group(2)], consts, depth + 1)
    return None


def _fl_hex_css(h: str) -> str:
    """#RRGGBBAA (Dart's alpha last here) as a CSS colour the contrast helper reads."""
    if len(h) == 9:
        return f"rgba({int(h[1:3], 16)}, {int(h[3:5], 16)}, {int(h[5:7], 16)}, {round(int(h[7:9], 16) / 255, 3)})"
    return h


def _fl_consts(files: list[Path]) -> dict[str, str]:
    """Every `static const name = …` and top-level `const name = …` in lib/, by name (the last one wins)."""
    out: dict[str, str] = {}
    for p in files:
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"(?:static\s+)?(?:const|final)\s+(?:Color\s+|double\s+|int\s+)?(\w+)\s*=\s*", t):
            j = m.end()
            depth, k = 0, j
            while k < len(t):
                ch = t[k]
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    if depth == 0:
                        break
                    depth -= 1
                elif ch == ";" and depth == 0:
                    break
                k += 1
            out[m.group(1)] = t[j:k].strip()
    return out


def flutter_theme(root: Path, files: list[Path], consts: dict[str, str]) -> dict:
    """ThemeData and ColorScheme: literal schemes per brightness, seeds, the TextTheme's coloured styles, extensions."""
    schemes, seeds, text_styles, extensions, cupertino = [], [], [], [], []
    palettes, scales = [], []
    m3 = None
    for p in files:
        t = _no_comments(read(p, 300_000))
        # A class of constants: colours (AppColors) or sizes (Dimens, Spacing, AppRadius)
        for cm in re.finditer(r"(?:abstract\s+)?(?:final\s+)?class\s+(\w+)[^{]*\{", t):
            body = _balanced(t, cm.end() - 1)
            vals = re.findall(r"static\s+const\s+(?:\w+\s+)?(\w+)\s*=\s*([^;]+);", body)
            cols = [(k, _fl_color(v, consts)) for k, v in vals]
            cols = [(k, c) for k, c in cols if c]
            nums = [(k, v.strip()) for k, v in vals if re.match(r"^[\d.]+$", v.strip())]
            if len(cols) >= 3:
                palettes.append({"file": rel(root, p), "name": cm.group(1), "colors": cols[:16]})
            if len(nums) >= 2 and re.search(r"Dimen|Spac|Size|Inset|Gap|Radi|Padding|Margin|Layout|Breakpoint", cm.group(1)):
                scales.append({"file": rel(root, p), "name": cm.group(1),
                               "values": [(k, v.rstrip("0").rstrip(".") if "." in v else v) for k, v in nums[:12]]})
        if "ColorScheme" not in t and "ThemeData" not in t and "TextTheme" not in t and "ThemeExtension" not in t:
            continue
        for m in re.finditer(r"(?:\bColorScheme|\bcolorScheme\s*:\s*(?:const\s+)?(?=\.))(\.(?:light|dark|highContrastLight|highContrastDark))?\s*\(", t):
            body = _balanced(t, m.end() - 1)
            fl = _fields(body)
            colors = [(k, _fl_color(v, consts)) for k, v in fl.items() if k not in ("brightness",)]
            colors = [(k, v) for k, v in colors if v]
            bright = "dark" if (m.group(1) or "").lower().endswith("dark") or re.search(r"(?:Brightness)?\.dark\b", fl.get("brightness") or "") else "light"
            before = t[max(0, m.start() - 120):m.start()]
            name = (re.findall(r"(\w+)\s*=\s*(?:const\s+)?$", before) or re.findall(r"(\w+)\s*:\s*(?:const\s+)?$", before) or [""])[-1]
            if len(colors) >= 2:
                schemes.append({"file": rel(root, p), "name": name, "brightness": bright, "colors": colors})
        for m in re.finditer(r"(?:\bColorScheme|\bcolorScheme\s*:\s*(?:const\s+)?)\.fromSeed\s*\(", t):   # `.fromSeed(` is Dart's dot shorthand
            fl = _fields(_balanced(t, m.end() - 1))
            seed = _fl_color(fl.get("seedColor", ""), consts)
            seeds.append({"file": rel(root, p), "seed": seed or (fl.get("seedColor") or "?")[:40],
                          "brightness": "dark" if re.search(r"(?:Brightness)?\.dark\b", fl.get("brightness") or "") else "light"})
        for m in re.finditer(r"\bcolorSchemeSeed\s*:\s*([^,)\n]+)", t):
            seeds.append({"file": rel(root, p), "seed": _fl_color(m.group(1), consts) or m.group(1).strip()[:40], "brightness": "?"})
        for m in re.finditer(r"\bprimarySwatch\s*:\s*([^,)\n]+)", t):
            seeds.append({"file": rel(root, p), "seed": (_fl_color(m.group(1), consts) or m.group(1).strip()) + " (a Material 2 swatch)", "brightness": "?"})
        um = re.search(r"useMaterial3\s*:\s*(true|false)", t)
        if um:
            m3 = um.group(1) == "true"
        for m in re.finditer(r"\bTextTheme\s*\(", t):
            for style, v in _fields(_balanced(t, m.end() - 1)).items():
                sm = re.match(r"^(?:const\s+)?TextStyle\s*\(", v)
                if not sm:
                    continue
                sf = _fields(_balanced(v, sm.end() - 1))
                text_styles.append({"style": style, "size": sf.get("fontSize"), "weight": (sf.get("fontWeight") or "").replace("FontWeight.", ""),
                                    "color": _fl_color(sf.get("color", ""), consts), "file": rel(root, p)})
        extensions += re.findall(r"class\s+(\w+)\s+extends\s+ThemeExtension<", t)
        for m in re.finditer(r"\bCupertinoThemeData\s*\(", t):
            fl = _fields(_balanced(t, m.end() - 1))
            c = _fl_color(fl.get("primaryColor", ""), consts)
            cupertino.append({"file": rel(root, p), "primary": c or (fl.get("primaryColor") or "")[:30]})
    # A light and a dark literal scheme side by side: by their names (lightColorScheme / darkColorScheme) or their brightness.
    pairs, used = [], set()
    for i, a in enumerate(schemes):
        if i in used or a["brightness"] != "light":
            continue
        base = re.sub(r"(?i)light", "", a["name"])
        j = next((j for j, b in enumerate(schemes) if j not in used and j != i and b["brightness"] == "dark"
                  and (re.sub(r"(?i)dark", "", b["name"]) == base or b["file"] == a["file"])), None)
        used.add(i)
        if j is not None:
            used.add(j)
        pairs.append({"file": a["file"], "name": a["name"] + (f" / {schemes[j]['name']}" if j is not None else ""),
                      "light": a["colors"], "dark": schemes[j]["colors"] if j is not None else []})
    pairs += [{"file": b["file"], "name": b["name"], "light": [], "dark": b["colors"]} for k, b in enumerate(schemes) if k not in used]
    return {"schemes": pairs[:3], "seeds": list({(s["seed"], s["brightness"]): s for s in seeds}.values())[:4], "textStyles": text_styles[:14],
            "extensions": list(dict.fromkeys(extensions))[:6], "m3": m3, "cupertino": cupertino[:2], "palettes": palettes[:3], "scales": scales[:4]}


def flutter_scheme_contrast(pair: dict, text_styles: list[dict]) -> list[str]:
    """onX on X for each literal scheme, and each TextTheme style that sets its own colour, against the surface."""
    out = []
    light, dark = dict(pair["light"]), dict(pair["dark"])
    on = []
    for k in [k for k in dict.fromkeys(list(light) + list(dark)) if re.match(r"^on[A-Z]", k)]:
        base = k[2].lower() + k[3:]
        a = _rn_contrast(_fl_hex_css(light[k]), _fl_hex_css(light[base])) if k in light and base in light else None
        b = _rn_contrast(_fl_hex_css(dark[k]), _fl_hex_css(dark[base])) if k in dark and base in dark else None
        if a is None and b is None:
            continue
        on.append(f"{k} on {base} {a if a is not None else '—'} / {b if b is not None else '—'}"
                  + (" ✗" if (a is not None and a < 4.5) or (b is not None and b < 4.5) else ""))
    if on:
        out.append("content on its colour (light / dark, 4.5:1 for text): " + " · ".join(on[:6]))
    # the secondary roles on the surface: onSurfaceVariant is text (4.5:1), outline a border (3:1)
    side = []
    for k, need in (("onSurfaceVariant", 4.5), ("outline", 3.0)):
        a = _rn_contrast(_fl_hex_css(light[k]), _fl_hex_css(light["surface"])) if k in light and "surface" in light else None
        b = _rn_contrast(_fl_hex_css(dark[k]), _fl_hex_css(dark["surface"])) if k in dark and "surface" in dark else None
        if a is not None or b is not None:
            side.append(f"{k} on surface {a if a is not None else '—'} / {b if b is not None else '—'} ({need:g}:1)"
                        + (" ✗" if (a is not None and a < need) or (b is not None and b < need) else ""))
    if side:
        out.append("secondary roles on the surface (light / dark): " + " · ".join(side))
    styled = []
    for s in text_styles:
        if not s["color"]:
            continue
        a = _rn_contrast(_fl_hex_css(s["color"]), _fl_hex_css(light["surface"])) if "surface" in light else None
        b = _rn_contrast(_fl_hex_css(s["color"]), _fl_hex_css(dark["surface"])) if "surface" in dark else None
        if a is None and b is None:
            continue
        need = 3 if s["size"] and re.match(r"^[\d.]+$", s["size"]) and float(s["size"]) >= 24 else 4.5
        styled.append(f"{s['style']} {s['color']} on surface {a if a is not None else '—'} / {b if b is not None else '—'}"
                      + (" ✗" if (a is not None and a < need) or (b is not None and b < need) else ""))
    if styled:
        out.append("TextTheme styles with their own colour (light / dark surface): " + " · ".join(styled[:5]))
    return out


def _fl_class_index(files: list[Path]) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for p in files:
        for name, _ in FL_WIDGET_BASE.findall(read(p, 300_000)):
            idx.setdefault(name, p)
    return idx


def _fl_screen_of(body: str, idx: dict[str, Path]) -> str | None:
    """The first of the app's own widgets a builder returns, past wrappers (Builder, a transition page, Scaffold)."""
    for name in re.findall(r"(?<![\w.])(?:const\s+)?([A-Z]\w*)\s*(?:<[^>]{0,40}>)?\s*\(", body):
        if name in idx and name not in FL_WRAPPERS:
            return name
    return None


def _fl_path(v: str | None, consts: dict[str, str]) -> str | None:
    if not v:
        return None
    s = _unquote(v.strip())
    if s is None:
        m = re.match(r"^(\w+)\.(\w+)$", v.strip())
        if m and m.group(2) in consts:
            s = _unquote(consts[m.group(2)])
    if s is None:
        return None
    return re.sub(r"\$\{?(\w+)\}?", lambda k: _unquote(consts.get(k.group(1), "")) or "{" + k.group(1) + "}", s)


def flutter_go_router(root: Path, files: list[Path], idx: dict[str, Path], consts: dict[str, str]) -> dict:
    """go_router's tree: each GoRoute's full path and screen, the ShellRoute around it, the redirects."""
    routes, shells, guards = [], [], []

    def walk(t: str, body: str, prefix: str, shell: str | None, depth: int):
        if depth > 8:
            return
        for el in _split_top(body):
            m = re.match(r"^(?:const\s+)?(GoRoute|ShellRoute|StatefulShellRoute(?:\.indexedStack)?|StatefulShellBranch|TypedGoRoute)\s*\(", el)
            if not m:
                continue
            fl = _fields(_balanced(el, m.end() - 1))
            kind = m.group(1)
            here = prefix
            if kind == "GoRoute":
                p = _fl_path(fl.get("path"), consts)
                if p is not None:
                    here = p if p.startswith("/") else _join_route(prefix, p)
            builder = fl.get("builder") or fl.get("pageBuilder") or ""
            screen = _fl_screen_of(builder, idx) if builder else None
            new_shell = shell
            if kind.startswith(("ShellRoute", "StatefulShellRoute")) and screen:
                new_shell = screen
                shells.append(screen)
            elif kind == "GoRoute":
                routes.append({"path": here, "screen": screen, "shell": shell, "redirect": "redirect" in fl})
            sub = fl.get("routes") or fl.get("branches")
            if sub and sub.startswith("["):
                walk(t, _balanced(sub, 0), here, new_shell, depth + 1)

    for p in files:
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"\bGoRouter\s*\(", t):
            fl = _fields(_balanced(t, m.end() - 1))
            if fl.get("redirect"):
                red = fl["redirect"]
                if re.match(r"^\w+$", red):                # redirect: _redirect — the function's body
                    fm = re.search(r"(?:^|\n)[\w<>?, ]*\b" + re.escape(red) + r"\s*\([^)]*\)\s*(?:async\s*)?\{", t)
                    red = _balanced(t, fm.end() - 1) if fm else red
                dests = list(dict.fromkeys(re.findall(r"return\s+['\"]([^'\"]+)['\"]", red) + re.findall(r"return\s+(\w+\.\w+)\s*;", red)))
                dests = [_fl_path(d if d.startswith(("'", '"')) or "." in d else f"'{d}'", consts) or d for d in dests]
                guards.append({"file": rel(root, p), "to": dests})
            rs = fl.get("routes", "")
            if rs.startswith("["):
                walk(t, _balanced(rs, 0), "/", None, 0)
            elif re.match(r"^\$?\w+$", rs):                # routes: $appRoutes (go_router_builder) or a list elsewhere
                lm = re.search(r"(?:final|const|var)\s+(?:List<\w+>\s+)?" + re.escape(rs.lstrip("$")) + r"\s*=\s*(?:<\w+>)?\[", t)
                if lm:
                    walk(t, _balanced(t, lm.end() - 1), "/", None, 0)
    return {"routes": routes, "shells": list(dict.fromkeys(shells)), "guards": guards}


def flutter_named_routes(root: Path, files: list[Path], idx: dict[str, Path], consts: dict[str, str]) -> list[dict]:
    """The Navigator's routes: MaterialApp(routes: {'/': (c) => Home()}), onGenerateRoute's cases, home:."""
    out = []
    for p in files:
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"\b(?:Material|Cupertino|Widgets)App\s*\(", t):
            fl = _fields(_balanced(t, m.end() - 1))
            if fl.get("home"):
                s = _fl_screen_of(fl["home"], idx)
                if s:
                    out.append({"path": "/ (home)", "screen": s, "shell": None, "redirect": False})
            r = fl.get("routes", "")
            if r.startswith("{"):
                for part in _split_top(_balanced(r, 0)):
                    km = re.match(r"^\s*(['\"][^'\"]*['\"]|\w+\.\w+)\s*:\s*(.*)$", part, re.S)
                    if km:
                        out.append({"path": _fl_path(km.group(1), consts) or km.group(1), "screen": _fl_screen_of(km.group(2), idx),
                                    "shell": None, "redirect": False})
        for m in re.finditer(r"case\s+(['\"][^'\"]+['\"]|\w+\.\w+)\s*:\s*(?:return\s+)?(?:MaterialPageRoute|CupertinoPageRoute|PageRouteBuilder)", t):
            body = t[m.end():m.end() + 300]
            out.append({"path": _fl_path(m.group(1), consts) or m.group(1), "screen": _fl_screen_of(body, idx), "shell": None, "redirect": False})
    return out


def flutter_auto_route(root: Path, files: list[Path], idx: dict[str, Path], consts: dict[str, str]) -> list[dict]:
    """auto_route: `@RoutePage()` screens, with the paths `AutoRoute(page: XRoute.page, path: …)` gives them."""
    pages = {}
    for p in files:
        t = read(p, 300_000)
        for name in re.findall(r"@RoutePage(?:<[^>]*>)?\([^)]*\)\s*class\s+(\w+)", t):
            pages[re.sub(r"(Screen|Page|View)$", "", name) + "Route"] = name
    out = []
    for p in files:
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"\b\w*AutoRoute\s*\(", t):
            fl = _fields(_balanced(t, m.end() - 1))
            pm = re.match(r"^(\w+)\.page$", fl.get("page", ""))
            if pm and pm.group(1) in pages:
                out.append({"path": _fl_path(fl.get("path"), consts) or f"({pm.group(1)})", "screen": pages[pm.group(1)], "shell": None,
                            "redirect": "guards" in fl})
    for route, name in pages.items():
        if not any(r["screen"] == name for r in out):
            out.append({"path": f"({route})", "screen": name, "shell": None, "redirect": False})
    return out


def _fl_signals(t: str) -> list[str]:
    sig = []
    n = len(re.findall(r"\b(?:TextField|TextFormField|CupertinoTextField|DropdownButton\w*|DropdownMenu|Checkbox|Switch|Radio|Slider|"
                       r"CupertinoSwitch|SegmentedButton|DatePickerDialog|showDatePicker)\s*[<(]", t))
    if n:
        sig.append(f"{n} field{'s' if n > 1 else ''}")
    if re.search(r"\bForm\s*\(", t):
        sig.append("form")
    if re.search(r"\b(?:DataTable|Table|PaginatedDataTable)\s*\(", t):
        sig.append("table")
    elif re.search(r"\b(?:ListView|GridView|SliverList|SliverGrid|CustomScrollView|ReorderableListView)(?:\.\w+)?\s*\(", t):
        sig.append("list")
    if re.search(r"\b(?:showDialog|showModalBottomSheet|showCupertinoDialog|showCupertinoModalPopup|AlertDialog|SimpleDialog)\b", t):
        sig.append("dialog")
    chrome = [w for w in ("AppBar", "SliverAppBar", "NavigationBar", "NavigationRail", "BottomNavigationBar", "TabBar", "Drawer", "FloatingActionButton",
                          "CupertinoNavigationBar", "CupertinoTabBar") if re.search(r"\b" + w + r"\s*[.(]", t)]
    if chrome:
        sig.append(", ".join(chrome[:3]))
    return sig


def _fl_components(t: str, idx: dict[str, Path], own: Path) -> list[str]:
    used = [n for n in dict.fromkeys(re.findall(r"(?<![\w.])(?:const\s+)?([A-Z]\w*)\s*\(", t)) if n in idx and idx[n] != own]
    return used[:6]


def flutter_pages(root: Path, files: list[Path], deps: dict, consts: dict[str, str]) -> dict:
    idx = _fl_class_index(files)
    gr = flutter_go_router(root, files, idx, consts) if "go_router" in deps else {"routes": [], "shells": [], "guards": []}
    routes = gr["routes"] or (flutter_auto_route(root, files, idx, consts) if "auto_route" in deps else []) or flutter_named_routes(root, files, idx, consts)
    by_screen: dict[str, list[dict]] = {}
    for r in routes:
        if r["screen"]:
            by_screen.setdefault(r["screen"], []).append(r)
    pages = []
    if len(by_screen) >= 2 or (by_screen and not any(re.search(r"(?:^|/)(pages|screens|views)/|_(page|screen)\.dart$", rel(root, p)) for p in files)):
        for name, rs in by_screen.items():
            f = idx[name]
            t = read(f, 200_000)
            paths = list(dict.fromkeys(r["path"] for r in rs))
            rec = {"file": rel(root, f), "lines": t.count("\n") + 1, "signals": _fl_signals(t), "classes": [],
                   "components": _fl_components(t, idx, f), "renders": None,
                   "route": ", ".join(f"`{x}`" for x in paths[:3]) + (f" and {len(paths) - 3} more" if len(paths) > 3 else "") + f" · {name}",
                   "routeGuards": []}
            shell = next((r["shell"] for r in rs if r["shell"]), None)
            if shell and shell in idx:
                st = read(idx[shell], 200_000)
                rec["inside"] = {"name": shell, "file": rel(root, idx[shell]), "lines": st.count("\n") + 1, "holder": "`child`"}
            signin = [d for d in (gr["guards"][0]["to"] if gr["guards"] else []) if re.search(r"log-?in|sign|auth|welcome|onboard", d, re.I)]
            if gr["guards"] and not set(paths) & set(signin):   # the sign-in page it redirects to is not behind it
                to = gr["guards"][0]["to"]
                rec["routeGuards"] = ["the router's redirect" + (f" (to {', '.join(f'`{d}`' for d in to[:2])})" if to else "")]
            pages.append(rec)
        mode = "go_router" if gr["routes"] else "auto_route" if "auto_route" in deps and routes else "Navigator"
    else:                                           # no route table: the page folders and the files named like pages
        for f in files:
            rp = rel(root, f)
            if not re.search(r"(?:^|/)(pages|screens|views)/|_(page|screen)\.dart$", rp):
                continue
            t = read(f, 200_000)
            names = [n for n, _ in FL_WIDGET_BASE.findall(t)]
            if not names:
                continue
            pages.append({"file": rp, "lines": t.count("\n") + 1, "signals": _fl_signals(t), "classes": [], "components": _fl_components(t, idx, f),
                          "renders": None, "route": f"{names[0]} (no route table)", "routeGuards": []})
        mode = "page files"
    return {"pages": pages[:32], "routes": [(r["path"], r["screen"] or "?") for r in routes][:30], "mode": mode, "guards": gr["guards"],
            "shells": [s for s in gr["shells"] if s in idx], "idx": idx}


def flutter_usage(root: Path, files: list[Path], theme_files: set[str], scales: list[dict] | None = None) -> dict:
    """What widgets use: spacing and radius numbers, font sizes, literal colours against the theme, the Material and Cupertino widgets."""
    spc, rad, fsz, lit, theme_col, text_ref, widgets = (collections.Counter() for _ in range(7))
    steps = collections.Counter()           # references to a spacing scale's named steps (Insets.md)
    scale_names = {sc["name"]: sc["file"] for sc in scales or []}
    a11y = collections.Counter()
    for p in files:
        rp = rel(root, p)
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"\bEdgeInsets(?:Directional)?\.(all|symmetric|only|fromLTRB|fromSTEB)\s*\(([^)]*)\)", t):
            for v in re.findall(r"(?:^|[,:(\s])(\d+(?:\.\d+)?)(?=\s*[,)]|\s*$)", m.group(2)):
                spc[v.rstrip("0").rstrip(".") if "." in v else v] += 1
        # a SizedBox without a child is a gap; one with a child is that child's size
        gaps = [v for sm in re.finditer(r"\bSizedBox\s*\(", t) for args in [_balanced(t, sm.end() - 1)]
                if not re.search(r"\bchild\s*:", args) for v in re.findall(r"\b(?:height|width)\s*:\s*(\d+(?:\.\d+)?)\s*(?:,|$)", args)]
        for v in gaps + re.findall(r"\bGap\s*\(\s*(\d+(?:\.\d+)?)\s*\)", t):
            spc[v.rstrip("0").rstrip(".") if "." in v else v] += 1
        for name, file in scale_names.items():
            if rp != file:
                # Insets.md, and Dimens.of(context).paddingScreen (a scale per screen size); not a call like Dimens.of(…)
                steps.update(f"{name}.{m}" for m in re.findall(r"\b" + re.escape(name) + r"\.(?:of\(\s*\w+\s*\)\.)?([a-z]\w*)\b(?!\s*\()", t))
        for v in re.findall(r"\b(?:BorderRadius|Radius)\.circular\s*\(\s*(\d+(?:\.\d+)?)\s*\)", t):
            rad[v.rstrip("0").rstrip(".") if "." in v else v] += 1
        if rp not in theme_files:             # the TextTheme's own sizes are the theme, not a widget's choice
            for v in re.findall(r"\bfontSize\s*:\s*(\d+(?:\.\d+)?)", t):
                fsz[v.rstrip("0").rstrip(".") if "." in v else v] += 1
        if rp not in theme_files:
            lit.update(re.findall(r"\bColor\(\s*0x[0-9a-fA-F]{8}\s*\)|\bColors\.\w+", t))
        theme_col.update(re.findall(r"\bcolorScheme\.(\w+)", t))
        text_ref.update(re.findall(r"\btextTheme\.(\w+)", t))
        widgets.update(re.findall(r"(?<![\w.])(?:const\s+)?(ElevatedButton|FilledButton|OutlinedButton|TextButton|IconButton|FloatingActionButton|"
                                  r"ListTile|Card|Chip|FilterChip|ChoiceChip|NavigationBar|NavigationRail|BottomNavigationBar|TabBar|AppBar|"
                                  r"SegmentedButton|SearchBar|Badge|CupertinoButton|CupertinoListTile|CupertinoNavigationBar|CupertinoTabBar)"
                                  r"(?:\.\w+)?\s*\(", t))
        a11y["semantics"] += len(re.findall(r"\bSemantics\s*\(", t))
        a11y["labels"] += len(re.findall(r"\bsemanticLabel\s*:|\bsemanticsLabel\s*:", t))
        a11y["tooltips"] += len(re.findall(r"\btooltip\s*:", t))
        a11y["iconButtons"] += len(re.findall(r"(?<![\w.])(?:const\s+)?IconButton(?:\.\w+)?\s*\(", t))
        a11y["gestures"] += len(re.findall(r"(?<![\w.])(?:GestureDetector|InkWell)\s*\(", t))
        a11y["noScale"] += len(re.findall(r"TextScaler\.noScaling|textScaleFactor\s*:\s*1(?:\.0)?\b|TextScaler\.linear\(\s*1(?:\.0)?\s*\)", t))
        a11y["clamped"] += len(re.findall(r"withClampedTextScaling|\.clamp\(\s*(?:min|max)ScaleFactor", t))
    return {"spacing": spc.most_common(8), "steps": steps.most_common(6), "stepTotal": sum(steps.values()), "spacingTotal": sum(spc.values()),
            "radius": rad.most_common(5), "fontSize": fsz.most_common(6), "literal": sum(lit.values()),
            "literalTop": lit.most_common(4), "themeColors": theme_col.most_common(6), "themeColorTotal": sum(theme_col.values()),
            "textStyles": text_ref.most_common(6), "widgets": widgets.most_common(12), "a11y": dict(a11y)}


def flutter_start(root: Path, ps: dict) -> dict:
    deps = {**(ps.get("dependencies") or {}), **(ps.get("dev_dependencies") or {})} if isinstance(ps.get("dependencies"), dict) else {}
    files = _dart_files(root)
    consts = _fl_consts(files)
    pg = flutter_pages(root, files, deps, consts)
    theme = flutter_theme(root, files, consts)
    usage = flutter_usage(root, files, {s["file"] for s in theme["schemes"] + theme["textStyles"] + theme["palettes"]}, theme["scales"])
    before, layouts = [], []
    app_file = None
    app_bits = {}
    best = -1
    for p in files:
        t = _no_comments(read(p, 300_000))
        for m in re.finditer(r"\b(?:Material|Cupertino)App(?:\.router)?\s*\(", t):
            fl = _fields(_balanced(t, m.end() - 1))
            score = sum(k in fl for k in ("theme", "darkTheme", "themeMode", "routerConfig", "routes", "home", "localizationsDelegates", "navigatorKey")) \
                + (3 if p.name in ("main.dart", "app.dart") else 0) - (5 if re.search(r"error|test|debug|mock", p.name) else 0)
            if score <= best:
                continue
            best = score
            app_file = rel(root, p)
            app_bits = {"theme": fl.get("theme"), "darkTheme": fl.get("darkTheme"), "themeMode": fl.get("themeMode"),
                        "kind": "CupertinoApp" if "CupertinoApp" in m.group(0) else "MaterialApp" + (".router" if ".router" in m.group(0) else ""),
                        "locales": bool(fl.get("supportedLocales") or fl.get("localizationsDelegates"))}
    main = root / "lib" / "main.dart"
    mt = _no_comments(read(main, 200_000)) if main.is_file() else ""
    rm = re.search(r"\brunApp\s*\(", mt)
    root_widget = re.sub(r"\s+", " ", _balanced(mt, rm.end() - 1)).strip() if rm else None
    if root_widget and len(root_widget) > 40:          # RefenaScope.withContainer(container: …, child: …) → its outer call
        om = re.match(r"^(?:const\s+)?([\w.]+)\s*\(", root_widget)
        root_widget = f"{om.group(1)}(…)" if om else root_widget[:40] + "…"
    wraps = [w for w in re.findall(r"([A-Z]\w*)\s*\(", root_widget or "") if w in ("ProviderScope", "MultiProvider", "MultiBlocProvider", "RefenaScope",
                                                                                   "ChangeNotifierProvider", "BlocProvider", "GetMaterialApp", "TranslationProvider")]
    if app_file:
        def short(e: str) -> str:
            e = re.sub(r"\s+", " ", e).strip().replace("( ", "(").replace(" )", ")")
            return e if len(e) <= 48 else e[:47] + "…"
        theme_expr = f"`{short(app_bits['theme'])}`" if app_bits.get("theme") else "the default"
        layouts.append({"file": app_file, "css": [], "fonts": [], "providers": wraps, "chrome": [], "scope": "",
                        "scopeText": f"holds the {app_bits['kind']}, with theme {theme_expr}"
                                     + (f" and darkTheme `{short(app_bits['darkTheme'])}`" if app_bits.get("darkTheme") else "")})
    for s in pg["shells"]:
        before.append(f"`{rel(root, pg['idx'][s])}` ({s}) is the shell around the routes under it: the navigation bar or rail is there")
    for g in pg["guards"]:
        before.append(f"`{g['file']}`: the router redirects " + (f"to {', '.join(f'`{d}`' for d in g['to'][:3])} " if g["to"] else "")
                      + "when its check fails (a sign-in): render past it with the stored flag the check reads (`--prefs KEY=VALUE`), "
                      "by signing in (`--enter Email=… --enter Password=… --tap 'Sign in'`), or pump the screen itself (`--widget`)")
    prefs = sorted({k for p in files for k in re.findall(r"\b(?:prefs|preferences|sharedPreferences|_prefs|storage)\.(?:get|set)(?:String|Bool|Int|Double|StringList)?\(\s*['\"]([\w.:-]+)['\"]", read(p, 200_000))})
    if prefs:
        before.append("stored settings (shared_preferences keys): " + ", ".join(f"`{k}`" for k in prefs[:8])
                      + f" — a widget test starts with none: `--prefs {prefs[0]}=…` sets one before the app starts")
    plugins = [k for k in deps if k in ("firebase_core", "google_maps_flutter", "camera", "webview_flutter", "flutter_inappwebview", "local_auth",
                                        "geolocator", "image_picker", "file_picker", "path_provider", "package_info_plus", "device_info_plus",
                                        "connectivity_plus", "flutter_secure_storage", "sqflite", "isar", "hive_flutter", "shared_preferences")]
    fonts = []
    for fam in (ps.get("flutter") or {}).get("fonts") or [] if isinstance(ps.get("flutter"), dict) else []:
        if isinstance(fam, dict) and fam.get("family"):
            n = len(fam.get("fonts") or []) if isinstance(fam.get("fonts"), list) else 0
            fonts.append(f"{fam['family']} ({n} file{'s' if n != 1 else ''})")
    gf = sorted(set(m for p in files for m in re.findall(r"GoogleFonts\.(\w+?)(?:TextTheme)?\(", read(p, 200_000)) if m not in ("getFont", "getTextTheme", "config")))
    ff = sorted(set(m for p in files for m in re.findall(r"fontFamily\s*:\s*['\"]([^'\"]+)['\"]", read(p, 200_000))))
    l10n = [rel(root, p) for p in sorted((root / "lib").rglob("*.arb"))][:4] if (root / "lib").is_dir() else []
    l10n += [rel(root, p) for p in sorted(root.glob("l10n/*.arb"))][:4] if not l10n else []
    slang = [rel(root, p) for p in (root / "lib").rglob("strings*.g.dart")][:1] if (root / "lib").is_dir() else []
    platform = sum(1 for p in files if re.search(r"Platform\.is(?:IOS|Android|MacOS|Windows|Linux)|kIsWeb|defaultTargetPlatform", read(p, 200_000)))
    # `flutter create`'s counter, untouched: its seed colour is the template's, not a choice
    template = "_incrementCounter" in mt and len(files) <= 3
    return {"template": template, "pages": pg["pages"], "routes": pg["routes"], "mode": pg["mode"], "layouts": layouts, "stackBefore": before, "theme": theme,
            "usage": usage, "appFile": app_file, "app": app_bits, "rootWidget": root_widget, "wraps": wraps, "plugins": plugins,
            "fonts": fonts, "googleFonts": gf, "fontFamilies": ff, "l10n": l10n, "slang": slang, "platform": platform, "consts": len(consts)}


def dart_fanin(root: Path, files: list[Path], pkg: str | None) -> list[dict]:
    """The app's own files imported most, with a widget's constructor fields (its props)."""
    counts: collections.Counter = collections.Counter()
    for p in files:
        t = read(p, 200_000)
        seen = set()
        for spec in re.findall(r"^\s*import\s+['\"]([^'\"]+)['\"]", t, re.M):
            if pkg and spec.startswith(f"package:{pkg}/"):
                target = root / "lib" / spec[len(f"package:{pkg}/"):]
            elif not spec.startswith(("package:", "dart:")):
                target = (p.parent / spec)
            else:
                continue
            target = Path(os.path.normpath(target))
            if target.is_file() and target != p and target not in seen:
                seen.add(target)
                counts[target] += 1
    out = []
    for f, n in counts.most_common(40):
        if n < 2:
            break
        t = read(f, 200_000)
        wm = FL_WIDGET_BASE.search(t)
        if not wm:
            continue
        cm = re.search(r"(?:const\s+)?" + re.escape(wm.group(1)) + r"\s*\(\s*\{([^}]*)\}", t)
        props = [x for x in re.findall(r"(?:required\s+)?this\.(\w+)", cm.group(1))] if cm else []
        out.append({"file": rel(root, f), "importers": n, "props": props[:8]})
        if len(out) >= 8:
            break
    return out


def flutter_copy(fl: dict) -> dict:
    dicts = []
    for f in fl["l10n"]:
        try:
            n = len([k for k in json.loads(read(Path(fl["root"]) / f)).keys() if not k.startswith("@")])
        except (json.JSONDecodeError, AttributeError, OSError):
            n = 0
        dicts.append((f, n))
    libs = (["flutter_localizations (ARB files, `AppLocalizations.of(context)`)"] if fl["l10n"] else []) + (["slang (`t.…`)"] if fl["slang"] else [])
    return {"dictionaries": dicts, "typed": None, "libs": libs, "hook": None}


def md_flutter_lines(fl: dict) -> list[str]:
    out = []
    u = fl["usage"]
    if u["widgets"]:
        out.append("- Widgets by use (Material and Cupertino): " + " · ".join(f"{n} ×{c}" for n, c in u["widgets"][:10])
                   + ". A match task builds with these and the app's theme (" + ("`CupertinoTheme.of(context)`" if (fl.get("appKind") or "").startswith("Cupertino")
                                                                             else "`Theme.of(context).colorScheme`, `textTheme`") + "), not hand-rolled containers.")
    if u["themeColors"] or u["literal"]:
        out.append("- Colours: from the theme ×" + str(u["themeColorTotal"])
                   + (f" ({', '.join(f'`colorScheme.{k}` ×{n}' for k, n in u['themeColors'][:4])})" if u["themeColors"] else "")
                   + f", literals in widgets ×{u['literal']}" + (f" ({', '.join(f'`{k}` ×{n}' for k, n in u['literalTop'][:3])})" if u["literalTop"] else "")
                   + (f"; text styles read: {', '.join(f'`{k}` ×{n}' for k, n in u['textStyles'][:4])}" if u["textStyles"] else ""))
    a = u["a11y"]
    bits = [f"{a.get('semantics', 0)} `Semantics`", f"{a.get('labels', 0)} semantic labels",
            f"{a.get('tooltips', 0)} tooltip{'s' if a.get('tooltips', 0) != 1 else ''} (for {a.get('iconButtons', 0)} `IconButton`{'s' if a.get('iconButtons', 0) != 1 else ''})"]
    if a.get("gestures"):
        bits.append(f"{a['gestures']} `GestureDetector` / `InkWell` (a tap target with no role unless wrapped in `Semantics(button: true)`)")
    if a.get("noScale"):
        bits.append(f"`TextScaler.noScaling` or a text scale of 1 ×{a['noScale']}: that text ignores the user's font size")
    out.append("- Accessibility in code: " + " · ".join(bits))
    if fl["platform"]:
        out.append(f"- `Platform.isIOS` / `kIsWeb` / `defaultTargetPlatform` in {fl['platform']} file{'s' if fl['platform'] > 1 else ''}: a widget test runs as Android unless told otherwise (`debugDefaultTargetPlatformOverride`)")
    return out


def md_flutter_tokens(fl: dict) -> list[str]:
    out = []
    th = fl["theme"]
    for pair in th["schemes"]:
        light, dark = dict(pair["light"]), dict(pair["dark"])
        keys = list(dict.fromkeys(list(light) + list(dark)))
        out.append(f"### ColorScheme `{pair['name'] or '(unnamed)'}` in `{pair['file']}`")
        out.append(("- light / dark: " if light and dark else "- colours: ") + " · ".join(
            f"{k} {light.get(k, '—')}" + (f" / {dark.get(k, '—')}" if dark else "") for k in keys[:14]) + (" …" if len(keys) > 14 else ""))
        out += [f"- {x}" for x in flutter_scheme_contrast(pair, th["textStyles"])]
    known = [s for s in th["seeds"] if re.match(r"^#[0-9A-F]{6}", s["seed"])]
    for s in known:
        out.append(f"### ColorScheme from a seed — `{s['file']}`")
        out.append(f"- seed {s['seed']}" + (f" ({s['brightness']})" if s["brightness"] != "?" else "")
                   + ": Material 3 generates the scheme from it, so its colours are only known when rendered (`flutter_render.mjs` measures them)")
    if th["seeds"] and not known:
        out.append(f"### ColorScheme from a seed chosen at run time — `{th['seeds'][0]['file']}`")
        out.append("- the scheme is generated from a colour the app picks while running: only a render shows its colours")
    if th["textStyles"]:
        out.append(f"### TextTheme — `{th['textStyles'][0]['file']}`")
        out.append("- " + " · ".join(f"{s['style']} {s['size'] or '—'}" + (f" {s['weight']}" if s['weight'] else "") + (f" {s['color']}" if s['color'] else "")
                                     for s in th["textStyles"]))
    for pal in th["palettes"]:
        out.append(f"### `{pal['name']}` in `{pal['file']}`")
        out.append("- " + " · ".join(f"{k} {v}" for k, v in pal["colors"]))
    for sc in th["scales"]:
        out.append(f"### `{sc['name']}` in `{sc['file']}`")
        out.append("- " + " · ".join(f"{k} {v}" for k, v in sc["values"]))
    if th["extensions"]:
        out.append("### Theme extensions: " + ", ".join(f"`{e}`" for e in th["extensions"]) + " (read with `Theme.of(context).extension<T>()`)")
    if th["cupertino"]:
        out.append("### CupertinoThemeData — " + ", ".join(f"`{c['file']}` primary {c['primary']}" for c in th["cupertino"]))
    return out


def md_flutter_usage(fl: dict) -> list[str]:
    u = fl["usage"]
    out = []
    if u.get("steps"):
        out.append("- spacing from a scale: " + ", ".join(f"`{k}` ×{n}" for k, n in u["steps"]))
    if u["spacing"]:
        out.append(f"- spacing{' as bare numbers' if u.get('steps') else ''} (EdgeInsets, SizedBox gaps, Gap): " + ", ".join(f"{k} ×{n}" for k, n in u["spacing"]))
    if u["radius"]:
        out.append("- radius (BorderRadius.circular): " + ", ".join(f"{k} ×{n}" for k, n in u["radius"]))
    if u["fontSize"]:
        out.append("- font sizes set in widgets: " + ", ".join(f"{k} ×{n}" for k, n in u["fontSize"]))
    return out


FL_MOTION = {"flutter_animate": "flutter_animate", "rive": "Rive", "lottie": "Lottie", "animations": "animations"}


def flutter_stack(root: Path, ps: dict) -> dict:
    """detect_stack's answer for a Flutter app (or a pub workspace of them)."""
    deps = {**(ps.get("dependencies") or {}), **(ps.get("dev_dependencies") or {})} if isinstance(ps.get("dependencies"), dict) else {}
    is_app = "flutter" in deps and (root / "lib").is_dir()
    env = ps.get("environment") if isinstance(ps.get("environment"), dict) else {}
    router = next((label for key, label in FL_ROUTERS.items() if key in deps), None)
    return {
        "name": ps.get("name"), "depsSource": "pubspec.yaml", "framework": "Flutter" if is_app else None,
        "router": router, "react": None, "reactNative": None, "rnWeb": None, "vue": None, "svelte": None,
        "frameworkVersion": env.get("flutter") or None, "dartSdk": env.get("sdk"),
        "workspaceApps": [] if is_app else flutter_workspace_apps(root), "integrations": [],
        "tailwind": None, "tailwindMajor": None, "tailwindConfigFiles": [],
        "ui": sorted({label for key, label in FL_KITS.items() if key in deps and label}),
        "icons": sorted({"Cupertino icons" if k == "cupertino_icons" else "SVG assets (flutter_svg)" if k == "flutter_svg" else k for k in deps
                         if k in ("cupertino_icons", "font_awesome_flutter", "lucide_icons", "phosphor_flutter", "flutter_svg", "hugeicons")}),
        "motion": sorted({label for key, label in FL_MOTION.items() if key in deps}),
        "state": sorted({label for key, label in FL_STATE.items() if key in deps}),
        "shadcn": None, "typescript": False, "deps": {k: (v if isinstance(v, str) else "") for k, v in deps.items()},
    }


def flutter_start_here(root: Path, stack: dict) -> dict:
    ps = flutter_pubspec(root) or {}
    fl = flutter_start(root, ps)
    fl["root"] = str(root)
    files = _dart_files(root)
    th, app = fl["theme"], fl["app"]
    dark = None
    if app:
        tm = (app.get("themeMode") or "").strip()
        if app.get("darkTheme"):
            dark = ("a `darkTheme` beside the light one; " + (f"`themeMode: {tm}`" if tm else "no `themeMode`, so the device's setting picks")
                    + ". `flutter_render.mjs` renders both, the dark one under a dark platform brightness")
        elif app.get("theme") and re.search(r"Brightness|brightness", app.get("theme") or ""):
            dark = "the theme is built per brightness in code; `flutter_render.mjs` renders the dark one under a dark platform brightness"
        else:
            dark = "no `darkTheme`: a dark device shows the light theme"
    stack_notes = "references/stacks/flutter.md"
    render = ("render with `node <skill>/scripts/flutter_render.mjs <project>`: a widget test starts the app through its `main()`"
              + (f" (`{fl['rootWidget']}`)" if fl["rootWidget"] else "") + " at 375 / 768 / 1440, in light and dark and with text at 200 %, "
              "saves the screenshots, and measures the contrast of every text, tap targets and labels, and layout overflow, each with the widget's "
              "file and line; `--route /path` opens a route, `--tap` and `--enter` walk there, `--widget` pushes one screen")
    before = list(fl["stackBefore"])
    unmocked = [p for p in fl["plugins"] if p not in ("shared_preferences", "path_provider")]
    if unmocked:
        before.append("plugins a widget test has no platform for: " + ", ".join(f"`{p}`" for p in unmocked[:6])
                      + " — the harness mocks shared_preferences and path_provider; others need `--setup` (answer their channel) or `--widget … --standalone`")
    before.append(render)
    return {
        "vocabulary": [], "imported": dart_fanin(root, files, stack.get("name")), "pages": fl["pages"], "routes": fl["routes"],
        "layouts": fl["layouts"], "stackBefore": before, "theme": dark, "flutter": {**{k: fl[k] for k in (
            "theme", "usage", "mode", "fonts", "googleFonts", "fontFamilies", "platform", "rootWidget", "wraps", "appFile", "l10n", "template")},
            "appKind": app.get("kind") if app else None},
        "copy": flutter_copy(fl), "boot": {"files": [], "apiModule": None, "base": None}, "dev": {"proxies": [], "helpers": [], "scripts": {}},
        "gates": [], "kits": {"kits": [], "styled": None, "modules": None}, "kitDark": bool(app.get("darkTheme")) if app else False,
        "kitLook": True, "stackNotes": stack_notes, "kitNotes": None, "nuxtui": None, "locale": None,
        "widgets": sorted(n for n, f in _fl_class_index(files).items() if not n.startswith("_")
                          and {x.lower() for x in f.relative_to(root).parts[:-1]} & {"widgets", "widget", "components", "common", "shared", "core"})[:40],
        "dartFiles": len(files),
    }


# ------------------------------------------------------------ React Native / Expo
# A React Native app has no stylesheet and no HTML. Its look is a theme object (a colour map per scheme,
# a spacing scale), StyleSheet.create in each component, or NativeWind's classes; its pages are screens in
# navigators (React Navigation) or files in app/ (Expo Router); its dark mode follows the device. In a
# browser it runs through react-native-web, and that is what the renderer sees: a file's `.web.tsx` twin
# replaces it there, and a `Platform.OS === 'web'` branch is not what the phone shows.
RN_CODE = (".tsx", ".ts", ".jsx", ".js")
RN_PLATFORM = re.compile(r"\.(web|native|ios|android)$")
RN_THEME_DIRS = {"theme", "themes", "constants", "styles", "style", "tokens", "design", "colors", "colours", "design-system", "alf", "palette"}
RN_THEME_WORD = r"(?:colou?rs?|themes?|palette|tokens?|styles?|spacing|metrics|sizes|typography)"
RN_THEME_STEM = re.compile(r"^" + RN_THEME_WORD + r"|" + RN_THEME_WORD + r"(?:dark|light)?$|(?:^|[-_.])" + RN_THEME_WORD + r"(?:[-_.]|$)", re.I)
RN_NAMED = {"white", "black", "transparent"}
RN_BG_KEYS = ("background", "bg", "surface", "card", "base", "screen", "backgroundColor")
RN_TEXT_KEY = re.compile(r"text|^(?:foreground|fg|label|onBackground|onSurface|onSurfaceVariant|title|body|muted|subtle)$", re.I)
RN_SEMANTIC_FIRST = ("text", "background", "primary", "tint", "textSecondary", "textDim", "secondary", "surface", "card", "border",
                     "icon", "accent", "error", "success", "warning", "muted", "separator", "notification")
RN_NAV_KIND = [(re.compile(r"Drawer"), "drawer"), (re.compile(r"MaterialTopTab|TopTab"), "top tabs"),
               (re.compile(r"Tab"), "tabs"), (re.compile(r"Stack"), "stack")]
RN_KITS = {"react-native-paper": "React Native Paper", "tamagui": "Tamagui", "@tamagui/core": "Tamagui",
           "@gluestack-ui/themed": "gluestack-ui", "@rneui/themed": "React Native Elements", "@ui-kitten/components": "UI Kitten",
           "native-base": "NativeBase", "heroui-native": "HeroUI Native"}
RN_NATIVE_ONLY = {"react-native-maps": "maps", "react-native-vision-camera": "camera", "react-native-webview": "web views",
                  "@react-native-firebase/app": "Firebase (native SDK)", "react-native-nitro-modules": "Nitro modules",
                  "react-native-ble-plx": "Bluetooth", "@shopify/react-native-skia": "Skia (needs CanvasKit on the web)"}


def rn_app(root: Path, deps: dict) -> dict | None:
    """An Expo or bare React Native app: versions, the router, and what app.json says about the look."""
    if "react-native" not in deps and "expo" not in deps:
        return None
    cfg: dict = {}
    aj = root / "app.json"
    if aj.is_file():
        try:
            data = json.loads(read(aj))
            cfg = data.get("expo", data) if isinstance(data, dict) else {}
        except (json.JSONDecodeError, AttributeError):
            cfg = {}
    ui_style, web_output, plugin_fonts = cfg.get("userInterfaceStyle"), (cfg.get("web") or {}).get("output"), []
    for pl in cfg.get("plugins") or []:
        if isinstance(pl, list) and pl and pl[0] == "expo-font" and len(pl) > 1 and isinstance(pl[1], dict):
            plugin_fonts += [Path(str(x)).stem for x in pl[1].get("fonts") or []]
    for name in ("app.config.ts", "app.config.js"):
        t = read(root / name) if (root / name).is_file() else ""
        ui_style = ui_style or (re.search(r"userInterfaceStyle\s*:\s*['\"](\w+)['\"]", t) or [None, None])[1]
        web_output = web_output or (re.search(r"output\s*:\s*['\"](static|single|server)['\"]", t) or [None, None])[1]
    app_dir = None
    if "expo-router" in deps:
        custom = ((cfg.get("extra") or {}).get("router") or {}).get("root")     # expo.extra.router.root, else src/app, else app (Expo's order)
        for d in ([root / custom] if isinstance(custom, str) else []) + [root / "src" / "app", root / "app"]:
            if d.is_dir() and any(p.stem.startswith(("_layout", "index")) for p in d.iterdir() if p.is_file()):
                app_dir = d
                break
    router = "Expo Router" if app_dir else "React Navigation" if any(k.startswith("@react-navigation/") for k in deps) else None
    return {"expo": deps.get("expo"), "rn": deps.get("react-native"), "web": deps.get("react-native-web"), "router": router,
            "appDir": app_dir, "uiStyle": ui_style, "webOutput": web_output, "pluginFonts": plugin_fonts}


def _rn_twins(f: Path) -> list[str]:
    """The platform files beside a file: `index.web.tsx` next to `index.tsx`."""
    stem = RN_PLATFORM.sub("", f.stem)
    return sorted(p.name for p in f.parent.glob(f"{stem}.*.*") if p != f and RN_PLATFORM.search(p.stem) and p.suffix in RN_CODE
                  and RN_PLATFORM.sub("", p.stem) == stem)


def _rn_signals(text: str) -> list[str]:
    """What a screen holds: fields, a list, a modal or sheet, a form library, the data it fetches."""
    sig = []
    n = len(re.findall(r"<(?:TextInput|TextField|Input|Picker|Select|Switch|Checkbox|Slider|RadioButton\.Group|SegmentedButtons|ControlledInput)\b", text))
    if n:
        sig.append(f"{n} field{'s' if n > 1 else ''}")
    if re.search(r"\buseForm\(|<Formik\b|\buseAppForm\(|\bcreateFormHook\(", text):
        sig.append("form")
    if re.search(r"<(?:FlatList|FlashList|SectionList|LegendList|VirtualizedList)\b|\.map\(\s*\(?[\w{}, ]*\)?\s*=>\s*\(?\s*<", text):
        sig.append("list")
    if re.search(r"<(?:Modal|BottomSheet\w*|Dialog|Portal|Sheet|ActionSheet)\b", text):
        sig.append("modal")
    if re.search(r"<ScrollView\b|<KeyboardAwareScrollView\b|preset=\"scroll\"", text):
        sig.append("scrolls")
    data = list(dict.fromkeys(re.findall(r"\buse(\w+)Query\(|\buseQuery\(\s*\{?\s*queryKey:\s*\[\s*['\"]([\w-]+)", text)))
    names = [a or b for a, b in data][:2]
    if names:
        sig.append("data: " + ", ".join(f"`{x}`" for x in names))
    return sig


def _rn_components(text: str) -> list[str]:
    """The components a screen renders that are the app's own or a kit's: not React Native's primitives."""
    local, kit = set(), set()
    for names, spec in re.findall(r"import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", text):
        own = spec.startswith((".", "@/", "~/", "#/", "app/", "src/", "components", "@components")) or spec in RN_KITS
        if not own:
            continue
        for part in names.split(","):
            n = part.strip().split(" as ")[-1].strip()
            if re.match(r"^[A-Z]\w+$", n):
                (kit if spec in RN_KITS else local).add(n)
    for n, spec in re.findall(r"import\s+([A-Z]\w+)\s+from\s*['\"]([^'\"]+)['\"]", text):
        if spec.startswith((".", "@/", "~/", "#/", "app/", "src/", "components")):
            local.add(n)
    used = [t for t in dict.fromkeys(re.findall(r"(?<![\w.$])<([A-Z]\w*)", text)) if t in local or t in kit]
    return used[:6]


def _rn_layout_kind(root: Path, f: Path, text: str, aliases: list) -> str | None:
    """What an Expo Router layout renders around its pages: a stack, tabs, a drawer, or only a slot."""
    for pat, kind in ((r"<NativeTabs\b", "native tabs"), (r"<Tabs\b", "tabs"), (r"<Drawer\b", "drawer"), (r"<(?:Stack|JsStack)\b", "stack"),
                      (r"<Slot\b", "slot")):
        if re.search(pat, text):
            return kind
    for tag in re.findall(r"<([A-Z]\w+)\s*/>", text):         # <AppTabs />: one level down
        src = _js_source_of(root, f, text, tag, aliases)
        if src and src != f:
            t = read(src, 200_000)
            for pat, kind in ((r"<NativeTabs\b", "native tabs"), (r"<Tabs\b|<TabList\b", "tabs"), (r"<Drawer\b", "drawer"), (r"<Stack\b", "stack")):
                if re.search(pat, t):
                    twins = [x for x in _rn_twins(src) if ".web." in x]
                    return f"{kind} from `{rel(root, src)}`" + (f" (web: `{twins[0]}`)" if twins else "")
    return None


def _rn_redirects(text: str) -> list[str]:
    """A layout's guards: `if (cond) return <Redirect href="/login" />`, and Stack.Protected."""
    out = []
    for cond, href in re.findall(r"if\s*\(([^)]{1,90})\)\s*\{?\s*return\s*\(?\s*<Redirect\s+href=\{?\s*['\"]([^'\"]+)['\"]", text):
        out.append(f"a redirect to `{href}` when `{cond.strip()}`")
    for guard in re.findall(r"<Stack\.Protected\s+guard=\{([^}]{1,60})\}", text):
        out.append(f"`Stack.Protected` (guard `{guard.strip()}`)")
    return out


def expo_router_site(root: Path, app_dir: Path, aliases: list) -> dict:
    """Expo Router's file routes: pages with their URL, the layout around them and its redirects; API routes."""
    files = sorted(p for p in app_dir.rglob("*") if p.is_file() and p.suffix in RN_CODE and not set(p.relative_to(root).parts) & SKIP_DIRS
                   and not re.search(r"\.(test|spec|d)$", RN_PLATFORM.sub("", p.stem)) and "__tests__" not in p.parts)
    layouts: dict[Path, dict] = {}
    for p in files:
        if RN_PLATFORM.sub("", p.stem) == "_layout" and not RN_PLATFORM.search(p.stem):
            t = _no_comments(read(p, 200_000))
            layouts[p.parent] = {"file": p, "text": t, "kind": _rn_layout_kind(root, p, t, aliases), "guards": _rn_redirects(t),
                                 "lines": t.count("\n") + 1}
    pages, routes, apis = [], [], []
    for p in files:
        stem = RN_PLATFORM.sub("", p.stem)
        if stem == "_layout" or stem in ("+html", "+native-intent", "+middleware") or (RN_PLATFORM.search(p.stem) and (p.parent / (stem + p.suffix)).is_file()):
            continue
        if stem.endswith("+api"):
            apis.append("/" + "/".join([x for x in p.relative_to(app_dir).parent.parts if not x.startswith("(")] + [stem[:-4]]))
            continue
        segs = [x for x in p.relative_to(app_dir).parent.parts if not (x.startswith("(") and x.endswith(")"))]
        route = "(not found)" if stem == "+not-found" else "/" + "/".join(segs + ([] if stem == "index" else [stem]))
        t = own = read(p, 200_000)
        renders = None
        ex = re.search(r"export\s*\{\s*(?:default|(\w+)\s+as\s+default)\s*\}\s*from\s*['\"]([^'\"]+)['\"]", t) \
            or re.search(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"][\s\S]{0,80}export\s+default\s+\1\s*;?\s*$", t)
        if ex and t.count("\n") < 12:                  # a route file that hands the page to a screen elsewhere
            tgt = _js_resolve(root, p, ex.group(2), aliases)
            if tgt and ex.group(1):
                tgt = _ng_defines(root, tgt, ex.group(1), aliases, exts=JS_EXTS) or tgt
            if tgt and tgt.is_file():
                tt = read(tgt, 200_000)
                dn = re.search(r"export\s+default\s+(?:async\s+)?(?:function|class)\s+(\w+)", tt)
                renders = {"name": ex.group(1) or (dn.group(1) if dn else tgt.stem), "file": rel(root, tgt), "lines": tt.count("\n") + 1,
                           "signals": _rn_signals(tt)}
                t = tt
        chain = [layouts[d] for d in [p.parent, *p.parent.parents] if d in layouts and (d == app_dir or app_dir in d.parents)]
        inner = next((lay for lay in chain if lay["kind"] and lay["kind"] != "slot"), None)
        guards = [g for lay in chain for g in lay["guards"]]
        web_twin = next((x for x in _rn_twins(p) if ".web." in x), None)
        rec = {"file": rel(root, p), "lines": own.count("\n") + 1, "signals": [] if renders else _rn_signals(t), "classes": [],
               "components": _rn_components(t), "renders": renders, "route": f"`{route}`" + (f" (web: `{web_twin}`)" if web_twin else ""),
               "routeGuards": guards}
        if inner:
            rec["inside"] = {"name": f"{rel(root, inner['file'])} ({inner['kind']})", "file": None, "lines": inner["lines"], "holder": ""}
        pages.append(rec)
        routes.append((route, rel(root, p)))
    root_lay = layouts.get(app_dir)
    return {"pages": pages, "routes": routes, "apis": apis, "layouts": layouts, "rootLayout": root_lay}


def _jsx_conditions(body: str, i: int) -> list[str]:
    """The ternary and && branches of a navigator's JSX that hold position i: `isAuthenticated`, `!isAuthenticated`."""
    stack, j, quote = [], 0, None
    while j < i:
        ch = body[j]
        if quote:
            if ch == "\\":
                j += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch in "({":
            stack.append((ch, j))
        elif ch in ")}" and stack:
            stack.pop()
        j += 1
    out = []
    for k, (ch, pos) in enumerate(stack):
        if ch != "(":
            continue
        before = body[:pos].rstrip()
        opener = next((p for c, p in reversed(stack[:k]) if c == "{"), None)
        if opener is None:
            continue
        expr = body[opener + 1:pos]
        if before.endswith("?"):
            out.append(re.sub(r"\s+", " ", expr.rstrip()[:-1].strip())[:50])
        elif before.endswith(":"):
            cond = expr.split("?", 1)[0].strip()
            out.append("!" + re.sub(r"\s+", " ", cond)[:50] if cond else "")
        elif before.endswith("&&"):
            out.append(re.sub(r"\s+", " ", expr.rstrip()[:-2].strip())[:50])
    return [c for c in out if c]


def _rn_linking(root: Path, code_files: list[Path]) -> dict[str, str]:
    """React Navigation's linking config: screen name → the URL path the web shows for it."""
    paths: dict[str, str] = {}

    def walk(body: str, prefix: str) -> None:
        for name, v in _fields(body).items():
            s = _unquote(v)
            if s is not None:
                paths.setdefault(name, _join_route(prefix, s))
            elif v.startswith("{"):
                inner = _fields(_balanced(v, 0))
                p = _unquote(inner.get("path"))
                here = _join_route(prefix, p) if p is not None else prefix
                if p is not None:
                    paths.setdefault(name, here)
                if inner.get("screens", "").startswith("{"):
                    walk(_balanced(inner["screens"], 0), here)

    for f in code_files:
        t = read(f, 300_000)
        if "screens" not in t or not re.search(r"\blinking\b|\bprefixes\b|getStateFromPath|LinkingOptions", t):
            continue
        t = _no_comments(t)
        for m in re.finditer(r"\b(?:config|linking)\s*[:=]\s*(?:\{\s*(?:[^{}]*?\bconfig\s*:\s*)?)?\{\s*(?:initialRouteName\s*:[^,]+,\s*)?screens\s*:\s*\{", t):
            walk(_balanced(t, m.end() - 1), "/")
    return paths


def _rn_jsx_screens(code: str, nav: str) -> list[dict]:
    """The `<Nav.Screen>` elements in code: name, the component (component=, getComponent=, a child render function),
    and the branch of a ternary or && that holds each."""
    out = []
    for sm in re.finditer(r"<" + re.escape(nav) + r"\.Screen\b", code):
        attrs, _, _ = _jsx_attrs(code, sm.end())
        raw = _jsx_attr(attrs, "name") or ""
        sname = _unquote(raw) or (re.search(r"['\"]([^'\"]+)['\"]", raw) or [None, raw.strip("{} ")])[1]
        comp = _jsx_attr(attrs, "component") or ""
        if not comp:
            gc = _jsx_attr(attrs, "getComponent") or ""
            rq = re.search(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)(?:\.(\w+))?", gc)
            comp = f"require:{rq.group(1)}" if rq else (re.search(r"=>\s*(\w+)", gc) or [None, ""])[1]
        if not comp:                                 # <Stack.Screen name="X">{(props) => <XScreen {...props} />}</Stack.Screen>
            cm = re.search(r">\s*\{\s*\(?[^)]*\)?\s*=>\s*<([A-Z]\w*)", code[sm.end():sm.end() + 400])
            comp = cm.group(1) if cm else ""
        out.append({"name": sname, "comp": comp.strip("{} "), "conds": _jsx_conditions(code, sm.start()), "link": None})
    return out


def rn_navigation(root: Path, src_files: list[Path], aliases: list) -> dict:
    """React Navigation's screens: each navigator (stack, tabs, drawer) and the screen files it shows, with the
    branch of an auth ternary that holds them, the navigator that contains a nested one, and the linking path."""
    code_files = [p for p in _code_files(src_files, RN_CODE)]
    navs: dict[str, dict] = {}                  # navigator const → {file, kind, screens: [...]}
    for f in code_files:
        t = read(f, 300_000)
        if ".Screen" not in t and "screens" not in t:
            continue
        code = _no_comments(t)
        for m in re.finditer(r"(?:const|let|var)\s+(\w+)\s*(?::[^=]{1,80})?=\s*(create\w*Navigator\w*)\s*(?:<[^>]*>)?\s*\(", code):
            name, fn = m.group(1), m.group(2)
            kind = next((k for pat, k in RN_NAV_KIND if pat.search(fn)), "stack")
            nav = {"name": name, "file": f, "kind": kind, "screens": [], "initial": None}
            args = _balanced(code, m.end() - 1).strip()
            if args.startswith("{"):                # the static API: createNativeStackNavigator({ screens: { … } })
                fl = _fields(_balanced(args, 0))
                nav["initial"] = _unquote(fl.get("initialRouteName"))
                if fl.get("screens", "").startswith("{"):
                    for sname, v in _fields(_balanced(fl["screens"], 0)).items():
                        if sname.startswith("..."):
                            continue
                        comp, link = v, None
                        if re.match(r"create\w*Screen\s*\(", v):
                            v = _balanced(v, v.index("(")).strip()
                        if v.startswith("{"):
                            inner = _fields(_balanced(v, 0))
                            comp = inner.get("screen", "")
                            link = _unquote(inner.get("linking")) if inner.get("linking") else None
                            if link is None and (inner.get("linking") or "").startswith("{"):
                                link = _unquote(_fields(_balanced(inner["linking"], 0)).get("path"))
                        nav["screens"].append({"name": sname, "comp": comp.strip(), "conds": [], "link": link})
            else:                                   # the dynamic API: <Stack.Screen name="…" component={…} />
                nav["screens"] = _rn_jsx_screens(code, name)
                im = re.search(r"<" + re.escape(name) + r"\.Navigator\b", code)
                if im:
                    attrs, _, _ = _jsx_attrs(code, im.end())
                    ini = _jsx_attr(attrs, "initialRouteName") or ""
                    nav["initial"] = _unquote(ini) or ini.strip("{} ")[:60] or None
            if nav["screens"]:
                navs[name + "@" + str(f)] = nav
        # Screens a function adds to whichever navigator it is handed: function commonScreens(Stack) { <Stack.Screen … }
        declared = set(re.findall(r"(?:const|let|var)\s+(\w+)\s*(?::[^=]{1,80})?=\s*create\w*Navigator", code))
        for fm in re.finditer(r"function\s+(\w+)\s*\(\s*(\w+)\s*[:,)]", code):
            fname, param = fm.group(1), fm.group(2)
            brace = code.find("{", fm.end())
            if param in declared or brace < 0:
                continue
            body = _balanced(code, brace)
            if not re.search(r"<" + re.escape(param) + r"\.Screen\b", body):
                continue
            users = [n for n in declared if re.search(re.escape(fname) + r"\(\s*" + re.escape(n) + r"\b", code)]
            navs[fname + "@" + str(f)] = {"name": fname, "file": f, "kind": f"shared by {len(users)} navigators" if users else "shared screens",
                                          "screens": _rn_jsx_screens(body, param), "initial": None}
    links = _rn_linking(root, code_files)
    by_file: dict[Path, list[dict]] = {}
    for n in navs.values():
        by_file.setdefault(n["file"], []).append(n)
    screens: list[dict] = []
    nested: dict[int, tuple[dict, dict]] = {}      # id(child navigator) → (parent navigator, the screen that holds it)
    resolved: list[tuple[dict, dict, Path | None, bool]] = []
    for nav in navs.values():
        code = _no_comments(read(nav["file"], 300_000))
        for s in nav["screens"]:
            comp = s["comp"]
            if comp.startswith("require:"):
                f = _js_resolve(root, nav["file"], comp[8:], aliases)
            else:
                f = _js_source_of(root, nav["file"], code, comp.split(".")[0] if comp else None, aliases) if comp else None
            children = []
            if f and f != nav["file"] and f in by_file:            # a navigator in its own file
                children = by_file[f]
            elif f and f == nav["file"] and comp:                   # a function in this file that renders a navigator
                fm = re.search(r"(?:function\s+" + re.escape(comp) + r"\s*\(|(?:const|let)\s+" + re.escape(comp) + r"\s*=\s*(?:\([^)]*\)|\w+)\s*=>)", code)
                body = _balanced(code, code.find("{", fm.end())) if fm and code.find("{", fm.end()) >= 0 else ""
                children = [n for n in by_file.get(f, []) if n is not nav and re.search(r"<" + re.escape(n["name"]) + r"\.Navigator\b", body)]
            for c in children:
                nested[id(c)] = (nav, s)
            resolved.append((nav, s, f, bool(children)))
    for nav, s, f, holds_nav in resolved:
        if holds_nav:
            continue                                  # a navigator inside a navigator: its own screens are the pages
        screens.append({"nav": nav, "screen": s, "file": f, "parent": nested.get(id(nav)),
                        "link": s["link"] if s["link"] is not None else links.get(s["name"])})
    # URLs from a route table the app keeps itself (`new Router({ Home: '/', Profile: '/profile/:name' })`)
    if sum(1 for sc in screens if sc["link"] is None) >= 3:
        names = {sc["screen"]["name"] for sc in screens}
        for f in code_files:
            t = read(f, 300_000)
            if t.count("'/") + t.count('"/') < 5:
                continue
            for body in _rn_objects(_no_comments(t)).values():
                fl = _fields(body)
                paths = {k: (_unquote(v) or _unquote((_split_top(v[1:-1]) or [""])[0]) if v.startswith("[") else _unquote(v)) for k, v in fl.items() if k in names}
                paths = {k: v for k, v in paths.items() if v and v.startswith("/")}
                if len(paths) >= 5:
                    for sc in screens:
                        if sc["link"] is None and sc["screen"]["name"] in paths:
                            sc["link"] = paths[sc["screen"]["name"]]
                    links.update(paths)
                    break
    has_prop = any(re.search(r"<NavigationContainer\b[^>]*\blinking=", read(f, 300_000)) for f in code_files[:400])
    return {"navs": list(navs.values()), "screens": screens,
            "linking": bool(links) or has_prop or any(s["link"] is not None for n in navs.values() for s in n["screens"])}


def rn_screen_pages(root: Path, nav: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """React Navigation screens as page lines: the file, its URL (linking), the navigator, the branch it is in."""
    pages, routes, seen = [], [], set()
    for sc in nav["screens"]:
        f = sc["file"]
        if not f or not f.is_file() or f in seen:
            continue
        seen.add(f)
        t = read(f, 200_000)
        n, s = sc["nav"], sc["screen"]
        link = sc["link"] if sc["link"] is None or sc["link"].startswith("/") else _join_route("/", sc["link"])
        where = f"`{link}`" if link is not None else "no URL"
        twins = [x for x in _rn_twins(f) if ".web." in x]
        rec = {"file": rel(root, f), "lines": t.count("\n") + 1, "signals": _rn_signals(t), "classes": [], "components": _rn_components(t),
               "renders": None, "route": f"`{s['name']}` · {where}" + (f" (web: `{twins[0]}`)" if twins else ""), "routeGuards": []}
        conds = list(s["conds"])
        parent = sc["parent"]
        label = f"{n['name']} ({n['kind']})" + (f" in {parent[0]['name']} ({parent[0]['kind']}) as `{parent[1]['name']}`" if parent else "")
        nt = read(n["file"], 200_000)
        rec["inside"] = {"name": label, "file": rel(root, n["file"]), "lines": nt.count("\n") + 1, "holder": "navigator"}
        if parent:
            conds += parent[1]["conds"]
        if conds:
            rec["when"] = "shown when " + " and ".join(f"`{c}`" for c in dict.fromkeys(conds))
        pages.append(rec)
        routes.append((link if link is not None else f"({s['name']})", rel(root, f)))
    return pages, routes


# --- the theme: colour maps (one per scheme), spacing and radius scales, a kit's theme
def _rn_rgb(v: str) -> tuple[float, float, float, float] | None:
    v = v.strip().lower()
    if v in ("white", "black"):
        return (255, 255, 255, 1) if v == "white" else (0, 0, 0, 1)
    m = re.match(r"^#([0-9a-f]{3,8})$", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255 if len(h) == 8 else 1)
    m = re.match(r"^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+%?))?\s*\)$", v)
    if m:
        a = m.group(4)
        alpha = (float(a[:-1]) / 100 if a.endswith("%") else float(a)) if a else 1
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)), alpha)
    return None


def _rn_contrast(fg: str, bg: str) -> float | None:
    a, b = _rn_rgb(fg), _rn_rgb(bg)
    if not a or not b or b[3] < 1:
        return None
    if a[3] < 1:
        a = tuple(a[k] * a[3] + b[k] * (1 - a[3]) for k in range(3)) + (1,)

    def lum(c):
        f = [x / 255 for x in c[:3]]
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in f]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 1)


def _rn_is_color(v: str | None) -> bool:
    return bool(v) and (bool(re.match(r"^(?:#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\))$", v.strip())) or v.strip().lower() in RN_NAMED)


def _rn_objects(code: str) -> dict[str, str]:
    """Top-level object literals by name: `const X = {…}`, `export default {…}` (as `default`), `module.exports = {…}`,
    and an object handed to a theme factory (`createTheme({…})` as X)."""
    out: dict[str, str] = {}
    for m in re.finditer(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=\n]{1,80})?=\s*(?:new\s+)?(?:[\w.]+\s*(?:<[^>()]*>)?\s*\(\s*)?\{", code, re.M):
        out.setdefault(m.group(1), _balanced(code, m.end() - 1))
    m = re.search(r"^export\s+default\s+(?:\w+\s*\(\s*)?\{", code, re.M) or re.search(r"^module\.exports\s*=\s*\{", code, re.M)
    if m:
        out.setdefault("default", _balanced(code, m.end() - 1))
    return out


class _RNResolver:
    """Resolves a theme value to a literal: `palette.neutral800`, `colors.primary[400]`, an imported object's key."""

    def __init__(self, root: Path, aliases: list):
        self.root, self.aliases, self.cache = root, aliases, {}

    def objects(self, f: Path) -> tuple[str, dict[str, str]]:
        if f not in self.cache:
            code = _no_comments(read(f, 300_000))
            self.cache[f] = (code, _rn_objects(code))
        return self.cache[f]

    def value(self, f: Path, expr: str, depth: int = 0) -> str | None:
        expr = expr.strip().rstrip(",").strip()
        if depth > 4 or not expr:
            return None
        s = _unquote(expr)
        if s is not None:
            return s
        if re.match(r"^-?[\d.]+$", expr):
            return expr
        m = re.match(r"^([A-Za-z_$][\w$]*)((?:\.[\w$]+|\[\s*['\"]?[\w$-]+['\"]?\s*\])*)(?:\s+as\s+const)?$", expr)
        if not m:
            return None
        base, path = m.group(1), [x for x in re.findall(r"\.([\w$]+)|\[\s*['\"]?([\w$-]+)['\"]?\s*\]", m.group(2))]
        keys = [a or b for a, b in path]
        code, objs = self.objects(f)
        if base in objs:
            return self._walk(f, objs[base], keys, depth)
        cm = re.search(r"(?:const|let|var)\s+" + re.escape(base) + r"\s*=\s*(['\"][^'\"]*['\"]|[\w.$\[\]'\"]+)\s*;?\s*$", code, re.M)
        if cm and not keys:
            return self.value(f, cm.group(1), depth + 1)
        src = _js_source_of(self.root, f, code, base, self.aliases)
        if src and src != f and src.is_file():
            code2, objs2 = self.objects(src)
            dm = re.search(r"import\s+" + re.escape(base) + r"\s+from", code)
            name = "default" if dm else base
            if name in objs2:
                return self._walk(src, objs2[name], keys, depth + 1)
            if name == "default":
                em = re.search(r"export\s+default\s+(\w+)", code2)
                if em and em.group(1) in objs2:
                    return self._walk(src, objs2[em.group(1)], keys, depth + 1)
        return None

    def _walk(self, f: Path, body: str, keys: list[str], depth: int) -> str | None:
        cur = body
        for k in keys:
            fl = _fields(cur)
            v = fl.get(k)
            if v is None:                            # a spread base: `...DefaultTheme.colors` is not ours to read
                return None
            if v.startswith("{"):
                cur = _balanced(v, 0)
                continue
            return self.value(f, v, depth + 1)
        return None

    def flat(self, f: Path, body: str, depth: int = 0) -> tuple[list[tuple[str, str]], list[str], list[str]]:
        """A map's colour entries (resolved), the nested scales in it, and the bases it spreads."""
        colors, scales = [], []
        spreads = [x[3:].strip() for x in _split_top(body) if x.startswith("...")]      # `...DefaultTheme.colors`: a base theme
        for k, v in _fields(body).items():
            if v.startswith("{"):
                inner = _fields(_balanced(v, 0))
                if sum(1 for x in inner.values() if _rn_is_color(self.value(f, x, depth + 1) or "")) >= 3:
                    mid = inner.get("500") or inner.get("DEFAULT") or list(inner.values())[len(inner) // 2]
                    scales.append(f"{k} {self.value(f, mid, depth + 1) or '?'}")
                continue
            r = self.value(f, v, depth + 1)
            if r and _rn_is_color(r):
                colors.append((k, r))
        return colors, scales, spreads


RN_BASE_THEMES = {    # the colours a theme spread over these starts from (React Navigation 7, React Native Paper's MD3 baseline)
    ("@react-navigation/native", "DefaultTheme"): {"primary": "rgb(0, 122, 255)", "background": "rgb(242, 242, 242)", "card": "rgb(255, 255, 255)",
                                                   "text": "rgb(28, 28, 30)", "border": "rgb(216, 216, 216)", "notification": "rgb(255, 59, 48)"},
    ("@react-navigation/native", "DarkTheme"): {"primary": "rgb(10, 132, 255)", "background": "rgb(1, 1, 1)", "card": "rgb(18, 18, 18)",
                                                "text": "rgb(229, 229, 231)", "border": "rgb(39, 39, 41)", "notification": "rgb(255, 69, 58)"},
    ("react-native-paper", "MD3LightTheme"): {"primary": "rgb(103, 80, 164)", "onPrimary": "rgb(255, 255, 255)", "background": "rgb(255, 251, 254)",
                                              "onBackground": "rgb(28, 27, 31)", "surface": "rgb(255, 251, 254)", "onSurface": "rgb(28, 27, 31)",
                                              "onSurfaceVariant": "rgb(73, 69, 79)", "outline": "rgb(121, 116, 126)", "error": "rgb(179, 38, 30)"},
    ("react-native-paper", "MD3DarkTheme"): {"primary": "rgb(208, 188, 255)", "onPrimary": "rgb(56, 30, 114)", "background": "rgb(28, 27, 31)",
                                             "onBackground": "rgb(230, 225, 229)", "surface": "rgb(28, 27, 31)", "onSurface": "rgb(230, 225, 229)",
                                             "onSurfaceVariant": "rgb(202, 196, 208)", "outline": "rgb(147, 143, 153)", "error": "rgb(242, 184, 181)"},
}
RN_BASE_THEMES[("expo-router", "DefaultTheme")] = RN_BASE_THEMES[("@react-navigation/native", "DefaultTheme")]
RN_BASE_THEMES[("expo-router", "DarkTheme")] = RN_BASE_THEMES[("@react-navigation/native", "DarkTheme")]


def _rn_base_colors(code: str, spreads: list[str]) -> tuple[str, dict[str, str]] | None:
    """The library theme a map spreads (`...DarkTheme.colors`, imported as itself or renamed) and its colours."""
    for sp in spreads:
        local = sp.split(".")[0]
        for names, spec in re.findall(r"import\s*\{([^}]*)\}\s*from\s*['\"](@react-navigation/native|expo-router|react-native-paper)['\"]", code):
            for part in names.split(","):
                bits = [x.strip() for x in part.split(" as ")]
                if bits[-1] == local and (spec, bits[0]) in RN_BASE_THEMES:
                    return bits[0], RN_BASE_THEMES[(spec, bits[0])]
    return None


def _rn_lib_spreads(code: str, spreads: list[str]) -> list[str]:
    """The library themes a map is made of: `...LightTheme.colors` from react-native-paper → "React Native Paper's `LightTheme`"."""
    libs = {"@react-navigation/native": "React Navigation", "expo-router": "React Navigation", "react-native-paper": "React Native Paper",
            "@react-navigation/native-stack": "React Navigation"}
    out, adapted = [], {}
    for names, spec in re.findall(r"import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", code):
        for part in names.split(","):
            bits = [x.strip() for x in part.split(" as ")]
            if spec in libs and bits[-1]:
                adapted[bits[-1]] = f"{libs[spec]}'s `{bits[0]}`"
    for names in re.findall(r"const\s*\{([^}]*)\}\s*=\s*adaptNavigationTheme\(", code):     # Paper's adapter over React Navigation's
        for part in names.split(","):
            bits = [x.strip() for x in part.split(":")]
            adapted[bits[-1]] = f"React Navigation's theme adapted by Paper (`{bits[0]}`)"
    for sp in spreads:
        hit = adapted.get(sp.split(".")[0])
        if hit and hit not in out:
            out.append(hit)
    return out


def _rn_order(colors: list[tuple[str, str]]) -> list[tuple[str, str]]:
    first = {k: i for i, k in enumerate(RN_SEMANTIC_FIRST)}
    return sorted(colors, key=lambda kv: first.get(kv[0], len(first)))


def _rn_pair_name(name: str) -> tuple[str, str] | None:
    """`lightTheme` → (theme, light); `colorsDark` → (colors, dark); `DarkTheme` → (Theme, dark)."""
    m = re.match(r"^(light|dark|Light|Dark|LIGHT|DARK)_?(\w*)$", name) or re.match(r"^(\w*?)_?(Light|Dark|light|dark|LIGHT|DARK)$", name)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if a.lower() in ("light", "dark"):
        return (b.lower() or "theme", a.lower())
    return (a.lower() or "theme", b.lower())


def rn_theme(root: Path, src_files: list[Path], aliases: list) -> dict:
    """Where the app's look is declared: colour maps (light and dark when both exist), scales, the fonts it loads."""
    res = _RNResolver(root, aliases)
    cands = []
    for p in _code_files(src_files, RN_CODE):
        rp = p.relative_to(root)
        dirs = {x.lower() for x in rp.parts[:-1]}
        if dirs & RN_THEME_DIRS or RN_THEME_STEM.search(RN_PLATFORM.sub("", p.stem)):
            if re.search(r"\.(test|spec|stories)$", p.stem) or dirs & {"__tests__", "node_modules"}:
                continue
            cands.append(p)
    maps: list[dict] = []
    scales: list[dict] = []
    bases: list[dict] = []
    for f in cands[:40]:
        code, objs = res.objects(f)
        for name, body in objs.items():
            fl = _fields(body)
            if "light" in fl and "dark" in fl and fl["light"].startswith("{") and fl["dark"].startswith("{"):
                lc, _, _ = res.flat(f, _balanced(fl["light"], 0))
                dc, _, _ = res.flat(f, _balanced(fl["dark"], 0))
                if len(lc) >= 3:
                    maps.append({"file": f, "name": name, "light": lc, "dark": dc, "scales": [], "spreads": [], "pair": True})
                    continue
            target = body
            label = name
            if "colors" in fl and fl["colors"].startswith("{"):
                target, label = _balanced(fl["colors"], 0), f"{name}.colors"
            colors, sc, spreads = res.flat(f, target)
            if not colors and not sc and spreads and label.endswith(".colors"):
                libs = _rn_lib_spreads(code, spreads)
                if libs:
                    bases.append({"file": f, "name": label[:-7], "bases": libs})
                    continue
            base = _rn_base_colors(code, spreads)
            if base:                                   # the rest of the map is the library theme's: fill it in
                have = {k for k, _ in colors}
                colors += [(k, v) for k, v in base[1].items() if k not in have]
                spreads = [base[0]]
            if len(colors) >= 3 or len(sc) >= 2 or (spreads and colors):
                maps.append({"file": f, "name": label, "light": colors, "dark": [], "scales": sc, "spreads": spreads, "pair": False})
            nums = [(k, _lit(v)) for k, v in fl.items() if _lit(v) and re.match(r"^-?[\d.]+$", _lit(v) or "")]
            if len(nums) >= 4 and re.search(r"spacing|space|gap|size|radi|rounded|inset", name, re.I):
                scales.append({"file": f, "name": name, "values": nums[:10]})
            for key in ("spacing", "space", "radii", "radius", "borderRadius", "fontSize", "fontSizes"):
                if key in fl and fl[key].startswith("{"):
                    inner = [(k, _lit(v)) for k, v in _fields(_balanced(fl[key], 0)).items() if _lit(v) and re.match(r"^-?[\d.]+$", _lit(v) or "")]
                    if len(inner) >= 3:
                        scales.append({"file": f, "name": f"{name}.{key}", "values": inner[:10]})
    # Pair maps kept apart: `colors` in colors.ts with `colors` in colorsDark.ts; lightTheme / darkTheme.
    paired: list[dict] = []
    used = set()
    for i, a in enumerate(maps):
        if a["pair"] or i in used:
            continue
        for j, b in enumerate(maps):
            if j <= i or j in used or b["pair"]:
                continue
            same_name = a["name"] == b["name"] and a["file"] != b["file"] and \
                re.sub(r"[-_.]?dark", "", a["file"].stem, flags=re.I).lower() == re.sub(r"[-_.]?dark", "", b["file"].stem, flags=re.I).lower() and \
                ("dark" in a["file"].stem.lower()) != ("dark" in b["file"].stem.lower())
            pa, pb = _rn_pair_name(a["name"].split(".")[0]), _rn_pair_name(b["name"].split(".")[0])
            by_name = pa and pb and pa[0] == pb[0] and pa[1] != pb[1]
            if same_name or by_name:
                light, dark = (a, b) if ("dark" in b["file"].stem.lower() if same_name else pb[1] == "dark") else (b, a)
                paired.append({"file": light["file"], "darkFile": dark["file"], "name": light["name"] + (f" / {dark['name']}" if light["name"] != dark["name"] else ""),
                               "light": light["light"], "dark": dark["light"], "scales": light["scales"], "spreads": light["spreads"], "pair": True})
                used |= {i, j}
                break
    maps = [m for k, m in enumerate(maps) if k not in used] + paired
    # The one to print first: a pair with the most semantic keys, then single maps; palettes (numbered keys) last.
    def weight(m):
        sem = sum(1 for k, _ in m["light"] if not re.search(r"\d", k))
        return (not m["pair"], -sem, -len(m["scales"]))
    maps.sort(key=weight)
    semantic = [m for m in maps if any(not re.search(r"\d", k) for k, _ in m["light"]) or m["scales"]]
    palettes = [m for m in maps if m not in semantic] if semantic else []
    return {"maps": (semantic or maps)[:4], "palettes": [(m["name"], m["file"], len(m["light"])) for m in palettes][:3], "scales": scales[:4],
            "bases": bases[:3]}


def rn_theme_contrast(m: dict) -> list[str]:
    """The text keys of a colour map against its background, per scheme (WCAG 1.4.3: 4.5:1)."""
    light, dark = dict(m["light"]), dict(m.get("dark") or [])
    bg = next((k for k in RN_BG_KEYS if k in light), None)
    if not bg:
        return []
    out = []
    for k in [k for k in light if RN_TEXT_KEY.search(k) and k != bg][:4]:
        a = _rn_contrast(light[k], light[bg])
        b = _rn_contrast(dark[k], dark[bg]) if k in dark and bg in dark else None
        if a is None:
            continue
        out.append(f"{k} {a}" + (f" / {b}" if b is not None else "") + (" ✗" if a < 4.5 or (b is not None and b < 4.5) else ""))
    lines = [f"text on `{bg}` ({'light / dark' if dark else 'light'}, 4.5:1 needed): " + " · ".join(out)] if out else []
    on = []                                       # Material's pairs: onPrimary on primary, onSurface on surface
    for k in [k for k in light if re.match(r"^on[A-Z]", k)]:
        base = k[2].lower() + k[3:]
        if base in light and base != bg:
            a = _rn_contrast(light[k], light[base])
            b = _rn_contrast(dark[k], dark[base]) if k in dark and base in dark else None
            if a is not None:
                on.append(f"{k} on {base} {a}" + (f" / {b}" if b is not None else "") + (" ✗" if a < 4.5 or (b is not None and b < 4.5) else ""))
    if on:
        lines.append("content on its colour (4.5:1 for text on it): " + " · ".join(on[:5]))
    return lines


def rn_style_usage(root: Path, src_files: list[Path], theme_files: set[Path]) -> dict:
    """How components style themselves: StyleSheet, inline styles, NativeWind classes; the numbers and colours they use."""
    fsz, rad, spc, lit_col, theme_col = (collections.Counter() for _ in range(5))
    sheets = inline = class_names = files = typed = 0
    for p in _code_files(src_files, (".tsx", ".jsx", ".ts", ".js")):
        if p in theme_files or re.search(r"\.(test|spec|stories)$", p.stem):
            continue
        t = read(p, 200_000)
        if "react-native" not in t and "StyleSheet" not in t and "style=" not in t:
            continue
        files += 1
        sheets += "StyleSheet.create" in t
        typed += bool(re.search(r":\s*(?:ThemedStyle<\s*)?(?:ViewStyle|TextStyle|ImageStyle)\b", t))
        inline += len(re.findall(r"style=\{\{", t))
        class_names += len(re.findall(r"\bclassName=", t))
        for v in re.findall(r"\bfontSize\s*:\s*([\w.\[\]'\"]+)", t):
            fsz[v.strip("'\"")] += 1
        for v in re.findall(r"\bborderRadius\s*:\s*([\w.\[\]'\"]+)", t):
            rad[v.strip("'\"")] += 1
        for v in re.findall(r"\b(?:padding|margin)(?:Horizontal|Vertical|Top|Bottom|Left|Right|Start|End)?\s*:\s*([\w.\[\]'\"]+)|\b(?:gap|rowGap|columnGap)\s*:\s*([\w.\[\]'\"]+)", t):
            x = (v[0] or v[1]).strip("'\"")
            if x not in ("0", "auto", "undefined"):
                spc[x] += 1
        for v in re.findall(r"\b(?:color|backgroundColor|borderColor|tintColor|borderTopColor|borderBottomColor|shadowColor|placeholderTextColor)\s*[:=]\s*\{?\s*['\"](#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|white|black)['\"]", t):
            lit_col[v.lower()] += 1
        for v in re.findall(r"\b(?:theme\.colors|colors|Colors\[[^\]]{1,40}\]|palette|theme)\.([A-Za-z]\w*)", t):
            if v not in ("palette", "colors", "spacing", "typography"):
                theme_col[v] += 1
    return {"files": files, "sheets": sheets, "typed": typed, "inline": inline, "classNames": class_names,
            "fontSize": fsz.most_common(6), "radius": rad.most_common(5), "spacing": spc.most_common(8),
            "literalColors": sum(lit_col.values()), "literalTop": lit_col.most_common(4),
            "themeColors": sum(theme_col.values()), "themeTop": theme_col.most_common(6)}


def rn_fonts(root: Path, src_files: list[Path], deps: dict, app: dict) -> list[str]:
    """The faces the app loads: useFonts / Font.loadAsync, @expo-google-fonts packages, the expo-font plugin."""
    loaded: dict[str, str] = {}
    where: list[str] = []
    for p in _code_files(src_files, RN_CODE):
        t = read(p, 200_000)
        bodies = [_balanced(t, m.end() - 1) for m in re.finditer(r"\b(?:useFonts|loadAsync)\(\s*\{", t)]
        for name in re.findall(r"\b(?:useFonts|loadAsync)\(\s*([A-Za-z_]\w*)\s*\)", t):
            src = _js_source_of(root, p, t, name, ts_aliases(root))
            objs = _rn_objects(_no_comments(read(src, 200_000))) if src else {}
            if name in objs:
                bodies.append(objs[name])
        for body in bodies:
            for k, v in _fields(body).items():
                if k.startswith("..."):
                    continue
                rq = re.search(r"require\(\s*['\"]([^'\"]+)['\"]", v)
                loaded.setdefault(k.strip("'\""), Path(rq.group(1)).name if rq else v.strip()[:40])
            if rel(root, p) not in where:
                where.append(rel(root, p))
    out = []
    if loaded:
        out.append("`useFonts` in " + ", ".join(f"`{w}`" for w in where[:3]) + ": " + ", ".join(f"{k} (`{v}`)" if v.endswith((".ttf", ".otf")) else k for k, v in list(loaded.items())[:6]))
    g = sorted(k for k in deps if k.startswith("@expo-google-fonts/"))
    if g:
        out.append("bundled from npm (no network needed): " + ", ".join(f"`{k}`" for k in g))
    if app.get("pluginFonts"):
        out.append("the expo-font plugin embeds " + ", ".join(app["pluginFonts"][:4]) + " in the native build; the web loads a face only through `useFonts`")
    return out


def rn_dark(root: Path, src_files: list[Path], app: dict, deps: dict) -> tuple[str | None, bool]:
    """How dark mode switches: the device's scheme (useColorScheme), an app setting kept in storage, or not at all."""
    n_scheme, stored, nativewind, mmkv_id = 0, None, False, "mmkv.default"
    for p in _code_files(src_files, RN_CODE):
        t = read(p, 200_000)
        if re.search(r"\buseColorScheme\s*\(|\bAppearance\.getColorScheme\(|\buseTheme\(\)\.dark\b|\bcolorScheme\b|\buseUniwind\s*\(", t):
            n_scheme += 1
        m = re.search(r"useMMKV(?:String|Boolean)?\(\s*['\"]([^'\"]*(?:theme|scheme|mode|appearance)[^'\"]*)['\"]", t, re.I) \
            or re.search(r"(?:const|let)\s+\w*THEME\w*\s*=\s*['\"]([\w.:-]+)['\"]", t)
        if m and not stored:
            mmkv = "MMKV" in t or "mmkv" in t
            stored = (m.group(1), mmkv)
        nativewind = nativewind or bool(re.search(r"\bcolorScheme\.set\(|\bsetColorScheme\(|Uniwind\.setTheme\(", t))
        idm = re.search(r"(?:new\s+MMKV|createMMKV)\(\s*\{[^}]*\bid\s*:\s*['\"]([^'\"]+)['\"]", t)
        if idm:
            mmkv_id = idm.group(1)
    if not n_scheme and not stored:
        return None, False
    bits = [f"follows the device's scheme (read in {n_scheme} file{'s' if n_scheme > 1 else ''})" if n_scheme else "chosen in the app"]
    if stored:
        key = f"{mmkv_id}\\{stored[0]}" if stored[1] else stored[0]
        bits.append(f"a choice the user makes is kept in {'MMKV' if stored[1] else 'storage'} `{stored[0]}` (on the web: localStorage `{key}`)")
    if app.get("uiStyle") in ("light", "dark"):
        bits.append(f"app.json sets `userInterfaceStyle: \"{app['uiStyle']}\"`, so the native build stays {app['uiStyle']} whatever the code says")
    line = "; ".join(bits) + (". The renderer tries a dark device on its own (react-native-web reads the scheme in JS)" if app.get("web") else "")
    if stored and app.get("web"):
        line += f"; to render the app's own dark setting: `--dark-storage '{key}=dark'`"
    return line, True


def rn_storage(root: Path, src_files: list[Path], aliases: list) -> dict:
    """The keys the app keeps on the device (MMKV, AsyncStorage, SecureStore), and what they are called in a browser."""
    keys: dict[str, str] = {}
    mmkv_id = "mmkv.default"
    call = re.compile(r"(useMMKV\w*|\b\w*[sS]torage\.(?:getString|getBoolean|getNumber|set|remove|delete)|\b(?:getItem|setItem|removeItem|getItemAsync|setItemAsync|deleteItemAsync|multiGet)(?:<[^>()]*>)?)\(\s*(?:['\"]([^'\"]+)['\"]|([A-Za-z_]\w*))")
    for p in _code_files(src_files, RN_CODE):
        t = read(p, 200_000)
        if not re.search(r"MMKV|mmkv|AsyncStorage|SecureStore|[sS]torage\.|getItem|setItem", t):
            continue
        idm = re.search(r"(?:new\s+MMKV|createMMKV)\(\s*\{[^}]*\bid\s*:\s*['\"]([^'\"]+)['\"]", t)
        if idm:
            mmkv_id = idm.group(1)
        consts = dict(re.findall(r"(?:const|let)\s+(\w+)\s*=\s*['\"]([\w.:@/-]+)['\"]", t))
        for m in call.finditer(t):
            fn, key = m.group(1), m.group(2) or consts.get(m.group(3) or "")
            if not key or len(key) > 60:
                continue
            if "SecureStore" in t and "Async" in fn:
                kind = "SecureStore"
            elif fn.startswith("useMMKV") or "mmkv" in t.lower():
                kind = "MMKV"
            elif "AsyncStorage" in t:
                kind = "AsyncStorage"
            else:                                  # a wrapper: getItem from the app's own storage module
                src = _js_source_of(root, p, t, fn.split("<")[0].split(".")[-1], aliases) if fn.split("<")[0] in ("getItem", "setItem", "removeItem") else None
                st = read(src, 100_000) if src else ""
                kind = "MMKV" if "mmkv" in st.lower() else "AsyncStorage" if "AsyncStorage" in st else "SecureStore" if "SecureStore" in st else None
            if kind:
                keys.setdefault(key, kind)
    return {"keys": keys, "mmkvId": mmkv_id}


def rn_start(root: Path, src_files: list[Path], css_files: list[Path], deps: dict, app: dict) -> dict:
    """Everything the Start-here section needs for a React Native app."""
    aliases = ts_aliases(root)
    if app["router"] == "Expo Router":
        site = expo_router_site(root, app["appDir"], aliases)
        pages, routes = site["pages"], site["routes"]
        layouts, before = [], []
        rl = site["rootLayout"]
        if rl:
            t = rl["text"]
            prov = [x for x in dict.fromkeys(re.findall(r"<(\w*Provider|GestureHandlerRootView|SafeAreaProvider|KeyboardProvider|PortalHost)\b", t))][:6]
            chrome = [rl["kind"]] if rl["kind"] and rl["kind"] != "slot" else []
            layouts.append({"file": rel(root, rl["file"]), "css": [c for c in re.findall(r"import\s+['\"]([^'\"]+\.css)['\"]", t)], "fonts": [],
                            "providers": prov, "chrome": chrome, "scope": "", "scopeText": "wraps every page"})
            if "preventAutoHideAsync" in t:
                before.append(f"`{rel(root, rl['file'])}` keeps the splash screen up (`SplashScreen.preventAutoHideAsync`) until it hides it: on the web there is no splash, the page shows once the fonts load")
        for d, lay in sorted(site["layouts"].items()):
            if lay is rl:
                continue
            scope = rel(root, d)
            layouts.append({"file": rel(root, lay["file"]), "css": [], "fonts": [], "providers": [], "chrome": [lay["kind"]] if lay["kind"] else [],
                            "scope": scope, "scopeText": f"wraps `{scope}/*`"})
        for lay in site["layouts"].values():
            for g in lay["guards"]:
                before.append(f"`{rel(root, lay['file'])}`: {g}")
        if site["apis"]:
            before.append("API routes (`+api`): " + ", ".join(f"`{a}`" for a in site["apis"][:6]) + " — served by `expo start` itself")
        router = f"Expo Router, file routes in {rel(root, app['appDir'])}/"
    else:
        nav = rn_navigation(root, src_files, aliases)
        pages, routes = rn_screen_pages(root, nav)
        layouts, before = [], []
        for n in nav["navs"]:
            if n["initial"]:
                before.append(f"`{rel(root, n['file'])}`: {n['name']} starts at `{n['initial']}` (`initialRouteName`)")
        if nav["navs"] and not nav["linking"]:
            before.append("no linking config: on the web every screen shows at `/`, so the render reaches a screen past the first by tapping to it (`--act click:text=…`)")
        router = "React Navigation" + (", with a linking config" if nav["linking"] else "")
    store = rn_storage(root, src_files, aliases)
    if store["keys"]:
        web = {"MMKV": lambda k: f"{store['mmkvId']}\\{k}", "AsyncStorage": lambda k: k}
        shown = [f"`{k}` ({v})" for k, v in list(store["keys"].items())[:8]]
        auth = [k for k, v in store["keys"].items() if re.search(r"token|auth|session|jwt|credential|user", k, re.I) and v in web]
        secure = [k for k, v in store["keys"].items() if v == "SecureStore"]
        line = "the app keeps state on the device: " + ", ".join(shown)
        if any(v == "MMKV" for v in store["keys"].values()):
            line += f"; on the web MMKV is localStorage under `{store['mmkvId']}\\KEY`"
        if auth:
            k = auth[0]
            line += f"; a signed-in screen renders with that session in place: `--storage '{web[store['keys'][k]](k)}=…'` (the value the app writes there)"
        if secure:
            line += f"; SecureStore ({', '.join(f'`{k}`' for k in secure[:2])}) has no web version: a session kept there cannot be set in the browser"
        before.append(line)
    theme = rn_theme(root, src_files, aliases)
    theme_files = {m["file"] for m in theme["maps"]} | {m.get("darkFile") for m in theme["maps"] if m.get("darkFile")}
    usage = rn_style_usage(root, src_files, theme_files)
    for b in theme["bases"]:
        b["file"] = rel(root, b["file"])
    for m in theme["maps"]:                      # paths as the report prints them (and --json can carry)
        m["file"] = rel(root, m["file"])
        if m.get("darkFile"):
            m["darkFile"] = rel(root, m["darkFile"])
    theme["palettes"] = [(n, rel(root, f), c) for n, f, c in theme["palettes"]]
    for sc in theme["scales"]:
        sc["file"] = rel(root, sc["file"])
    kit_uses = []
    for pkg, label in RN_KITS.items():
        if pkg in deps or (label == "React Native Paper" and any("react-native-paper" in read(p, 60_000) for p in _code_files(src_files, RN_CODE)[:200])):
            uses = _react_kit_uses(src_files, (pkg,) if label != "Tamagui" else ("tamagui", "@tamagui/core"))
            if uses and label not in [k for k, _ in kit_uses]:
                kit_uses.append((label, uses))
    twins = []
    web_branches = 0
    for p in _code_files(src_files, RN_CODE):
        if ".web" in p.stem and RN_PLATFORM.search(p.stem):
            base = p.with_name(RN_PLATFORM.sub("", p.stem) + p.suffix)
            if base.is_file() or any(base.with_suffix(s).is_file() for s in RN_CODE):
                twins.append(rel(root, p))
        t = read(p, 200_000)
        web_branches += bool(re.search(r"Platform\.OS\s*===?\s*['\"]web['\"]|Platform\.select\(\s*\{[^}]*\bweb\s*:", t))
    a11y = collections.Counter()
    for p in _code_files(src_files, (".tsx", ".jsx")):
        t = read(p, 200_000)
        a11y["pressables"] += len(re.findall(r"<(?:Pressable|TouchableOpacity|TouchableHighlight|TouchableWithoutFeedback|TouchableRipple)\b", t))
        a11y["roles"] += len(re.findall(r"\b(?:accessibilityRole|role)=", t))
        a11y["labels"] += len(re.findall(r"\b(?:accessibilityLabel|aria-label)=", t))
        a11y["noScale"] += len(re.findall(r"allowFontScaling=\{\s*false\s*\}", t))
        a11y["hitSlop"] += len(re.findall(r"\bhitSlop=", t))
    dark_line, dark_on = rn_dark(root, src_files, app, deps)
    native_only = [f"`{k}` ({v})" for k, v in RN_NATIVE_ONLY.items() if k in deps]
    tailwind_rn = next((label for key, label in (("nativewind", "NativeWind"), ("uniwind", "Uniwind"), ("twrnc", "twrnc")) if key in deps), None)
    return {"pages": pages, "routes": routes, "layouts": layouts, "stackBefore": before, "router": router,
            "theme": theme, "usage": usage, "kits": kit_uses, "twins": twins, "webBranches": web_branches, "a11y": dict(a11y),
            "dark": dark_line, "darkOn": dark_on, "fonts": rn_fonts(root, src_files, deps, app), "nativeOnly": native_only, "tailwindRN": tailwind_rn}


def md_rn_lines(rn: dict, app: dict) -> list[str]:
    """Start-here lines for a React Native app: its kit, how it styles, the web twins, the accessibility props."""
    out = []
    for label, uses in rn["kits"]:
        out.append(f"- {label} — its components by use (counted by the files that import them): " + " · ".join(f"{n} ×{c}" for n, c in uses)
                   + ". A match task builds with these and the kit's theme, not hand-rolled views.")
    u = rn["usage"]
    if u["files"]:
        how = []
        if u["sheets"]:
            how.append(f"`StyleSheet.create` in {u['sheets']} files")
        if u.get("typed"):
            how.append(f"style objects typed `ViewStyle` / `TextStyle` (or themed style functions) in {u['typed']} files")
        if u["inline"]:
            how.append(f"inline `style={{{{…}}}}` ×{u['inline']}")
        if u["classNames"] and rn.get("tailwindRN"):
            how.append(f"`className` ×{u['classNames']} ({rn['tailwindRN']}: Tailwind classes)")
        cols = f"colours from the theme ×{u['themeColors']}" + (f" ({', '.join(f'`{k}` ×{n}' for k, n in u['themeTop'][:4])})" if u["themeTop"] else "") \
            + f", literals ×{u['literalColors']}" + (f" ({', '.join(f'`{k}` ×{n}' for k, n in u['literalTop'][:3])})" if u["literalTop"] else "")
        out.append("- Styling: " + " · ".join(how or ["no StyleSheet or className found"]) + f" · {cols}. A new component styles itself the same way and takes colours from the theme.")
    if rn["twins"]:
        out.append(f"- Web twins ({len(rn['twins'])}): " + ", ".join(f"`{x}`" for x in rn["twins"][:6])
                   + " — the render shows these, the phone shows the file without `.web`: a fix to one is not a fix to the other")
    if rn["webBranches"]:
        out.append(f"- `Platform.OS === 'web'` or `Platform.select({{ web }})` in {rn['webBranches']} file{'s' if rn['webBranches'] > 1 else ''}: what the render shows there differs from the phone")
    a = rn["a11y"]
    if a.get("pressables"):
        out.append(f"- Accessibility props: {a['pressables']} pressables, {a.get('roles', 0)} roles, {a.get('labels', 0)} labels"
                   + (f" · `allowFontScaling={{false}}` ×{a['noScale']}: that text ignores the user's font size" if a.get("noScale") else "")
                   + (f" · `hitSlop` ×{a['hitSlop']}: the phone's touch area is larger than the box the render measures" if a.get("hitSlop") else ""))
    return out


def md_rn_tokens(rn: dict, root: Path) -> list[str]:
    out = []
    for m in rn["theme"]["maps"]:
        files = f"`{m['file']}`" + (f", `{m['darkFile']}`" if m.get("darkFile") and m["darkFile"] != m["file"] else "")
        label = m["name"].replace("default.colors", "the default export's colors").replace("default", "the default export")
        out.append(f"### React Native theme — `{label}` in {files}" if "default" not in m["name"] else f"### React Native theme — {label} of {files}")
        light, dark = _rn_order(m["light"]), dict(m.get("dark") or [])
        light += [(k, "—") for k in dark if k not in dict(light)]
        semantic = [(k, v) for k, v in light if not re.search(r"\d{2,}$", k)]
        numbered = len(light) - len(semantic)
        if semantic:
            out.append(("- light / dark: " if dark else "- colours: ") + " · ".join(f"{k} {v}" + (f" / {dark[k]}" if k in dark else "") for k, v in semantic[:12])
                       + (" …" if len(semantic) > 12 else ""))
        if numbered:
            out.append(f"- {numbered} numbered palette colours (prefer the names above)" if semantic else f"- palette: {numbered} numbered colours")
        if m["scales"]:
            out.append("- scales (500 or middle step): " + " · ".join(m["scales"][:8]))
        if m["spreads"]:
            out.append("- on top of: " + ", ".join(f"`{s}`" for s in m["spreads"][:3]) + " (values it does not set are that theme's"
                       + (", filled in above" if any(s in ("DefaultTheme", "DarkTheme", "MD3LightTheme", "MD3DarkTheme") for s in m["spreads"]) else "") + ")")
        out += [f"- {x}" for x in rn_theme_contrast(m)]
    for b in rn["theme"].get("bases") or []:
        out.append(f"### `{b['name']}` in `{b['file']}` — no colours of its own: " + " + ".join(b["bases"]))
    if rn["theme"].get("palettes"):
        out.append("- palettes the names above are drawn from: " + ", ".join(f"`{n}` in `{f}` ({c} colours)" for n, f, c in rn["theme"]["palettes"]))
    for s in rn["theme"]["scales"]:
        out.append(f"### `{s['name']}` in `{s['file']}`")
        out.append("- " + " · ".join(f"{k} {v}" for k, v in s["values"]))
    return out


def md_rn_usage(rn: dict) -> list[str]:
    u = rn["usage"]
    out = []
    if u["fontSize"]:
        out.append("- font sizes: " + ", ".join(f"{k} ×{n}" for k, n in u["fontSize"]))
    if u["radius"]:
        out.append("- border radius: " + ", ".join(f"{k} ×{n}" for k, n in u["radius"]))
    if u["spacing"]:
        out.append("- padding / margin / gap: " + ", ".join(f"{k} ×{n}" for k, n in u["spacing"]))
    return out


def page_signatures(root: Path, src_files: list[Path], vocab_names: list[str], framework: str | None = None, deps: dict | None = None) -> dict:
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
    # A React app with a route table: the files it names are the pages, with their routes, layouts and guards.
    by_file: dict[Path, list[dict]] = {}
    table = None
    if (deps or {}).get("react") and not (is_next or is_nuxt or is_kit or is_astro) and framework not in ("Vue", "Angular", "Laravel"):
        table = react_route_table(root, src_files, deps or {})
        for r in table["routes"]:
            if r["file"] and r["file"].suffix in {".tsx", ".jsx", ".ts", ".js"} and r["file"].is_file():
                by_file.setdefault(r["file"], []).append(r)
    route_mode = len(by_file) >= 2
    shown_by: dict[Path, str] = {}
    if route_mode:
        # Screens outside the table (a sign-in App shows before any route) stay pages; a tab a routed page imports,
        # a file under a routed page's folder, or a component folder's file does not.
        routed_dirs = [f.parent for f in by_file if f.stem == "index"]
        routed_text = "\n".join(read(f, 200_000) for f in by_file)
        code = [q for q in src_files if q.suffix in {".tsx", ".jsx", ".ts", ".js"} and not re.search(r"\.(test|spec|stories)$", q.stem)]
        for c in src_files:
            if c in by_file or c.suffix not in {".tsx", ".jsx"} or re.search(r"\.(test|spec|stories)$", c.stem):
                continue
            dirs = [x.lower() for x in c.relative_to(root).parts[:-1]]
            if not set(dirs) & {"pages", "views", "screens"} or set(dirs) & {"components", "utils", "hooks", "sections", "_components"}:
                continue
            if any(d in c.parents for d in routed_dirs):
                continue
            imp = re.compile(r"from\s*['\"][^'\"]*[/'\"]" + re.escape(c.stem) + r"(?:\.\w+)?['\"]|import\(\s*['\"][^'\"]*/" + re.escape(c.stem) + r"['\"]")
            if imp.search(routed_text):
                continue
            who = next((q for q in code if q != c and q not in by_file and imp.search(read(q, 200_000))), None)
            if who:
                shown_by[c] = rel(root, who)
        candidates = sorted(by_file) + sorted(shown_by)
    for p in candidates:
        if p.suffix not in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".md", ".mdx"}:
            continue
        rp = p.relative_to(root)
        dirs = [x.lower() for x in rp.parts[:-1]]
        if not (is_kit or is_astro or route_mode):
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
        rec = {
            "file": str(rp), "lines": text.count("\n") + 1, "signals": signals,
            "classes": [f"{n} ×{c}" for n, c in used if c][:3], "components": list(dict.fromkeys(page_comps))[:6], "renders": rendered,
        }
        if route_mode and p in shown_by:
            rec["route"] = f"no route: `{shown_by[p]}` shows it"
        elif route_mode:
            rs = by_file[p]
            paths = list(dict.fromkeys(r["path"] for r in rs))
            rec["route"] = ", ".join(f"`{x}`" for x in paths[:3]) + (f" and {len(paths) - 3} more" if len(paths) > 3 else "")
            lay = next((r["layout"] for r in rs if r["layout"] and r["layout"]["name"] not in ("App", "Root", "Providers", "AppProviders")), None)
            if lay:
                lt = read(lay["file"], 200_000) if lay.get("file") else ""
                rec["inside"] = {"name": lay["name"], "file": rel(root, lay["file"]) if lay.get("file") else None, "lines": lt.count("\n") + 1,
                                 "holder": "`<Outlet />`" if "<Outlet" in lt else "`children`"}
            rec["routeGuards"] = list(dict.fromkeys(g for r in rs for g in r["guards"]))
        pages.append(rec)
    pages.sort(key=lambda x: x["file"])
    if route_mode:                                   # the page lines carry the rest: redirects and unresolved routes only
        routes += [(r["path"], f"(redirect → `{r['redirect']}`)" if r["redirect"] else r["name"] or "?")
                   for r in table["routes"] if r["redirect"] or not r["file"]]
    for p in ([] if route_mode else src_files):
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
    return {"pages": pages[:32 if route_mode else 24], "routes": routes[:30]}


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
            pkg = json.loads(read(pj))
            native = any(k in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})} for k in ("react-native", "expo"))
            scripts = {k: v for k, v in pkg.get("scripts", {}).items() if k in {"dev", "start", "preview"} or k.startswith("dev:")}
            if native and "web" in pkg.get("scripts", {}):        # a React Native app runs in a browser through its `web` script
                scripts = {"web": pkg["scripts"]["web"], **scripts}
        except (json.JSONDecodeError, AttributeError):
            pass
    return {"proxies": proxies[:6], "helpers": sorted(helpers), "scripts": scripts, "next": next_cfg}


def storage_keys(root: Path, src_files: list[Path]) -> list[str]:
    """Where the app keeps its state in the browser: the keys to seed with --init-script."""
    found: dict[str, str] = {}
    # The store's own file names the key best; an error boundary that also reads it comes later.
    ranked = sorted(src_files, key=lambda p: (0 if re.search(r"stor(e|age)|persist|db", str(p), re.I) else 1, str(p)))
    for p in ranked:
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"} or re.search(r"\.(test|spec|stories)$", p.stem):
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


def gates(root: Path, src_files: list[Path], native: bool = False) -> list[str]:
    out = []
    idx = root / "index.html"
    if idx.exists() and re.search(r"<script>(?:(?!</script>).)*?(matchMedia|localStorage|data-?theme|dataset\.theme)", read(idx), re.S):
        out.append("`index.html` decides the theme in an inline script at boot (`data-theme`); the dark pass reloads for it")
    for p in [] if native else src_files:
        if SPLASH_STEM.match(p.stem) and p.suffix in {".tsx", ".jsx", ".vue", ".svelte"} \
                and not {x.lower() for x in p.relative_to(root).parts[:-1]} & {"pages", "views", "screens"}:
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
            t = read(p, 200_000)
            if re.search(r"export\s+(?:async\s+)?(?:const|function)\s+(?:getInitialState|layout|rootContainer)\b", t):
                continue                                # umi's runtime config, not an App component
            conds = re.findall(r"\n[ \t]*if\s*\(([^)\n]{1,80})\)\s*\{\s*\n[ \t]*return\b", t)
            if conds:
                out.append(f"`{rel(root, p)}` returns early on, in order: " + " → ".join(f"`{c.strip()}`" for c in conds[:6]))
    return out[:6]


def start_here(root: Path, src_files: list[Path], css_files: list[Path], stack: dict, deps: dict) -> dict:
    if stack.get("framework") == "Flutter":
        return flutter_start_here(root, stack)
    ui_files = [p for p in src_files if p.suffix in {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".mdx"}]
    texts = [read(p, 200_000) for p in ui_files[:MAX_SRC_FILES]]
    ng = angular_start(root, src_files, css_files, deps) if stack.get("framework") == "Angular" else None
    lv = laravel_start(root, src_files, css_files, deps) if stack.get("framework") == "Laravel" else None
    app = rn_app(root, deps) if stack.get("framework") in ("Expo", "React Native") else None
    rn = rn_start(root, src_files, css_files, deps, app) if app else None
    site = None
    if lv:
        vocab = css_vocabulary(root, css_files, texts + [read(p, 200_000) for p in src_files if p.name.endswith(".blade.php")][:MAX_SRC_FILES])
        sig = {"pages": lv["pages"], "routes": lv["routes"]}
    elif not ng and stack.get("framework") in (None, "Eleventy") and (site_generator(root, deps) or not stack.get("framework")):
        own_css = [c for c in css_files if not ({x.lower() for x in c.relative_to(root).parts[:-1]} & SITE_SKIP)]
        templates = [read(p, 200_000) for p in iter_files(root) if p.suffix in {".njk", ".liquid", ".md", ".hbs", ".webc", ".markdown"}][:MAX_SRC_FILES]
        vocab = css_vocabulary(root, own_css, texts + templates)
        site = site_start(root, src_files, css_files, stack, deps, [v["name"] for v in vocab])
    if lv:
        pass
    elif site:
        sig = {"pages": site["pages"], "routes": site["routes"]}
    elif ng:      # a component's own stylesheet is scoped to it: only the global ones make a vocabulary
        texts += ng["inlineTemplates"]
        vocab = css_vocabulary(root, [c for c in css_files if c not in ng["scopedCss"]], texts, skip=r"(?:mat|mdc|cdk)-")
        sig = {"pages": ng["pages"], "routes": ng["routes"]}
    elif rn:      # a web-only CSS Module (a `.web.tsx` twin's) is local to it, as elsewhere
        vocab = css_vocabulary(root, [c for c in css_files if not re.search(r"\.module\.\w+$", c.name)], texts)
        sig = {"pages": rn["pages"][:32], "routes": rn["routes"][:30]}
    else:                   # a CSS Module's classes are local to its component: not a shared vocabulary
        vocab = css_vocabulary(root, [c for c in css_files if not re.search(r"\.module\.\w+$", c.name)], texts)
        sig = page_signatures(root, src_files, [v["name"] for v in vocab], stack.get("framework"), deps)
    is_next = stack.get("framework") == "Next.js"
    is_nuxt = stack.get("framework") == "Nuxt"
    is_kit, is_astro = stack.get("framework") == "SvelteKit", stack.get("framework") == "Astro"
    notes = {"Nuxt": "references/stacks/nuxt.md", "Vue": "references/stacks/vue.md", "SvelteKit": "references/stacks/sveltekit.md",
             "Svelte": "references/stacks/sveltekit.md", "Astro": "references/stacks/astro.md",
             "Angular": "references/stacks/angular.md", "Laravel": "references/stacks/laravel.md",
             "Eleventy": "references/stacks/static.md", "Expo": "references/stacks/react-native.md",
             "React Native": "references/stacks/react-native.md"}.get(stack.get("framework") or "") or ("references/stacks/static.md" if site else None)
    dev = dev_setup(root)
    theme = theme_mechanism(root, css_files, stack, src_files)
    kits = kit_start(root, src_files, css_files, deps) if not (ng or lv or site or rn) else {"kits": [], "styled": None, "modules": None}
    dyn = runtime_routes(root, src_files) if not (ng or lv or site or rn) else None
    hashed = hash_history(root, src_files) if not (ng or lv or site or rn) else None
    if rn:
        theme = rn["dark"]
    kit_line, kit_dark_on = kit_dark(kits, root, src_files)
    if kit_line and not (theme and "--dark-storage" in theme):
        theme = kit_line
    if ng:
        dev["proxies"] = ng["proxies"] + dev["proxies"]
    return {
        "vocabulary": vocab,
        "imported": [] if ng or site or lv else import_fanin(root, src_files),
        **sig,
        "layouts": (next_layouts(root) if is_next else nuxt_layouts(root, src_files) if is_nuxt else sveltekit_layouts(root) if is_kit
                    else astro_layouts(root, src_files) if is_astro else ng["layouts"] if ng else site["layouts"] if site
                    else lv["layouts"] if lv else rn["layouts"] if rn else []),
        "stackBefore": (sveltekit_before(root, deps) if is_kit else astro_before(root, deps) if is_astro else ng["stackBefore"] if ng
                        else site["stackBefore"] if site else lv["stackBefore"] if lv else rn["stackBefore"] if rn else [])
                       + ([dyn] if dyn else []) + ([hashed] if hashed else []),
        "rn": {**{k: rn[k] for k in ("router", "theme", "usage", "kits", "twins", "webBranches", "a11y", "darkOn", "fonts", "nativeOnly", "tailwindRN")},
               "web": app["web"], "expo": app["expo"], "webOutput": app["webOutput"], "uiStyle": app["uiStyle"]} if rn else None,
        "bladeUsed": lv["used"] if lv else [],
        "bladeKit": lv["kit"] if lv else None,
        "laravel": {"router": lv["router"]} if lv else None,
        "site": {k: site[k] for k in ("kind", "siteLine", "kits", "libs", "copies")} if site else None,
        "ngUsed": ng["ngUsed"] if ng else [],
        "material": ng["material"] if ng else None,
        "ng": {"port": ng["port"], "router": ng["router"], "components": ng["components"]} if ng else None,
        "astro": is_astro,
        "autoImported": vue_component_uses(root, src_files, nuxt_components(root)) if is_nuxt else [],
        "nuxtui": nuxt_ui(root, src_files, deps),
        "nuxtBefore": nuxt_before(root, deps, src_files) if is_nuxt else [],
        "nuxt": is_nuxt,
        "vite": "vite" in deps and not is_next and not is_nuxt and not is_astro and not ng and not lv and not rn,
        "umi": stack.get("framework") == "Umi",
        "stackNotes": notes,
        "theme": theme,
        "kits": kits,
        "kitDark": kit_dark_on,
        "kitLook": bool(kits["kits"] or kits["styled"] or kits["modules"]),     # with Tailwind barely used, the kit is the look
        "kitNotes": "references/stacks/kits.md" if (kits["kits"] or kits["styled"] or kits["modules"]) else None,
        "middleware": middleware_line(root) if is_next else None,
        "locale": locale_routing(root, src_files, sig["routes"]),
        "next": is_next,
        "contentlayer": any(k in deps for k in ("contentlayer", "contentlayer2", "next-contentlayer", "next-contentlayer2")),
        "copy": copy_mechanism(root, src_files, deps),
        "boot": boot_requests(root, src_files),
        "dev": dev,
        "gates": gates(root, src_files, native=bool(rn)) + [s for s in ([] if rn else storage_keys(root, src_files))   # a key a guard or the theme line already names
                                                            if not ng or not any(s.split("`")[1] in b for b in ng["stackBefore"] + [theme or ""])],
    }


def rel_s(p) -> str:
    """A path as the report prints it: relative strings pass through."""
    return p if isinstance(p, str) else str(p)


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
    st = sh.get("site")
    if st:
        out.append(f"- Site: {st['siteLine']}")
        if st["kits"] or st["libs"]:
            out.append("- Loads: " + " · ".join(x for x in (st["kits"], ", ".join(st["libs"])) if x)
                       + (" — build with the kit's classes, not new CSS" if st["kits"] else ""))
        if st["copies"]:
            out.append("- Copied into each page (a change to it is an edit to every page): " + " · ".join(st["copies"]))
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
    bk = sh.get("bladeKit")
    if bk and bk["components"]:
        out.append(f"- {bk['name']} — its components by use: " + " · ".join(f"{n} ×{c}" for n, c in bk["components"])
                   + ". A match task builds with these, not hand-rolled Tailwind.")
    if sh.get("bladeUsed"):
        out.append("- Used most (Blade components, counted by the views that use them): " + " · ".join(
            f"`{rel_s(u['file'])}` `<{u['tag']}>` ({u['views']}" + (f"; props {', '.join(u['props'])}" if u["props"] else "") + ")" for u in sh["bladeUsed"]))
    out += md_kit_lines(sh.get("kits") or {})
    if sh.get("rn"):
        out += md_rn_lines(sh["rn"], {})
    if sh.get("flutter"):
        out += md_flutter_lines(sh["flutter"])
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
            if pg.get("route"):                     # Angular and sites: the route first, then the template or the page's length
                bits = [pg["route"]] + ([f"“{pg['title']}”"] if pg.get("title") else [])
                bits.append((f"template `{pg['template']}`, " if pg["template"] not in (None, "inline") else "inline template, ") + f"{pg['lines']} lines"
                            if pg.get("template") is not None else f"{pg['lines']} lines")
            if pg["signals"]:
                bits.append(", ".join(pg["signals"]))
            if pg["classes"]:
                bits.append(", ".join(pg["classes"]))
            if pg["components"]:
                bits.append((f"{pg['usesWord']} " if pg.get("usesWord") else "uses " if pg["file"].endswith((".vue", ".svelte", ".astro", ".md", ".mdx")) or pg.get("route") else "imports ") + ", ".join(pg["components"]))
            ins = pg.get("inside")
            if ins:
                bits.append(f"inside {ins['name']}" + ("" if not ins.get("file") or ins["file"] in wrappers_named
                                                        else f" (`{ins['file']}` · {ins['lines']} lines: the chrome, its {ins['holder']} holds the page)"))
                if ins.get("file"):
                    wrappers_named.add(ins["file"])
            if pg.get("routeGuards"):
                bits.append("behind " + ", ".join(pg["routeGuards"]))
            if pg.get("when"):
                bits.append(pg["when"])
            r = pg.get("renders")
            if r and r.get("wrapper"):
                bits.append(f"inside {r['name']}" + ("" if r["file"] in wrappers_named else f" (`{r['file']}` · {r['lines']} lines: the chrome, its "
                                                        + ("`<router-outlet>`" if r.get("outlet") else r.get("holder") or "slot") + " holds the page)"))
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
        elif sh.get("rn"):
            r = sh["rn"]
            line += (" — `expo start --web` serves the app through react-native-web at :8081 (`--port` changes it); the first request bundles it, which takes a while: render once it answers"
                     if r["web"] and r["expo"] else " — Metro serves the bundle at :8081" + ("; with `react-native-web` a web entry can render it" if r["web"] else ""))
            if r["web"] is None:
                line += "; no `react-native-web` in the dependencies: the app does not run in a browser (`npx expo install react-native-web react-dom` adds it), so the renderer cannot show it — check screens by the rules in the stack notes"
            if r["nativeOnly"]:
                many = len(r["nativeOnly"]) > 1
                line += "; " + ", ".join(r["nativeOnly"]) + (" have no web version: screens that use them fail or render empty in the browser" if many
                                                             else " has no web version: a screen that uses it fails or renders empty in the browser")
        elif sh.get("umi"):
            line += " — `max dev` listens on :8000 unless `PORT` says otherwise, and answers `/api` from `mock/` unless `MOCK=none`"
        elif sh.get("vite"):
            line += " — Vite listens on :5173 unless `--port` or `server.port` says otherwise"
        before.append(line)
    if before:
        out.append("- Before a page renders:")
        out += [f"  - {ln}" for ln in before]
    if sh.get("stackNotes"):
        out.append(f"- Stack notes: `{sh['stackNotes']}` in the skill folder — how this stack serves a page, switches theme and names its components")
    if sh.get("kitNotes"):
        out.append(f"- Kit notes: `{sh['kitNotes']}` in the skill folder, the section for this kit — where its theme is, its dark mode, and the defaults the render will flag")
    if sh["pages"] or sh["vocabulary"]:
        thin = any(pg.get("renders") and not pg["renders"].get("wrapper") for pg in sh["pages"])
        out.append("- Read next: " + (("the page above whose signals match yours" + (" (a thin page: the file it renders)" if thin else "") if sh["pages"] else "the vocabulary lines")
                   + (" and the vocabulary lines" if sh["pages"] and sh["vocabulary"] else ""))
                   + ". Not the CSS file, not the store.")
    elif (sh.get("kits") or {}).get("kits") or (sh.get("kits") or {}).get("styled") or (sh.get("kits") or {}).get("modules"):
        out.append("- Read next: the kit lines above and one component that already uses them. Not the CSS file, not the store.")
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
    site = (data.get("startHere") or {}).get("site")
    if site and (site["kits"] or site["libs"]):
        bits.append(" · ".join(x for x in (site["kits"], ", ".join(site["libs"])) if x))
    if s["framework"] in ("Nuxt", "Vue", "SvelteKit", "Svelte", "Astro", "Angular", "Laravel", "Eleventy", "Expo", "React Native", "Flutter") and s.get("frameworkVersion"):
        bits[-1] = bits[-1].replace(s["framework"], f"{s['framework']} {s['frameworkVersion']}", 1)
    if s.get("reactNative") and s["framework"] == "Expo":
        bits.append(f"React Native {s['reactNative']}")
    if s["framework"] in ("Expo", "React Native"):
        bits.append(f"react-native-web {s['rnWeb']}" if s.get("rnWeb") else "no react-native-web (no web build)")
    if s.get("dartSdk"):
        bits.append(f"Dart {s['dartSdk']}")
    fls = (data.get("startHere") or {}).get("flutter")
    if fls:
        bits.append("Cupertino (`CupertinoApp`)" if (fls.get("appKind") or "").startswith("Cupertino")
                    else "Material 2 (`useMaterial3: false`)" if fls["theme"]["m3"] is False else "Material 3")
    if s.get("state"):
        bits.append("state: " + ", ".join(s["state"]))
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
    if s.get("depsSource") and s["depsSource"] not in ("package.json", "pubspec.yaml"):
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
    if t.get("sass"):
        by_file = collections.defaultdict(list)
        for file, name, value in t["sass"]:
            by_file[file].append(f"{name}: {value};")
        for file, items in by_file.items():
            out += [f"### Sass variables in {file}", "```scss", *items[:40], *(["…"] if len(items) > 40 else []), "```"]
    for key, snippet in t["configExtend"].items():
        out += [f"### tailwind.config `extend.{key}`", "```js", snippet, "```"]
    kit_md = md_kit_tokens((data.get("startHere") or {}).get("kits") or {})
    rn = (data.get("startHere") or {}).get("rn")
    kit_md += md_rn_tokens(rn, Path(data["root"])) if rn else []
    kit_md += md_flutter_tokens(fls) if fls else []
    out += kit_md
    if not (t["theme"] or t["root"] or t.get("sass") or t["configExtend"] or kit_md):
        out.append("- none declared (no ColorScheme, seed colour, TextTheme or ThemeExtension: Material's defaults)" if fls
                   else "- none declared (no @theme, :root vars, Sass variables, or config extend)")
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
    for kit in ((data.get("startHere") or {}).get("kits") or {}).get("kits") or []:
        if kit.get("fonts"):
            out.append(f"- {kit['kit']} theme: " + ", ".join(kit["fonts"]))
    for line in (rn or {}).get("fonts") or []:
        out.append(f"- {line}")
    if fls:
        if fls["fonts"]:
            out.append("- pubspec fonts (bundled): " + ", ".join(fls["fonts"]))
        if fls["googleFonts"]:
            out.append("- google_fonts: " + ", ".join(fls["googleFonts"]) + " — fetched at run time unless the files are bundled as assets (`GoogleFonts.config.allowRuntimeFetching = false`)")
        if fls["fontFamilies"]:
            out.append("- fontFamily set in code: " + ", ".join(fls["fontFamilies"][:6]))
    fontsource = sorted(k for k in (s.get("deps") or {}) if k.startswith("@fontsource"))
    if fontsource:
        out.append("- loaded from npm (no network needed): " + ", ".join(f"`{k}`" for k in fontsource))
    if u["fontClasses"]:
        out.append("- classes in use: " + ", ".join(f"font-{k} ×{n}" for k, n in u["fontClasses"]))
    if len(out) and out[-1] == "## Fonts":
        out.append("- nothing explicit: the platform's face (Roboto on Android and the web, San Francisco on iOS)" if fls
                   else "- nothing explicit (system / Tailwind default stack)")
    out.append("")

    # Components
    if (data.get("startHere") or {}).get("flutter") is not None:
        c = {"primitives": [], "composed": data["startHere"].get("widgets") or []}
    out.append(f"## Components ({len(c['primitives']) + len(c['composed'])} found)")
    if c["primitives"]:
        out.append("- primitives (`ui/`): " + ", ".join(Path(p).stem for p in c["primitives"]))
    if c["composed"]:
        out.append("- composed: " + ", ".join(Path(p).stem for p in c["composed"][:40]) + (" …" if len(c["composed"]) > 40 else ""))
    if not (c["primitives"] or c["composed"]):
        out.append("- no widget classes in widgets/ components/ common/ shared/ core/" if fls else "- none found in components/ ui/ primitives/ dirs")
    out.append("")

    # Usage
    out.append(f"## What the code actually uses ({(data.get('startHere') or {}).get('dartFiles') or u['scannedFiles']} source files)")
    total = u["rawTotal"] + u["semanticTotal"]
    if fls:                   # Flutter: the numbers in EdgeInsets, SizedBox and BorderRadius
        out += md_flutter_usage(fls)
        u = {**u, "radius": [], "shadow": [], "textSize": [], "spacing": [], "arbitraryTotal": 0}
        total = -1
    elif (data.get("startHere") or {}).get("kitLook") and (not s.get("tailwind") or total < 10):   # counts would match props (shadow="hover")
        out.append("- not a Tailwind project: the look is the kit's theme and components above; class counts are left out")
        u = {**u, "radius": [], "shadow": [], "textSize": [], "spacing": [], "arbitraryTotal": 0}
        total = -1
    elif rn:                  # React Native: StyleSheet numbers; Tailwind counts only where NativeWind / Uniwind classes are used
        out += md_rn_usage(rn)
        if not s.get("tailwind") or total < 10:
            u = {**u, "radius": [], "shadow": [], "textSize": [], "spacing": [], "arbitraryTotal": 0}
            total = -1
    if total > 0:
        out.append("- color families: " + ", ".join(f"{k} {n}" for k, n in u["colorFamilies"]) +
                   f"  → raw {u['rawTotal']} / semantic {u['semanticTotal']}")
        if u["colorTokens"]:
            out.append("- most-used color classes: " + ", ".join(f"{k} {n}" for k, n in u["colorTokens"]))
        if u["semantic"]:
            out.append("- semantic tokens: " + ", ".join(f"{k} {n}" for k, n in u["semantic"]))
        if u["neutrals"]:
            out.append("- neutrals: " + ", ".join(f"{k} {n}" for k, n in u["neutrals"]))
    elif total == 0:
        out.append("- no Tailwind color classes found")
    if u["radius"]:
        out.append("- radius: " + ", ".join(f"rounded{'' if k == 'default' else '-' + k} {n}" for k, n in u["radius"]))
    if u["shadow"]:
        out.append("- shadow: " + ", ".join(f"shadow{'' if k == 'default' else '-' + k} {n}" for k, n in u["shadow"]))
    if u["textSize"]:
        out.append("- text sizes: " + ", ".join(f"text-{k} {n}" for k, n in u["textSize"]))
    if u["spacing"]:
        out.append("- spacing steps: " + ", ".join(f"{k} ×{n}" for k, n in u["spacing"]))
    if total != -1:
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
    src_files = [p for p in files if p.suffix in SRC_EXT or p.name.endswith(".blade.php")]
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
    if sh and sh.get("laravel"):
        stack["router"] = sh["laravel"]["router"]
    if sh and sh.get("rn"):
        stack["router"] = sh["rn"]["router"]
    if sh and sh.get("site") and not stack.get("framework"):
        stack["framework"] = sh["site"]["kind"]
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
