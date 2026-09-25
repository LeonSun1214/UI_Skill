#!/usr/bin/env python3
"""ui-craft verify — facts the model tends to invent, checked against what is actually there.

  python3 verify.py <project-root> [--lang zh] [--strict]

Checks
  packages   every `import … from 'pkg'` resolves to an installed package (node_modules,
             walking up for workspaces); a missing one is a FAIL — the build will break
  icons      every named import from an icon package (lucide-react, @heroicons/react,
             @phosphor-icons/react, @tabler/icons-react, react-icons/*, @radix-ui/react-icons)
             is really exported by the installed version; a wrong name is a FAIL, with the
             closest real name suggested
  fonts      every web font the project asks for exists: Google Fonts <link> families and
             next/font/google imports are looked up in the bundled catalog (data/google-fonts.json),
             requested weights are checked, and — when the page's language needs it — the
             family must ship the matching subset (a Chinese page set in Fraunces renders every
             CJK glyph in the fallback face). @font-face src files must exist. A font-family
             that is neither loaded nor a known system face is a WARN.

Prints one line per finding and a `Facts:` summary line for the report. Exit 1 with --strict
when anything FAILs. Standard library only.
"""
import difflib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".ui-craft", ".vite-cache", "coverage"}
SRC_EXT = {".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue", ".svelte", ".astro", ".mdx"}
MAX_FILES = 800

ICON_PACKAGES = {
    "lucide-react", "@heroicons/react", "@phosphor-icons/react", "@tabler/icons-react",
    "react-icons", "@radix-ui/react-icons", "lucide", "@heroicons/vue", "lucide-vue-next",
}
NODE_BUILTINS = {"fs", "path", "os", "url", "http", "https", "crypto", "util", "events", "stream", "child_process", "assert", "buffer", "zlib", "net", "tls", "readline", "process"}
SYSTEM_FONTS = {
    # generic + platform stacks
    "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace", "ui-rounded", "sans-serif", "serif", "monospace",
    "cursive", "fantasy", "emoji", "math", "fangsong", "inherit", "initial",
    "-apple-system", "blinkmacsystemfont", "segoe ui", "segoe ui emoji", "segoe ui symbol", "roboto", "helvetica neue",
    "helvetica", "arial", "arial black", "verdana", "tahoma", "trebuchet ms", "georgia", "times new roman", "times",
    "cambria", "garamond", "palatino", "book antiqua", "courier new", "courier", "menlo", "monaco", "consolas",
    "sf mono", "sf pro", "sf pro text", "sf pro display", "liberation mono", "liberation sans", "dejavu sans",
    "dejavu sans mono", "noto sans", "noto serif", "noto color emoji", "apple color emoji", "avenir", "avenir next",
    "gill sans", "optima", "futura", "baskerville", "didot", "hoefler text", "impact", "lucida grande", "lucida console",
    # CJK system faces
    "pingfang sc", "pingfang tc", "pingfang hk", "hiragino sans", "hiragino sans gb", "hiragino kaku gothic pron",
    "hiragino mincho pron", "microsoft yahei", "microsoft jhenghei", "simsun", "simhei", "kaiti", "songti sc", "songti tc",
    "stsong", "stheiti", "heiti sc", "heiti tc", "noto sans cjk sc", "noto sans cjk tc", "noto sans cjk jp", "noto serif cjk sc",
    "noto serif cjk tc", "source han sans", "source han sans sc", "source han serif", "source han serif sc", "wenquanyi micro hei",
    "yu gothic", "meiryo", "ms gothic", "ms mincho", "malgun gothic", "apple sd gothic neo", "nanum gothic",
    "微软雅黑", "苹方", "宋体", "黑体", "楷体", "思源黑体", "思源宋体",
}
LANG_SUBSET = {
    "zh": "chinese-simplified", "zh-cn": "chinese-simplified", "zh-hans": "chinese-simplified", "zh-sg": "chinese-simplified",
    "zh-tw": "chinese-traditional", "zh-hk": "chinese-hongkong", "zh-hant": "chinese-traditional",
    "ja": "japanese", "ko": "korean", "ru": "cyrillic", "uk": "cyrillic", "el": "greek", "vi": "vietnamese",
    "th": "thai", "ar": "arabic", "he": "hebrew", "hi": "devanagari",
}


# ------------------------------------------------------------------ helpers
def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def walk(root: Path):
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            p = Path(dirpath) / f
            if p.suffix in SRC_EXT or p.suffix in {".css", ".html"}:
                yield p
                n += 1
                if n >= MAX_FILES:
                    return


def node_modules_dirs(root: Path):
    dirs = []
    cur = root
    for _ in range(6):
        nm = cur / "node_modules"
        if nm.is_dir():
            dirs.append(nm)
        if cur.parent == cur:
            break
        cur = cur.parent
    return dirs


def package_name(spec: str):
    """'@scope/pkg/sub' → '@scope/pkg'; 'pkg/sub' → 'pkg'; relative/alias specs → None."""
    if spec.startswith((".", "/", "~", "@/", "#", "$", "virtual:", "node:", "data:", "http")):
        return None
    if spec.startswith("@"):
        parts = spec.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else None
    return spec.split("/")[0]


def find_package(name: str, nm_dirs):
    for nm in nm_dirs:
        p = nm / name
        if p.is_dir():
            return p
    return None


IMPORT_RE = re.compile(r"""import\s+(?P<clause>[^'";]+?)\s+from\s+['"](?P<spec>[^'"]+)['"]|import\s+['"](?P<bare>[^'"]+)['"]|require\(\s*['"](?P<req>[^'"]+)['"]\s*\)|from\s+['"](?P<from>[^'"]+)['"]""")


_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
# A line comment: `//` at the start of a line or after whitespace, `;`, `{`, `}`, `,` or `(`. Not
# after `:` — that is the `//` inside a URL string, which must stay.
_LINE_COMMENT = re.compile(r"(^|(?<=[\s;{},(]))//[^\n]*")


def strip_comments(text: str) -> str:
    """Source without its comments, so an `import` mentioned in a JSDoc is not an import."""
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))


def imports_in(text: str):
    """Yield (spec, named_imports or None) for every import in a source file."""
    text = strip_comments(text)
    for m in IMPORT_RE.finditer(text):
        spec = m.group("spec") or m.group("bare") or m.group("req") or m.group("from")
        clause = m.group("clause")
        names = None
        if clause:
            b = re.search(r"\{([^}]*)\}", clause)
            if b:
                names = []
                for part in b.group(1).split(","):
                    part = part.strip()
                    if not part or part.startswith("type "):
                        continue
                    names.append(part.split(" as ")[0].strip())
        yield spec, names, clause


# ------------------------------------------------------------- icon exports
_export_cache: dict[str, set] = {}


def exports_of(pkg_dir: Path, subpath: str) -> set | None:
    """Names exported by an installed package (or a subpath), read from its .d.ts / esm entry."""
    key = f"{pkg_dir}::{subpath}"
    if key in _export_cache:
        return _export_cache[key]
    candidates = []
    base = pkg_dir / subpath if subpath else pkg_dir
    try:
        pkg = json.loads(read(pkg_dir / "package.json"))
    except ValueError:
        pkg = {}
    if not subpath:
        for k in ("types", "typings"):
            if pkg.get(k):
                candidates.append(pkg_dir / pkg[k])
        exp = pkg.get("exports")
        if isinstance(exp, dict):
            dot = exp.get(".") if "." in exp else exp
            if isinstance(dot, dict):
                for k in ("types", "import", "default", "module"):
                    v = dot.get(k)
                    if isinstance(v, dict):
                        v = v.get("types") or v.get("default")
                    if isinstance(v, str):
                        candidates.append(pkg_dir / v)
        for k in ("module", "main"):
            if pkg.get(k):
                candidates.append(pkg_dir / pkg[k])
        candidates += [pkg_dir / "index.d.ts", pkg_dir / "dist" / "index.d.ts", pkg_dir / "index.js", pkg_dir / "index.mjs"]
    else:
        candidates += [base / "index.d.ts", base.with_suffix(".d.ts"), base / "index.js", base / "index.mjs", base.with_suffix(".js")]
    names: set = set()
    seen: set = set()

    def harvest(p: Path, depth: int):
        if depth > 3 or not p.exists() or p in seen:
            return
        seen.add(p)
        text = read(p)
        for blk in re.findall(r"export\s*(?:type\s*)?\{([^}]*)\}", text):
            for part in blk.split(","):
                part = part.strip()
                if not part:
                    continue
                m = re.match(r"(?:default\s+as\s+|type\s+)?(\w+)(?:\s+as\s+(\w+))?", part)
                if m:
                    names.add(m.group(2) or m.group(1))
        for m in re.finditer(r"export\s+(?:declare\s+)?(?:const|let|var|function|class|enum)\s+(\w+)", text):
            names.add(m.group(1))
        for m in re.finditer(r"^\s*declare\s+const\s+(\w+)\s*:", text, re.M):
            names.add(m.group(1))
        for m in re.finditer(r"export\s+\*\s+from\s+['\"]([^'\"]+)['\"]", text):
            target = m.group(1)
            for cand in (p.parent / (target + ".d.ts"), p.parent / target / "index.d.ts", p.parent / (target + ".js"), p.parent / target / "index.js", p.parent / (target + ".mjs")):
                harvest(cand, depth + 1)

    for c in candidates:
        if c.suffix in {".ts", ".js", ".mjs", ".cjs"} or c.name.endswith(".d.ts"):
            harvest(c, 0)
            if c.suffix == ".js" and not c.name.endswith(".d.ts"):
                harvest(c.with_name(c.name[:-3] + ".d.ts"), 0)
        if len(names) > 20:
            break
    result = names if names else None
    _export_cache[key] = result
    return result


# ------------------------------------------------------------------- fonts
def load_catalog():
    p = HERE / "data" / "google-fonts.json"
    try:
        return json.loads(read(p))
    except ValueError:
        return {"meta": {}, "fonts": {}}


def google_link_families(text: str):
    """Families (with requested weights) from fonts.googleapis.com URLs."""
    out = []
    for url in re.findall(r"https?://fonts\.googleapis\.com/css2?\?[^\"'\s)]+", text):
        for fam in re.findall(r"family=([^&]+)", url):
            fam = fam.replace("&amp;", "&")
            name, _, axes = fam.partition(":")
            name = name.replace("+", " ").strip()
            weights = set()
            if axes:
                spec = axes.split("@")[-1] if "@" in axes else ""
                for tup in spec.split(";"):
                    nums = [int(x) for x in re.findall(r"\d{3}", tup)]
                    if "ital,wght" in axes or "wght" in axes:
                        weights.update(nums[-1:] if nums else [])
                    for rng in re.findall(r"(\d{3})\.\.(\d{3})", tup):
                        weights.update({int(rng[0]), int(rng[1])})
                        weights.add(-1)  # range: any weight in between is fine
            out.append((name, weights, url[:80]))
    return out


def next_font_imports(text: str):
    out = []
    for names in re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/google['\"]", text):
        for n in names.split(","):
            n = n.strip().split(" as ")[0].strip()
            if n:
                fam = n.replace("_", " ")
                weights = set()
                m = re.search(re.escape(n) + r"\s*\(\s*\{([^}]*)\}", text)
                if m:
                    wm = re.search(r"weight\s*:\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", m.group(1))
                    if wm:
                        weights.update(int(x) for x in re.findall(r"\d{3}", wm.group(1)))
                out.append((fam, weights))
    return out


def font_face_decls(css: str, css_path: Path, root: Path):
    out = []
    for blk in re.findall(r"@font-face\s*\{([^}]*)\}", css, re.S):
        fam = re.search(r"font-family\s*:\s*['\"]?([^;'\"]+)", blk)
        srcs = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", blk)
        out.append((fam.group(1).strip() if fam else "?", srcs, css_path))
    return out


def font_family_stacks(css: str):
    fams = []
    for m in re.finditer(r"(?:--font-[\w-]+|font-family)\s*:\s*([^;}]+)", css):
        first = m.group(1).split(",")[0].strip().strip("'\"").strip()
        if first and not first.startswith("var("):
            fams.append(first)
    return fams


def page_lang(root: Path, override: str | None):
    if override:
        return override.lower()
    for p in (root / "index.html", root / "app" / "layout.tsx", root / "src" / "app" / "layout.tsx", root / "public" / "index.html"):
        m = re.search(r"<html[^>]*\blang=['\"]([^'\"]+)['\"]", read(p)) if p.exists() else None
        if m:
            return m.group(1).lower()
    return None


def cjk_present(files) -> bool:
    for p in files:
        if p.suffix in SRC_EXT and re.search(r"[一-鿿぀-ヿ가-힯]", read(p)):
            return True
    return False


# --------------------------------------------------------------------- main
def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(args[0]).resolve()
    strict = "--strict" in args
    lang = args[args.index("--lang") + 1] if "--lang" in args else None
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 1
    files = list(walk(root))
    nm_dirs = node_modules_dirs(root)
    fails: list[str] = []
    warns: list[str] = []
    stats = {"imports": 0, "packages": set(), "icons": 0, "fonts": 0}

    # --- packages + icons
    for p in files:
        if p.suffix not in SRC_EXT:
            continue
        text = read(p)
        rel = os.path.relpath(p, root)
        for spec, names, clause in imports_in(text):
            pkg = package_name(spec)
            if not pkg or pkg in NODE_BUILTINS:
                continue
            stats["imports"] += 1
            stats["packages"].add(pkg)
            pkg_dir = find_package(pkg, nm_dirs)
            if pkg_dir is None:
                if find_package("@types/" + pkg.replace("@", "").replace("/", "__"), nm_dirs):
                    continue
                fails.append(f"{rel}: package '{pkg}' is not installed (import '{spec}')")
                continue
            if pkg in ICON_PACKAGES and names:
                sub = spec[len(pkg):].strip("/")
                exported = exports_of(pkg_dir, sub)
                if exported is None:
                    warns.append(f"{rel}: could not read the exports of '{spec}' to verify icon names")
                    continue
                for n in names:
                    stats["icons"] += 1
                    if n not in exported:
                        close = difflib.get_close_matches(n, list(exported), n=1, cutoff=0.6)
                        hint = f" (did you mean '{close[0]}'?)" if close else ""
                        fails.append(f"{rel}: '{n}' is not exported by '{spec}'{hint}")

    # --- fonts
    catalog = load_catalog()
    fonts = catalog.get("fonts", {})
    lang_code = page_lang(root, lang)
    needed_subset = None
    if lang_code:
        needed_subset = LANG_SUBSET.get(lang_code) or LANG_SUBSET.get(lang_code.split("-")[0])
    if not needed_subset and cjk_present([f for f in files if f.suffix in SRC_EXT]):
        needed_subset = "chinese-simplified"
        lang_code = lang_code or "(CJK text found in source)"
    loaded: set[str] = set()
    declared_faces: set[str] = set()

    def check_google(fam: str, weights: set, where: str):
        stats["fonts"] += 1
        meta = fonts.get(fam)
        if meta is None:
            close = difflib.get_close_matches(fam, list(fonts), n=1, cutoff=0.75)
            hint = f" (did you mean '{close[0]}'?)" if close else ""
            fails.append(f"{where}: '{fam}' is not a Google Fonts family{hint} — the link will 400 and the page falls back silently")
            return
        loaded.add(fam.lower())
        if weights and -1 not in weights and not meta.get("variable"):
            missing = sorted(w for w in weights if w not in meta["weights"])
            if missing:
                warns.append(f"{where}: '{fam}' has no weight {missing} (has {meta['weights']}); the browser will synthesize or substitute")
        if needed_subset and needed_subset not in meta["subsets"]:
            warns.append(f"{where}: '{fam}' has no {needed_subset} subset — text in that script renders in the fallback face, not in {fam} (lang {lang_code})")

    for p in files:
        text = read(p)
        rel = os.path.relpath(p, root)
        if p.suffix in {".html", ".tsx", ".jsx", ".astro", ".vue", ".svelte", ".ts", ".js"}:
            for fam, weights, _ in google_link_families(text):
                check_google(fam, weights, rel)
            if "next/font/google" in text:
                for fam, weights in next_font_imports(text):
                    check_google(fam, weights, rel)
            if "next/font/local" in text:
                for src in re.findall(r"src\s*:\s*['\"]([^'\"]+)['\"]", text):
                    if not (p.parent / src).exists() and not (root / src.lstrip("./")).exists():
                        fails.append(f"{rel}: next/font/local src '{src}' does not exist")
        if p.suffix == ".css":
            for fam, srcs, cp in font_face_decls(text, p, root):
                declared_faces.add(fam.lower())
                for s in srcs:
                    if s.startswith(("http", "data:")):
                        continue
                    cand = [(p.parent / s), (root / "public" / s.lstrip("/")), (root / s.lstrip("/"))]
                    if not any(c.exists() for c in cand):
                        fails.append(f"{rel}: @font-face '{fam}' src '{s}' does not exist")
    # font-family stacks whose first family is nothing the page loads
    for p in files:
        if p.suffix != ".css":
            continue
        rel = os.path.relpath(p, root)
        for first in font_family_stacks(read(p)):
            low = first.lower()
            if low in SYSTEM_FONTS or low in loaded or low in declared_faces or low.startswith("var("):
                continue
            if low in {k.lower() for k in fonts} and low not in loaded:
                warns.append(f"{rel}: font-family '{first}' is a Google Fonts family but nothing loads it (no <link>, next/font or @font-face) — it renders only where installed locally")
            elif low not in {k.lower() for k in fonts}:
                warns.append(f"{rel}: font-family '{first}' is neither loaded by the page nor a known system face")

    # --- output (a family linked from two files is one finding)
    fails = list(dict.fromkeys(fails))
    warns = list(dict.fromkeys(warns))
    for f in fails:
        print(f"FAIL  {f}")
    for w in warns:
        print(f"WARN  {w}")
    lang_note = f" · page language {lang_code}" if lang_code else ""
    cat = catalog.get("meta", {})
    print(f"Facts: {stats['imports']} imports across {len(stats['packages'])} packages, {len([f for f in fails if 'not installed' in f])} missing · "
          f"{stats['icons']} icon names checked, {len([f for f in fails if 'not exported' in f])} wrong · "
          f"{stats['fonts']} web fonts checked against Google Fonts ({cat.get('families', '?')} families, {cat.get('updated', '?')}), "
          f"{len([f for f in fails if 'Google Fonts family' in f or 'does not exist' in f])} missing{lang_note} · {len(warns)} warnings")
    return 1 if (strict and fails) else 0


if __name__ == "__main__":
    sys.exit(main())
