#!/usr/bin/env node
/**
 * ui-craft flutter_render — render.mjs for a Flutter app.
 *
 * Flutter paints its own pixels (on the web too: a canvas, no DOM to audit), so this script renders
 * through Flutter itself. It writes a widget test into <project>/.ui-craft/render_test.dart and runs
 * it with `flutter test`. The test:
 *   - loads the fonts a test lacks: Roboto (Material's face), Material Icons, every font the app and
 *     its packages declare, and the Google Fonts files the app asks google_fonts for (fetched once,
 *     cached); without them a widget test draws every glyph as a box;
 *   - mocks shared_preferences and path_provider, then starts the app through its own main();
 *   - opens a route the way a deep link arrives (--route), taps its way somewhere (--tap), or pushes
 *     one screen over the app (--widget);
 *   - at 375 / 768 / 1440, in light and under a dark platform brightness, and at 375 with text at
 *     200 %, saves a screenshot and runs Flutter's own accessibility guidelines (text contrast on the
 *     rendered pixels, tap targets of 48dp and 44pt, a label on every tappable node), and records
 *     each layout overflow ("A RenderFlex overflowed by …") with the widget in the app's code.
 *
 * Usage:
 *   node flutter_render.mjs <project> [--out DIR] [--route /path] [--tap TEXT]... [--widget EXPR]
 *
 * Writes  DIR/contact.png          light, all widths and the 200 % text pass, one image (look first)
 *         DIR/contact-dark.png     dark, when the app has a dark theme
 *         DIR/<width>.png  DIR/<width>-dark.png  DIR/<width>-text200.png
 *         DIR/report.json          every measurement, per pass
 * Needs   the Flutter SDK (flutter on PATH, FLUTTER_ROOT, or .fvm/flutter_sdk), and playwright in this
 *         folder for the contact sheets (the screenshots are written without it).
 */
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { delimiter, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

const USAGE = `usage: node flutter_render.mjs <project> [options]
  --out DIR            output folder (default .ui-craft/latest)
  --target FILE        the entry file whose main() starts the app (default lib/main.dart; a flavor: lib/main_dev.dart)
  --route /path        open this route after start, the way a deep link arrives (go_router, auto_route, named routes)
  --tap TEXT           tap the widget with this text, semantics label or tooltip ('key:NAME' for a ValueKey)
  --enter FIELD=TEXT   type into the text field labelled or hinted FIELD ('key:NAME', or its index on the screen from 0)
                       --route, --tap and --enter run in the order given: --enter Email=a@b.co --enter Password=x --tap 'Sign in'
  --widget EXPR        push one screen over the running app: a Dart expression, with \`context\` in scope
                       ('SettingsScreen()', 'LoginScreen(viewModel: LoginViewModel(authRepository: context.read()))');
                       the files that declare its names are imported
  --import URI         an extra import for --widget (package:foo/foo.dart, or lib/a/b.dart) (repeatable)
  --standalone         with --widget: do not start the app, pump the screen in a MaterialApp with the app's theme
                       (for an app whose main() cannot start in a test: Firebase, a server)
  --theme EXPR / --dark-theme EXPR   the ThemeData for --standalone (default: the app's MaterialApp theme, when static)
  --prefs KEY=VALUE    a shared_preferences value before start: a session token, an onboarding flag (repeatable)
  --setup FILE.dart    a file with \`Future<void> setUpApp() async {…}\`, run before main(): mock another plugin's channel
  --viewports A,B,C    widths in logical pixels (default 375,768,1440)
  --no-dark            skip the dark pass  ·  --dark-first  start under a dark platform brightness (an app that reads it once)
  --no-text-scale      skip the 200 % text pass
  --network            let the app reach the network (a widget test answers every request with HTTP 400): images from
                       the web load, and an API the machine can reach answers
  --compare DIR        pixel-diff every screenshot against the same-named one in DIR (a previous run)
  --timeout SECONDS    give up on \`flutter test\` after this long (default 600)
env  FLUTTER_ROOT      the Flutter SDK to use`;

// ---------------------------------------------------------------- arguments
const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log(USAGE);
  process.exit(argv.length ? 0 : 1);
}
const opt = {
  out: '.ui-craft/latest', target: null, steps: [], widget: null, imports: [], standalone: false,
  theme: null, darkTheme: null, prefs: [], setup: null, viewports: [375, 768, 1440], dark: true, darkFirst: false,
  textScale: true, compare: null, timeout: 600, network: false,
};
let projectArg = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out') opt.out = argv[++i];
  else if (a === '--target') opt.target = argv[++i];
  else if (a === '--route') opt.steps.push(`route:${argv[++i]}`);
  else if (a === '--tap') opt.steps.push(`tap:${argv[++i]}`);
  else if (a === '--enter') { const v = argv[++i] || ''; if (v.indexOf('=') < 1) { console.error('--enter needs FIELD=TEXT'); process.exit(1); } opt.steps.push(`enter:${v}`); }
  else if (a === '--widget') opt.widget = argv[++i];
  else if (a === '--import') opt.imports.push(argv[++i]);
  else if (a === '--standalone') opt.standalone = true;
  else if (a === '--theme') opt.theme = argv[++i];
  else if (a === '--dark-theme') opt.darkTheme = argv[++i];
  else if (a === '--prefs') { const v = argv[++i] || ''; const k = v.indexOf('='); if (k > 0) opt.prefs.push([v.slice(0, k), v.slice(k + 1)]); }
  else if (a === '--setup') opt.setup = argv[++i];
  else if (a === '--viewports') opt.viewports = argv[++i].split(',').map(Number).filter((n) => n > 0);
  else if (a === '--no-dark') opt.dark = false;
  else if (a === '--dark-first') opt.darkFirst = true;
  else if (a === '--no-text-scale') opt.textScale = false;
  else if (a === '--network') opt.network = true;
  else if (a === '--compare') opt.compare = resolve(argv[++i]);
  else if (a === '--timeout') opt.timeout = Number(argv[++i]) || 600;
  else if (a.startsWith('--')) { console.error(`unknown option ${a}\n${USAGE}`); process.exit(1); }
  else projectArg = a;
}
if (!projectArg || !opt.viewports.length) { console.error(USAGE); process.exit(1); }
if (opt.standalone && !opt.widget) { console.error('--standalone needs --widget: the screen to pump'); process.exit(1); }

const project = resolve(projectArg);
const pubspecPath = join(project, 'pubspec.yaml');
if (!existsSync(pubspecPath)) { console.error(`no pubspec.yaml in ${project}: pass the Flutter app's folder`); process.exit(1); }
const pubspec = readFileSync(pubspecPath, 'utf8');
const pkgName = (/^name:\s*["']?([\w]+)/m.exec(pubspec) || [])[1];
if (!pkgName) { console.error('pubspec.yaml has no name'); process.exit(1); }
if (!/^\s+flutter:\s*\n\s+sdk:\s*flutter/m.test(pubspec)) { console.error(`${pkgName} does not depend on Flutter (no \`flutter: sdk: flutter\` in pubspec.yaml)`); process.exit(1); }
const out = resolve(opt.out);
mkdirSync(out, { recursive: true });

// ---------------------------------------------------------------- the SDK
function findFlutter() {
  const exe = process.platform === 'win32' ? 'flutter.bat' : 'flutter';
  const cands = [];
  if (process.env.FLUTTER_ROOT) cands.push(join(process.env.FLUTTER_ROOT, 'bin', exe));
  for (let d = project; ; d = dirname(d)) {
    cands.push(join(d, '.fvm', 'flutter_sdk', 'bin', exe)); // fvm pins a version per project
    if (dirname(d) === d) break;
  }
  for (const p of (process.env.PATH || '').split(delimiter)) if (p) cands.push(join(p, exe));
  const home = homedir();
  for (const p of ['flutter', 'development/flutter', 'fvm/default', 'sdk/flutter', 'snap/flutter/common/flutter']) cands.push(join(home, p, 'bin', exe));
  cands.push('/opt/flutter/bin/flutter', '/usr/local/flutter/bin/flutter');
  for (const c of cands) {
    if (!existsSync(c)) continue;
    const real = realpathSync(c);
    return { bin: real, root: dirname(dirname(real)) };
  }
  return null;
}
const flutter = findFlutter();
if (!flutter) {
  console.error('Flutter SDK not found (flutter on PATH, FLUTTER_ROOT, or .fvm/flutter_sdk). Install it: https://docs.flutter.dev/get-started/install — or review statically with inspect.py and the stack notes.');
  process.exit(2);
}
const env = { ...process.env, FLUTTER_SUPPRESS_ANALYTICS: 'true', FLUTTER_ROOT: flutter.root };
let materialFonts = join(flutter.root, 'bin', 'cache', 'artifacts', 'material_fonts');
if (!existsSync(materialFonts)) spawnSync(flutter.bin, ['precache', '--universal'], { env, stdio: 'ignore', timeout: 300000 });
const sdkVersion = (() => {
  try { return JSON.parse(readFileSync(join(flutter.root, 'bin', 'cache', 'flutter.version.json'), 'utf8')).frameworkVersion; } catch { /* older SDK */ }
  try { return readFileSync(join(flutter.root, 'version'), 'utf8').trim(); } catch { return null; }
})();

// ---------------------------------------------------------------- packages
function packageConfig() {
  for (let d = project; ; d = dirname(d)) {
    const f = join(d, '.dart_tool', 'package_config.json');
    if (existsSync(f)) {
      try {
        const j = JSON.parse(readFileSync(f, 'utf8'));
        const pk = new Map();
        for (const p of j.packages || []) {
          const root = p.rootUri.startsWith('file:') ? fileURLToPath(p.rootUri) : resolve(dirname(f), p.rootUri);
          pk.set(p.name, { root, lib: join(root, p.packageUri || 'lib/') });
        }
        if (pk.has(pkgName)) return { file: f, packages: pk };
      } catch { /* unreadable: pub get rewrites it */ }
    }
    if (dirname(d) === d) return null;
  }
}
let pc = packageConfig();
if (!pc || statSync(pubspecPath).mtimeMs > statSync(pc.file).mtimeMs + 1000) {
  console.log(`  flutter pub get (${pc ? 'pubspec.yaml changed since the last one' : 'first run'})…`);
  const r = spawnSync(flutter.bin, ['pub', 'get'], { cwd: project, env, encoding: 'utf8', timeout: 600000 });
  if (r.status !== 0) {
    console.error(`flutter pub get failed:\n${(r.stderr || r.stdout || '').split('\n').filter(Boolean).slice(-12).join('\n')}`);
    process.exit(2);
  }
  pc = packageConfig();
  if (!pc) { console.error('flutter pub get ran, but no package_config.json lists this package'); process.exit(2); }
}
const pk = pc.packages;
const libFile = (name, rel) => (pk.has(name) ? join(pk.get(name).lib, rel) : null);

// ---------------------------------------------------------------- Dart sources
function walk(dir, ext, acc = []) {
  let entries = [];
  try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of entries) {
    if (e.name.startsWith('.')) continue;
    const p = join(dir, e.name);
    if (e.isDirectory()) walk(p, ext, acc);
    else if (e.name.endsWith(ext)) acc.push(p);
  }
  return acc;
}
const stripComments = (s) => s.replace(/'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, (m) => (m[0] === '/' ? ' ' : m));
const libDir = join(project, 'lib');
const dartFiles = walk(libDir, '.dart');
const toPackageUri = (abs) => {
  const rel = relative(libDir, abs);
  return rel.startsWith('..') || isAbsolute(rel) ? null : `package:${pkgName}/${rel.split('\\').join('/')}`;
};
const importUri = (p) => {
  if (/^(package|dart):/.test(p)) return p;
  const abs = resolve(project, p);
  return toPackageUri(abs) || relative(join(project, '.ui-craft'), abs).split('\\').join('/');
};

// The entry: its main() starts the app.
const entryAbs = resolve(project, opt.target || 'lib/main.dart');
let mainArgs = '';
if (!opt.standalone) {
  if (!existsSync(entryAbs)) { console.error(`${relative(project, entryAbs)} not found: pass the entry with --target, or pump one screen with --widget … --standalone`); process.exit(1); }
  const m = /^(?:[\w<>?]+\s+)?main\s*\(([^)]*)\)/m.exec(stripComments(readFileSync(entryAbs, 'utf8')));
  if (!m) { console.error(`no main() in ${relative(project, entryAbs)}: pass the entry with --target`); process.exit(1); }
  if (m[1].trim()) mainArgs = 'const <String>[]';
}

// Where the names in a Dart expression are declared in lib/: those files are imported for it.
const DART_WORDS = new Set('abstract as assert async await break case catch class const continue default do else enum extends false final finally for if in is late new null on required return super switch this throw true try var void while with yield context animation secondaryAnimation'.split(' '));
let declIndex = null;
function declarations() {
  if (declIndex) return declIndex;
  declIndex = new Map();
  const partOwner = new Map();
  const sources = dartFiles.map((f) => [f, stripComments(readFileSync(f, 'utf8'))]);
  for (const [f, s] of sources) for (const m of s.matchAll(/^part\s+'([^']+)'/gm)) partOwner.set(resolve(dirname(f), m[1]), f);
  for (const [f, s] of sources) {
    if (/^part\s+of\b/m.test(s) && !partOwner.has(f)) continue;
    const lib = partOwner.get(f) || f;
    const add = (n) => { if (!declIndex.has(n)) declIndex.set(n, lib); };
    for (const m of s.matchAll(/^(?:(?:abstract|sealed|final|base|interface|mixin)\s+)*(?:class|enum|mixin|typedef|extension\s+type)\s+([A-Za-z_]\w*)/gm)) add(m[1]);
    for (const m of s.matchAll(/^(?:(?:late|final|const|var)\s+)+(?:[\w<>?,. ]+\s+)?([A-Za-z_]\w*)\s*=/gm)) add(m[1]);
    // a top-level function or getter: at column 0 (anything indented is inside a class or a body)
    for (const m of s.matchAll(/^(?!(?:import|export|part|library|class|enum|mixin|typedef|extension|abstract|sealed|base|interface|final|const|var|late|return)\b)(?:[A-Za-z_][\w<>?,. ]*\s+)?(?:get\s+)?([A-Za-z_]\w*)\s*(?:\(|=>)/gm)) add(m[1]);
  }
  return declIndex;
}
function importsFor(expr) {
  if (!expr) return [];
  const s = expr.replace(/'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"/g, "''");
  const files = new Set();
  for (const m of s.matchAll(/(^|[^.\w$])([A-Za-z_]\w*)/g)) {
    const id = m[2];
    if (DART_WORDS.has(id)) continue;
    if (/^\s*:(?!:)/.test(s.slice(m.index + m[0].length))) continue; // a named argument
    const f = declarations().get(id);
    if (f) files.add(f);
  }
  return [...files].map((f) => toPackageUri(f)).filter(Boolean);
}

// The app's MaterialApp theme and localizations, for --standalone: each is used when it is a plain
// reference (AppTheme.light, AppLocalizations.localizationsDelegates) or a list of them.
const plainRef = (v) => /^[A-Za-z_][\w.]*(\(\))?$/.test(v);
const plainList = (v) => {
  const m = /^(?:const\s+)?(?:<[\w<>?, ]+>\s*)?\[([\s\S]*)\]$/.exec(v);
  return !!m && m[1].split(',').map((x) => x.trim()).filter(Boolean).every(plainRef);
};
function appThemes() {
  const found = { theme: null, darkTheme: null, localizationsDelegates: null, supportedLocales: null, file: null };
  const ordered = [entryAbs, ...dartFiles.filter((f) => f !== entryAbs)];
  for (const f of ordered) {
    if (!existsSync(f)) continue;
    const s = stripComments(readFileSync(f, 'utf8'));
    const i = s.search(/\bMaterialApp(?:\.router)?\s*\(/);
    if (i < 0) continue;
    const args = balanced(s, s.indexOf('(', i));
    for (const k of ['theme', 'darkTheme', 'localizationsDelegates', 'supportedLocales']) {
      const m = new RegExp(`(?:^|[\\s,(])${k}\\s*:\\s*`).exec(args);
      if (!m) continue;
      const v = topLevelArg(args.slice(m.index + m[0].length)).replace(/,\s*\]$/, ']');
      if (plainRef(v) || (k.startsWith('l') || k.startsWith('s') ? plainList(v) : false)) found[k] = v;
    }
    found.file = f;
    break;
  }
  return found;
}
function balanced(s, open) {
  let depth = 0;
  for (let i = open; i < s.length; i++) {
    const c = s[i];
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { depth--; if (!depth) return s.slice(open + 1, i); }
  }
  return s.slice(open + 1);
}
function topLevelArg(s) {
  let depth = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { if (!depth) return s.slice(0, i).trim(); depth--; }
    else if (c === ',' && !depth) return s.slice(0, i).trim();
  }
  return s.trim();
}

// ---------------------------------------------------------------- Google Fonts
// google_fonts downloads each face at run time, and a test has no network: every text in such a face
// would be boxes. The package lists each face's file by hash (fonts.gstatic.com/s/a/<hash>.ttf);
// fetch those once into a cache, and the test registers them under the names google_fonts uses
// (OpenSans_regular, OpenSans_700, …, with the family name as the fallback).
async function googleFonts() {
  if (!pk.has('google_fonts')) return { families: [], failed: [] };
  const methods = new Set(), names = new Set();
  for (const f of dartFiles) {
    const s = readFileSync(f, 'utf8');
    for (const m of s.matchAll(/GoogleFonts\s*\.\s*([a-z]\w*)\s*\(/g)) {
      if (!['getFont', 'getTextTheme', 'asMap', 'pendingFonts'].includes(m[1])) methods.add(m[1].replace(/TextTheme$/, ''));
    }
    for (const m of s.matchAll(/GoogleFonts\s*\.\s*(?:getFont|getTextTheme)\s*\(\s*['"]([^'"]+)['"]/g)) names.add(m[1]);
  }
  if (!methods.size && !names.size) return { families: [], failed: [] };
  const all = walk(pk.get('google_fonts').lib, '.dart').map((f) => readFileSync(f, 'utf8')).join('\n');
  for (const n of names) {
    const m = new RegExp(`'${n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}'\\s*:\\s*(?:\\w+\\.)?(\\w+)`).exec(all);
    if (m) methods.add(m[1].replace(/TextTheme$/, ''));
  }
  const cache = join(process.env.XDG_CACHE_HOME || join(homedir(), '.cache'), 'ui-craft', 'google-fonts');
  mkdirSync(cache, { recursive: true });
  const families = [], failed = [];
  for (const meth of methods) {
    const i = all.search(new RegExp(`static TextStyle ${meth}\\s*\\(`));
    if (i < 0) continue;
    const rest = all.slice(i + 20);
    const end = rest.search(/static Text(?:Style|Theme)\b/);
    const block = all.slice(i, end < 0 ? i + 20000 : i + 20 + end);
    const family = (/fontFamily:\s*'([^']+)'/.exec(block) || [])[1];
    const variants = [...block.matchAll(/GoogleFontsVariant\(\s*fontWeight:\s*FontWeight\.w(\d+),\s*fontStyle:\s*FontStyle\.(\w+),?\s*\)\s*:\s*GoogleFontsFile\(\s*'([0-9a-f]+)'/g)]
      .map((m) => ({ weight: Number(m[1]), italic: m[2] === 'italic', hash: m[3] }));
    if (!family || !variants.length) continue;
    const files = [];
    for (const v of variants) {
      const path = join(cache, `${v.hash}.ttf`);
      if (!existsSync(path) || statSync(path).size < 1000) {
        const url = `https://fonts.gstatic.com/s/a/${v.hash}.ttf`;
        let ok = false;
        try {
          const r = await fetch(url, { signal: AbortSignal.timeout(20000) });
          if (r.ok) { writeFileSync(path, Buffer.from(await r.arrayBuffer())); ok = true; }
        } catch { /* no fetch through this network: try curl, which reads the proxy settings */ }
        if (!ok) ok = spawnSync('curl', ['-sSfL', '--max-time', '20', '-o', path, url], { stdio: 'ignore' }).status === 0;
        if (!ok) continue;
      }
      const name = v.weight === 400 ? (v.italic ? 'italic' : 'regular') : `${v.weight}${v.italic ? 'italic' : ''}`;
      files.push({ family: `${family}_${name}`, path, hash: v.hash });
    }
    if (files.length) families.push({ method: meth, family, files });
    else failed.push(family);
  }
  return { families, failed };
}

// ---------------------------------------------------------------- the test file
const dartStr = (s) => (s == null ? 'null' : `'${String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\$/g, '\\$').replace(/\n/g, '\\n')}'`);
function dartValue(v) {
  if (v === 'true' || v === 'false') return v;
  if (/^-?\d+$/.test(v)) return v;
  if (/^-?\d+\.\d+$/.test(v)) return v;
  if (/^\[.*\]$/.test(v)) { try { const a = JSON.parse(v); if (Array.isArray(a)) return `<String>[${a.map((x) => dartStr(String(x))).join(', ')}]`; } catch { /* a plain string */ } }
  return dartStr(v);
}

const gf = await googleFonts();
// google_fonts looks for a face in the app's support folder before it fetches it (the path_provider
// mock below points that folder at .ui-craft/tmp/support): put the files there too, so it loads them
// itself instead of failing on the test's network (HTTP 400) and reporting it as an error.
if (gf.families.length) {
  const support = join(project, '.ui-craft', 'tmp', 'support');
  mkdirSync(support, { recursive: true });
  for (const f of gf.families) for (const x of f.files) {
    for (const n of [`${x.family}_${x.hash}.ttf`, `${x.family}.ttf`]) if (!existsSync(join(support, n))) writeFileSync(join(support, n), readFileSync(x.path));
  }
}
const imports = [];
const mocks = [];
const classes = [];
if (!opt.standalone) imports.push(`import ${dartStr(importUri(entryAbs))} as app;`);
const exprImports = new Set([...importsFor(opt.widget)]);
for (const u of opt.imports) exprImports.add(importUri(u));
let themes = { theme: opt.theme, darkTheme: opt.darkTheme, localizationsDelegates: null, supportedLocales: null, file: null };
if (opt.standalone) {
  const t = appThemes();
  themes = { ...t, theme: opt.theme || t.theme, darkTheme: opt.darkTheme || (opt.theme ? null : t.darkTheme) };
}
for (const k of ['theme', 'darkTheme', 'localizationsDelegates', 'supportedLocales']) for (const u of importsFor(themes[k])) exprImports.add(u);
if (/Global(Material|Widgets|Cupertino)Localizations/.test(`${themes.localizationsDelegates || ''}`) && pk.has('flutter_localizations')) exprImports.add('package:flutter_localizations/flutter_localizations.dart');
if (opt.widget && /\bcontext\s*\.\s*(read|watch|select)\b/.test(opt.widget)) {
  for (const p of ['provider', 'flutter_bloc']) if (pk.has(p) && existsSync(libFile(p, `${p}.dart`))) exprImports.add(`package:${p}/${p}.dart`);
}
if (opt.widget && /\bcontext\s*\.\s*(go|push|pushNamed|goNamed)\b/.test(opt.widget) && pk.has('go_router')) exprImports.add('package:go_router/go_router.dart');
for (const u of exprImports) imports.push(`import ${dartStr(u)};`);

const prefsMap = opt.prefs.map(([k, v]) => `${dartStr(k)}: ${dartValue(v)}`).join(', ');
const mocked = [];
if (pk.has('shared_preferences')) {
  imports.push("import 'package:shared_preferences/shared_preferences.dart' as uic_prefs;");
  mocks.push(`  uic_prefs.SharedPreferences.setMockInitialValues(<String, Object>{${prefsMap}});`);
  if (existsSync(libFile('shared_preferences_platform_interface', 'in_memory_shared_preferences_async.dart') || '')) {
    imports.push("import 'package:shared_preferences_platform_interface/in_memory_shared_preferences_async.dart' as uic_prefs_mem;");
    imports.push("import 'package:shared_preferences_platform_interface/shared_preferences_async_platform_interface.dart' as uic_prefs_async;");
    mocks.push(`  uic_prefs_async.SharedPreferencesAsyncPlatform.instance = uic_prefs_mem.InMemorySharedPreferencesAsync.withData(<String, Object>{${prefsMap}});`);
  }
  mocked.push('shared_preferences');
} else if (opt.prefs.length) {
  console.error('--prefs sets shared_preferences values, and this app does not use shared_preferences');
  process.exit(1);
}
if (pk.has('path_provider_platform_interface') && existsSync(libFile('path_provider_platform_interface', 'path_provider_platform_interface.dart') || '')) {
  imports.push("import 'package:path_provider_platform_interface/path_provider_platform_interface.dart' as uic_paths;");
  mocks.push('  uic_paths.PathProviderPlatform.instance = _Paths();');
  classes.push(`// Folders under .ui-craft/tmp for every path_provider call: Hive, caches and databases open there.
class _Paths extends uic_paths.PathProviderPlatform {
  Future<String?> _dir(String name) async => (uicio.Directory('$_root/.ui-craft/tmp/$name')..createSync(recursive: true)).path;
  @override
  Future<String?> getTemporaryPath() => _dir('temp');
  @override
  Future<String?> getApplicationSupportPath() => _dir('support');
  @override
  Future<String?> getLibraryPath() => _dir('library');
  @override
  Future<String?> getApplicationDocumentsPath() => _dir('documents');
  @override
  Future<String?> getApplicationCachePath() => _dir('cache');
  @override
  Future<String?> getExternalStoragePath() => _dir('external');
  @override
  Future<String?> getDownloadsPath() => _dir('downloads');
}`);
  mocked.push('path_provider');
}
if (opt.setup) {
  const abs = resolve(project, opt.setup);
  if (!existsSync(abs)) { console.error(`--setup ${opt.setup}: not found`); process.exit(1); }
  imports.push(`import ${dartStr(importUri(abs))} as uic_setup;`);
  mocks.push('  await uic_setup.setUpApp();');
}

const start = opt.standalone
  ? `  _phase = 'widget';
  await tester.pumpWidget(uic.MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ${themes.theme || 'null'},
    darkTheme: ${themes.darkTheme || 'null'},${themes.localizationsDelegates ? `
    localizationsDelegates: ${themes.localizationsDelegates},` : ''}${themes.supportedLocales ? `
    supportedLocales: ${themes.supportedLocales},` : ''}
    home: uic.Builder(builder: (BuildContext context) => ${opt.widget}),
  ));`
  : `  _phase = 'main';
  await tester.runAsync(() async {
    try {
      final Object? r = (app.main as Function)(${mainArgs});
      if (r is uica.Future) await r.timeout(const Duration(seconds: 30));
    } on uica.TimeoutException {
      _note('main() did not finish within 30 s: it waits on a plugin, a server or a file a test does not have');
    }
  });
  await tester.pump();`;
const widgetPush = opt.widget && !opt.standalone
  ? `  _phase = 'widget';
  final nav = tester.state<uic.NavigatorState>(uict.find.byType(uic.Navigator).first);
  nav.push(uic.PageRouteBuilder<void>(
    transitionDuration: Duration.zero,
    reverseTransitionDuration: Duration.zero,
    pageBuilder: (BuildContext context, Animation<double> animation, Animation<double> secondaryAnimation) => ${opt.widget},
  ));
  await _settle(tester, 'widget');`
  : '';
const extraFonts = [];
for (const f of gf.families) {
  for (const x of f.files) extraFonts.push(`  ${dartStr(x.family)}: <String>[${dartStr(x.path)}],`);
  extraFonts.push(`  ${dartStr(f.family)}: <String>[${f.files.map((x) => dartStr(x.path)).join(', ')}],`);
}
const fill = {
  IMPORTS: imports.join('\n'),
  OUT: dartStr(out),
  ROOT: dartStr(project),
  PACKAGE: dartStr(pkgName),
  MATERIAL_FONTS: dartStr(materialFonts),
  WIDTHS: `<double>[${opt.viewports.map((w) => w.toFixed(1)).join(', ')}]`,
  DARK: String(opt.dark),
  DARK_FIRST: String(opt.darkFirst),
  TEXT_SCALE: String(opt.textScale),
  NETWORK: String(opt.network),
  STEPS: `<String>[${opt.steps.map(dartStr).join(', ')}]`,
  EXTRA_FONTS: extraFonts.length ? `<String, List<String>>{\n${extraFonts.join('\n')}\n}` : '<String, List<String>>{}',
  MOCKS: mocks.join('\n'),
  CLASSES: classes.join('\n\n'),
  START: start,
  WIDGET_PUSH: widgetPush,
};
const template = readFileSync(join(HERE, 'lib', 'flutter_harness.dart.tmpl'), 'utf8');
const code = template.replace(/\/\*\{\{(\w+)\}\}\*\//g, (m, k) => (k in fill ? fill[k] : m));
const uiDir = join(project, '.ui-craft');
mkdirSync(uiDir, { recursive: true });
if (!existsSync(join(uiDir, '.gitignore'))) writeFileSync(join(uiDir, '.gitignore'), '*\n');
const testFile = join(uiDir, 'render_test.dart');
writeFileSync(testFile, code);
// Last run's screenshots out of the way: a pass that does not happen this time must not leave its old picture.
for (const n of readdirSync(out)) if (/\.png$|^flutter-report\.json$/.test(n)) rmSync(join(out, n), { force: true });

// ---------------------------------------------------------------- run it
const tStart = Date.now();
const log = [];
const status = await new Promise((done) => {
  const args = ['test', '--no-pub', '-r', 'expanded', relative(project, testFile)];
  const child = spawn(flutter.bin, args, { cwd: project, env, stdio: ['ignore', 'pipe', 'pipe'] });
  const timer = setTimeout(() => { log.push(`\n[flutter_render] gave up after ${opt.timeout} s`); child.kill('SIGTERM'); }, opt.timeout * 1000);
  child.stdout.on('data', (d) => log.push(String(d)));
  child.stderr.on('data', (d) => log.push(String(d)));
  child.on('close', (code) => { clearTimeout(timer); done(code); });
  child.on('error', (e) => { clearTimeout(timer); log.push(String(e)); done(-1); });
});
const logText = log.join('');
writeFileSync(join(out, 'flutter-test.log'), logText);
const tTest = Date.now();

let rep = null;
try { rep = JSON.parse(readFileSync(join(out, 'flutter-report.json'), 'utf8')); } catch { /* the test never ran: compile errors below */ }
const rel = (p) => { const r = relative(process.cwd(), p); return r.startsWith('..') ? p : r || '.'; };

if (!rep || !(rep.passes || []).length) {
  console.log(`ui-craft flutter render → ${rel(out)}`);
  console.log(`  app: ${pkgName} · ${opt.standalone ? `--widget ${opt.widget} (standalone)` : `${relative(project, entryAbs)} main()`} · Flutter ${sdkVersion || '?'}`);
  const errs = [...logText.matchAll(/^([^\s:]+?\.dart):(\d+):(\d+): Error: (.+)$/gm)].map((m) => `${relative(project, resolve(project, m[1]))}:${m[2]}: ${m[4]}`);
  if (errs.length) {
    console.log(`  the test did not compile (${errs.length} error${errs.length > 1 ? 's' : ''}):`);
    for (const e of [...new Set(errs)].slice(0, 8)) console.log(`    ${e}`);
    if (errs.some((e) => /\.(g|freezed|gr|config|mocks)\.dart|part of|build_runner/.test(e))) console.log('  generated files are missing: run `dart run build_runner build --delete-conflicting-outputs` in the project first');
    else if (errs.some((e) => e.startsWith('.ui-craft/')) && (opt.widget || themes.theme || themes.darkTheme)) console.log(`  the error is in the expression passed (--widget / --theme) or a name it needs: pass the file that declares it with --import (the generated test: ${rel(testFile)})`);
    else if (errs.some((e) => e.startsWith('.ui-craft/'))) console.log(`  the error is in the harness itself, against Flutter ${sdkVersion || '?'} (it needs 3.10 or newer): ${rel(testFile)}`);
  } else if (rep && rep.crash) {
    printCrash(rep.crash);
  } else {
    const tail = logText.split('\n').filter((l) => l.trim()).slice(-15).join('\n    ');
    console.log(`  flutter test exited ${status} before any screenshot:\n    ${tail}`);
  }
  console.log(`  log: ${rel(join(out, 'flutter-test.log'))}`);
  process.exit(2);
}

function printCrash(c) {
  const where = c.where ? ` at ${c.where.file}:${c.where.line}` : '';
  console.log(`  stopped during ${c.phase}: ${c.error}${where}`);
  if (/MissingPluginException|PlatformException|channel/i.test(c.error)) console.log('  a plugin with no platform in a test: mock its channel in a --setup file, or pump the screen itself (--widget … --standalone)');
  if (/Firebase/i.test(c.error)) console.log('  Firebase does not start in a widget test: pump the screen itself (--widget … --standalone) with fakes for its data');
}

// ---------------------------------------------------------------- read the passes
const hex = (s) => {
  if (!s) return null;
  if (/^#[0-9A-F]{6}$/i.test(s)) return s.toUpperCase();
  let m = /0x([0-9a-f]{8})/i.exec(s);
  if (m) { const a = m[1].slice(0, 2).toUpperCase(); return `#${m[1].slice(2).toUpperCase()}${a === 'FF' ? '' : a}`; }
  m = /alpha:\s*([\d.]+),\s*red:\s*([\d.]+),\s*green:\s*([\d.]+),\s*blue:\s*([\d.]+)/.exec(s);
  if (m) {
    const [a, r, g, b] = m.slice(1).map(Number);
    const h = (x) => Math.round(x * 255).toString(16).padStart(2, '0').toUpperCase();
    return `#${h(r)}${h(g)}${h(b)}${a >= 0.999 ? '' : h(a)}`;
  }
  return null;
};
const whereStr = (w) => (w ? `${w.file}:${w.line}${w.widget ? ` (${w.widget})` : ''}` : null);
const passes = rep.passes;
const light = passes.filter((p) => !p.dark && p.textScale === 1);
const darkPasses = passes.filter((p) => p.dark && p.textScale === 1);
const scaled = passes.filter((p) => p.textScale !== 1);
const fontFetch = (e) => /Failed to load font with url|google_fonts was unable to load font/.test(e.summary);
const fontFetchErrors = (rep.errors || []).filter(fontFetch).length;
rep.errors = (rep.errors || []).filter((e) => !fontFetch(e));
const errorsOf = (key) => rep.errors.filter((e) => e.phase === key);
const overflowOf = (key) => errorsOf(key).filter((e) => /overflowed by/.test(e.summary));

// The dark pass moved nothing: no dark theme (or one chosen in the app's own settings).
const sameShot = (a, b) => { try { return readFileSync(join(out, a.shot)).equals(readFileSync(join(out, b.shot))); } catch { return false; } };
const darkUnchanged = darkPasses.length > 0 && darkPasses.every((d) => {
  const l = light.find((p) => p.width === d.width);
  return l && (sameShot(l, d) || (l.brightness === d.brightness && l.background === d.background));
});
const counted = darkUnchanged ? [...light, ...scaled] : passes;

for (const p of passes) {
  const guideline = (p.contrast.failures || []).map((f) => {
    const m = /Expected contrast ratio of at least ([\d.]+) but found ([\d.]+) for a font size of ([\d.]+|null)/.exec(f.reason) || [];
    const c = /light - (Color\([^)]*\)), dark - (Color\([^)]*\))/.exec(f.reason) || [];
    const colors = [hex(c[1]), hex(c[2])];
    return { text: f.label || f.value || '', need: Number(m[1]) || null, ratio: Number(m[2]) || null, size: m[3] && m[3] !== 'null' ? Number(m[3]) : null, fg: colors[1], bg: colors[0], where: f.where, rect: f.rect, source: 'guideline' };
  });
  // The per-text check is the one findings come from. Flutter's guideline takes the commonest dark
  // and light pixels in a text's box, so anti-aliased edges and dividers read as the text colour
  // (black list items at 4.17:1 on cupertino_gallery): its count is reported beside, not merged.
  const own = ((p.text || {}).failures || []);
  const contrast = own.filter((f) => !f.icon);
  const iconContrast = own.filter((f) => f.icon);
  const size = (f) => { const m = /but found Size\(([\d.]+), ([\d.]+)\)/.exec(f.reason); return m ? [Number(m[1]), Number(m[2])] : f.rect ? [f.rect[2], f.rect[3]] : null; };
  const targets = (p.android.failures || []).map((f) => ({ ...f, size: size(f) }));
  p.findings = {
    contrast,
    iconContrast,
    guideline,
    below24: targets.filter((t) => t.size && Math.min(...t.size) < 24),
    below48: targets.filter((t) => t.size && Math.min(...t.size) >= 24),
    below44: (p.ios.failures || []).length,
    unlabeled: p.unlabeled.failures || [],
    overflow: overflowOf(p.key),
    errors: errorsOf(p.key).filter((e) => !/overflowed by|statusCode: 4\d\d|NetworkImageLoadException|HTTP request failed|SocketException|Failed host lookup|ClientException/.test(e.summary)),
  };
  const f = p.findings;
  p.fails = [];
  p.warns = [];
  if (f.contrast.length) p.fails.push(`contrast ${f.contrast.length}`);
  if (f.iconContrast.length) p.fails.push(`icon contrast ${f.iconContrast.length}`);
  if (f.overflow.length) p.fails.push(`overflow ${f.overflow.length}`);
  if (f.below24.length) p.fails.push(`targets<24 ${f.below24.length}`);
  if (f.unlabeled.length) p.fails.push(`unlabeled ${f.unlabeled.length}`);
  if (f.below48.length) p.warns.push(`targets 24–48dp ${f.below48.length}`);
  if (f.errors.length) p.warns.push(`errors ${f.errors.length}`);
  if ((rep.unsettled || []).includes(p.key)) p.warns.push('never settled');
  // An image's error text (no network) is the network line's business, not a broken screen.
  p.errorScreen = p.errorWidget ? 'error widget' : (p.labels || []).slice(0, 4).find((t) => /(^|\s)(Error|Exception|Failed to)\b|Exception:/.test(t) && !/statusCode|HttpException|SocketException|ClientException|NetworkImageLoadException|Failed host lookup/.test(t)) || null;
  if (p.errorScreen) p.warns.unshift(p.errorWidget ? 'a build failed (error widget on screen)' : 'an error message on screen');
  p.status = p.fails.length ? 'FAIL' : 'PASS';
}

// ---------------------------------------------------------------- contact sheets and compare
let browser = null;
async function getBrowser() {
  if (browser) return browser;
  const { launchChromium, loadPlaywright } = await import('./lib/browser.mjs');
  browser = (await launchChromium(await loadPlaywright())).browser;
  return browser;
}
async function contactSheet(cells, name) {
  const gap = 24, pad = 24, labelH = 28;
  const totalW = pad * 2 + cells.reduce((s, f) => s + f.width, 0) + gap * (cells.length - 1);
  const maxH = Math.max(...cells.map((f) => f.height));
  const page = await (await getBrowser()).newPage({ viewport: { width: totalW, height: pad * 2 + labelH + maxH }, deviceScaleFactor: 1 });
  const html = cells.map((f) => `<figure style="margin:0;width:${f.width}px;flex:none"><figcaption style="font:600 14px system-ui,sans-serif;line-height:${labelH}px;height:${labelH}px;color:#333">${f.label}</figcaption><img src="data:image/png;base64,${readFileSync(join(out, f.shot)).toString('base64')}" style="width:${f.width}px;height:${f.height}px;display:block;border:1px solid #bbb;box-sizing:border-box;background:#fff"></figure>`).join('');
  await page.setContent(`<!doctype html><body style="margin:0;padding:${pad}px;background:#e6e6e6;display:flex;gap:${gap}px;align-items:flex-start">${html}</body>`, { waitUntil: 'load' });
  await page.screenshot({ path: join(out, name) });
  await page.close();
}
let sheetError = null;
const cell = (p) => ({ ...p, label: `${p.width} × ${p.height}${p.dark ? ' · dark' : ''}${p.textScale !== 1 ? ` · text ${Math.round(p.textScale * 100)} %` : ''}` });
let contact = null, contactDark = null;
try {
  await contactSheet([...light, ...scaled].map(cell), 'contact.png');
  contact = 'contact.png';
  if (darkPasses.length && !darkUnchanged) { await contactSheet(darkPasses.map(cell), 'contact-dark.png'); contactDark = 'contact-dark.png'; }
} catch (e) { sheetError = String(e.message || e).split('\n')[0]; }

let compare = null;
if (opt.compare) {
  compare = { baseline: opt.compare, files: {} };
  try {
    const page = await (await getBrowser()).newPage({ viewport: { width: 200, height: 200 } });
    for (const p of passes) {
      const base = join(opt.compare, p.shot);
      if (!existsSync(base)) { compare.files[p.shot] = { status: 'no baseline' }; continue; }
      const r = await page.evaluate(async ([ua, ub]) => {
        const load = (src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
        const [ia, ib] = await Promise.all([load(ua), load(ub)]);
        const w = Math.min(ia.width, ib.width), h = Math.min(ia.height, ib.height);
        const draw = (im) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, 0, 0); return x.getImageData(0, 0, w, h).data; };
        const da = draw(ia), db = draw(ib);
        let changed = 0, top = -1, bottom = -1;
        for (let i = 0; i < da.length; i += 4) {
          if (Math.abs(da[i] - db[i]) + Math.abs(da[i + 1] - db[i + 1]) + Math.abs(da[i + 2] - db[i + 2]) > 48) {
            changed++;
            const y = Math.floor(i / 4 / w);
            if (top < 0) top = y;
            bottom = y;
          }
        }
        return { changed, total: w * h, top, bottom, sizeChanged: ia.width !== ib.width || ia.height !== ib.height };
      }, [`data:image/png;base64,${readFileSync(base).toString('base64')}`, `data:image/png;base64,${readFileSync(join(out, p.shot)).toString('base64')}`]);
      compare.files[p.shot] = r.changed || r.sizeChanged
        ? { status: 'changed', pct: +((100 * r.changed) / r.total).toFixed(2), y: r.changed ? [Math.round(r.top / 2), Math.round(r.bottom / 2)] : null }
        : { status: 'identical' };
    }
    await page.close();
  } catch (e) { compare.error = String(e.message || e).split('\n')[0]; }
}
if (browser) await browser.close();

const report = {
  tool: 'flutter_render.mjs', project, package: pkgName, entry: opt.standalone ? null : relative(project, entryAbs), flutter: sdkVersion,
  options: { steps: opt.steps.map((x) => (x.startsWith('enter:') ? x.replace(/=.*/, '=…') : x)), widget: opt.widget, standalone: opt.standalone, theme: themes.theme, darkTheme: themes.darkTheme, prefs: opt.prefs.map(([k]) => k), setup: opt.setup },
  mocked, googleFonts: gf.families.map((f) => f.family), googleFontsFailed: gf.failed, fonts: rep.fonts, notes: rep.notes, steps: rep.steps,
  crash: rep.crash || null, unsettled: rep.unsettled, errors: rep.errors, darkUnchanged, passes, contact, contactDark, compare,
  timings: { test: tTest - tStart, total: Date.now() - tStart }, exitCode: status,
};
writeFileSync(join(out, 'report.json'), JSON.stringify(report, null, 2));

// ---------------------------------------------------------------- output
const label = (p) => (p.textScale !== 1 ? `${p.width} text ${Math.round(p.textScale * 100)}%` : `${p.width}${p.dark ? ' dark' : ''}`);
console.log(`ui-craft flutter render → ${rel(out)}`);
console.log(`  app: ${pkgName} · ${opt.standalone ? `${opt.widget} in a MaterialApp (theme ${themes.theme || 'the default'}${themes.darkTheme ? `, dark ${themes.darkTheme}` : ''}${themes.localizationsDelegates ? ', the app\'s localizations' : ''})` : `${relative(project, entryAbs)} main()`} · Flutter ${sdkVersion || '?'}${mocked.length ? ` · mocked: ${mocked.join(', ')}` : ''}`);
const steps = (rep.steps || []).map((s) => (s.route ? `route ${s.route}${s.handled ? '' : ' (nothing answered it: no router, or the path is unknown)'}` : s.enter != null ? `enter ${JSON.stringify(s.enter)}${s.found ? '' : ' (no such field)'}` : `tap ${JSON.stringify(s.tap)}${s.found ? '' : ' (not found)'}`));
if (opt.widget && !opt.standalone) steps.push(`pushed ${opt.widget}`);
if (steps.length) console.log(`  after: ${steps.join(' · ')}`);
if (contact) console.log(`  look first: ${rel(join(out, contact))} (${[...light, ...scaled].map((p) => label(p)).join(' / ')}, one image)${contactDark ? ` · dark: ${rel(join(out, contactDark))}` : ''}`);
else console.log(`  screenshots: ${rel(out)}/*.png${sheetError ? ` (no contact sheet: ${sheetError})` : ''}`);
for (const p of counted) {
  const detail = [...p.fails, ...p.warns.map((w) => `warn:${w}`)].join(' · ') || 'clean';
  console.log(`  ${label(p).padEnd(14)} ${p.status}  ${detail}`);
}
if (darkUnchanged) console.log(`  dark: tried under a dark platform brightness — the screen did not change (background ${light[0]?.background}): the app has no dark theme, or picks it in its own settings (--prefs with its key), or reads the brightness only at start (--dark-first)`);
if (rep.crash) printCrash(rep.crash);
{
  const first = light[0] || passes[0];
  // a route's own name only where it says something: go_router names its pages by pattern (:id)
  const place = [first.location ? `location ${first.location}` : null, first.routeName && (!first.location || first.routeName.startsWith('/')) && first.routeName !== first.location ? `route ${first.routeName}` : null].filter(Boolean).join(' · ');
  const flat = (t) => JSON.stringify(t.replace(/\s*\n\s*/g, ' · '));
  const heads = (first.headers || []).slice(0, 3).map(flat);
  const text = `${place}${heads.length ? `${place ? ' · ' : ''}headers ${heads.join(', ')}` : ''}${!heads.length && first.labels?.length ? `${place ? ' · ' : ''}text ${first.labels.slice(0, 4).map(flat).join(', ')}` : ''}`;
  // Only when the screen is not the one asked for: no steps were given, or the route asked for was redirected.
  const asked = [...opt.steps].reverse().find((x) => x.startsWith('route:'));
  const redirected = asked && first.location && !first.location.startsWith(asked.slice(6).split('?')[0]);
  const signIn = !opt.widget && (!opt.steps.length || redirected) && (/sign[ -]?in|log[ -]?in|登录/i.test(`${first.location || ''} ${first.routeName || ''} ${(first.headers || []).join(' ')}`)
    || (first.password && (first.labels || []).some((t) => /^(sign[ -]?in|log[ -]?in|continue|登录)$/i.test(t))));
  console.log(`  screen: ${text || '(no text, no header, no route name)'}${signIn ? '  ← looks like a sign-in screen: behind it, --prefs with the session key, --route after the check passes, or --widget for the screen itself' : ''}`);
}
{
  const bad = passes.find((p) => p.errorScreen);
  if (bad) {
    const msg = bad.errorWidget ? "Flutter's error box (a widget's build threw: the errors below say which)" : JSON.stringify(bad.errorScreen.slice(0, 90));
    const native = /dynamic library|DynamicLibrary|ffi|\.so\b|\.dylib/i.test(`${bad.errorScreen} ${JSON.stringify(rep.errors || [])}`);
    console.log(`  the screen shows an error, not the app: ${msg} — ${native ? 'a native library (Rust, FFI) that a widget test cannot load: ' : ''}the numbers above are for that screen. Pump a screen that does not need it (--widget … --standalone), or stub what failed in a --setup file`);
  }
}
const unsettled = [...new Set(rep.unsettled || [])];
if (unsettled.length) console.log(`  never settled (${unsettled.join(', ')}): an animation runs without end — a progress indicator waiting on data a test does not get (the network answers 400), or a repeating animation; the screenshots show it mid-way`);
const netErr = (e) => /statusCode: 4\d\d|NetworkImageLoadException|HTTP request failed|SocketException|Failed host lookup|ClientException/.test(e.summary);
{
  const hosts = new Map();
  for (const e of (rep.errors || []).filter(netErr)) {
    const h = (/(?:https?:)?\/\/([^/\s,:]+)/.exec(e.summary) || [])[1] || 'a host';
    hosts.set(h, (hosts.get(h) || new Set()).add((/(?:https?:)?\/\/\S+/.exec(e.summary) || [e.summary])[0]));
  }
  if (hosts.size) {
    const n = [...hosts.values()].reduce((a, b) => a + b.size, 0);
    console.log(`  network: ${n} request${n > 1 ? 's' : ''} failed (${[...hosts].map(([h, u]) => `${h} ×${u.size}`).join(', ')})${opt.network ? ' — with --network: that host is unreachable from here' : ' — a widget test answers every request with HTTP 400: images from the web show the app\'s placeholder or error widget, and data from an API does not arrive; --network lets them load where the machine can reach the host'}`);
  }
}
{
  const counts = new Map();
  for (const e of rep.errors || []) {
    if (/overflowed by/.test(e.summary) || netErr(e)) continue;
    const k = `${e.summary.slice(0, 140)}${e.where ? ` — ${whereStr(e.where)}` : ''}`;
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  if (counts.size) console.log(`  errors (${[...counts.values()].reduce((a, b) => a + b, 0)}): ${[...counts].slice(0, 4).map(([k, n]) => `${k}${n > 1 ? ` ×${n}` : ''}`).join(' · ')}${counts.size > 4 ? ` · … ${counts.size - 4} more in report.json` : ''}`);
  const channels = [...new Set([...counts.keys()].map((k) => (/MissingPluginException\(No implementation found for method \S+ on channel (\S+?)\)/.exec(k) || [])[1]).filter(Boolean))];
  if (channels.length) console.log(`  plugins with no platform in a test: ${channels.join(', ')} — answer them in a --setup file (TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(const MethodChannel('<channel>'), (call) async => null)), or pump a screen that does not call them`);
}
if (gf.failed.length) console.log(`  google_fonts: ${gf.failed.join(', ')} could not be fetched (offline?): that text is drawn in a fallback face`);
if (fontFetchErrors) console.log(`  google_fonts tried the network ${fontFetchErrors}× for a face not fetched here (a weight the scan missed): that text may be drawn in its fallback`);

// Findings across passes, each once with the passes it shows in.
{
  // One line per widget in the code (a Text used for seven cards is one finding, with its texts).
  const groups = new Map();
  const add = (kind, key, text, p, sample) => {
    const k = `${kind}|${key}`;
    if (!groups.has(k)) groups.set(k, { kind, text, at: new Set(), samples: new Set() });
    const g = groups.get(k);
    g.at.add(label(p));
    if (sample) g.samples.add(sample);
  };
  for (const p of counted) {
    const f = p.findings;
    for (const c of f.contrast) add('contrast', `${c.where ? whereStr(c.where) : c.text}|${c.fg}|${c.bg}`, `${c.ratio}:1 (needs ${c.need})${c.fg ? ` ${c.fg} on ${c.bg}` : ''}${c.size ? `, ${c.size}px${c.bold ? ' bold' : ''}` : ''}${c.where ? ` — ${whereStr(c.where)}` : ''}${c.source === 'guideline' ? " (Flutter's guideline)" : ''}`, p, JSON.stringify((c.text || '').replace(/\s*\n\s*/g, ' · ').slice(0, 40)));
    for (const c of f.iconContrast) add('icon', `${c.where ? whereStr(c.where) : c.rect}|${c.fg}|${c.bg}`, `${c.ratio}:1 (needs 3) ${c.fg} on ${c.bg}, ${Math.round(c.rect[2])}×${Math.round(c.rect[3])} at ${Math.round(c.rect[0])},${Math.round(c.rect[1])}${c.where ? ` — ${whereStr(c.where)}` : ''}`, p);
    for (const t of [...f.below24, ...f.below48]) add('target', `${t.where ? whereStr(t.where) : t.label}|${t.size}`, `${t.size.map((v) => Math.round(v)).join('×')} ${t.role || 'tappable'}${t.label || t.tooltip ? ` ${JSON.stringify((t.label || t.tooltip).slice(0, 40))}` : ''}${Math.min(...t.size) < 24 ? ' (below 24: WCAG 2.2)' : Math.min(...t.size) < 44 ? ' (below 44pt and 48dp)' : ' (below 48dp)'}${t.where ? ` — ${whereStr(t.where)}` : ''}`, p);
    for (const u of f.unlabeled) add('unlabeled', `${u.where ? whereStr(u.where) : u.rect}`, `${u.rect ? `${Math.round(u.rect[2])}×${Math.round(u.rect[3])} ` : ''}${u.role || 'tappable'} with no label${u.where ? ` — ${whereStr(u.where)}` : ''}`, p);
    for (const o of f.overflow) {
      const m = /overflowed by ([\d.]+) pixels on the (\w+)/.exec(o.summary);
      add('overflow', o.where ? whereStr(o.where) : o.summary, m ? `on the ${m[2]}${o.where ? ` — ${whereStr(o.where)}` : ''}` : `${o.summary}${o.where ? ` — ${whereStr(o.where)}` : ''}`, p, m ? `${Math.round(Number(m[1]) * 10) / 10} px` : null);
    }
  }
  const all = [...groups.values()];
  if (all.length) {
    const order = ['overflow', 'contrast', 'icon', 'unlabeled', 'target'];
    all.sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind) || b.at.size - a.at.size);
    const everywhere = counted.map(label);
    console.log('  findings:');
    for (const g of all.slice(0, 16)) {
      const sm = [...g.samples];
      const what = g.kind === 'overflow'
        ? (sm.length ? `by ${sm.map((x) => parseFloat(x)).sort((a, b) => a - b).filter((v, i, a) => i === 0 || i === a.length - 1).join('–')} px ` : '')
        : sm.length ? `${sm.slice(0, 3).join(', ')}${sm.length > 3 ? ` +${sm.length - 3}` : ''} ` : '';
      console.log(`    ${g.kind}: ${what}${g.text} · ${g.at.size === everywhere.length ? 'every pass' : `at ${[...g.at].join(', ')}`}`);
    }
    if (all.length > 16) console.log(`    … ${all.length - 16} more in report.json`);
  }
}
if (compare) {
  const fs_ = Object.entries(compare.files);
  const changed = fs_.filter(([, f]) => f.status === 'changed');
  console.log(`  compare vs ${rel(compare.baseline)}: ${compare.error || `${fs_.length - changed.length} identical, ${changed.length} changed${changed.length ? ` — ${changed.map(([n, f]) => `${n.replace('.png', '')} ${f.pct}%${f.y ? ` (y ${f.y[0]}–${f.y[1]})` : ''}`).join(', ')}` : ''}`}`);
}

// ---- the Verified block: the numbers the report to the user is made of. Paste it; don't recompute.
{
  const L = [];
  const errScreen = passes.find((p) => p.errorScreen);
  if (errScreen) L.push(`- Rendered: an error screen (${errScreen.errorWidget ? "Flutter's error box" : JSON.stringify(errScreen.errorScreen.slice(0, 60))}), not the app's UI — the numbers below are for it`);
  const worst = (list, fn) => list.reduce((m, p) => { const n = fn(p); return n > m.n ? { n, at: label(p) } : m; }, { n: 0, at: null });
  const at = (m, list) => (m.n && list.length > 1 ? ` (worst at ${m.at})` : '');
  const widest = light.reduce((a, b) => (a && a.width > b.width ? a : b), null) || passes[0];
  const cw = worst(light, (p) => p.findings.contrast.length), iw = worst(light, (p) => p.findings.iconContrast.length), gw = worst(light, (p) => p.findings.guideline.length);
  const wt = widest.text || {};
  L.push(`- Contrast: ${wt.checked ?? '?'} runs of text (every visible Text and field, in a merged label or not), ${cw.n} below threshold${at(cw, light)}${wt.disabled ? ` · ${wt.disabled} in disabled controls, exempt` : ''}${wt.unverifiable ? ` · ${wt.unverifiable} on an image or gradient, unverifiable` : ''} · ${wt.icons ?? 0} icons, ${iw.n} below 3:1${at(iw, light)} · Flutter's textContrastGuideline: ${gw.n}${gw.n > cw.n ? ' (it reads anti-aliased edges and dividers as the text colour; the per-text numbers are the ones to use)' : ''}`);
  if (darkPasses.length && !darkUnchanged) {
    const dw = worst(darkPasses, (p) => p.findings.contrast.length), diw = worst(darkPasses, (p) => p.findings.iconContrast.length);
    const dwid = darkPasses.find((p) => p.width === widest.width) || darkPasses[0];
    L.push(`- Dark mode: rendered (dark platform brightness${opt.darkFirst ? ', from start' : ''}) · ${dw.n} runs of text below threshold${at(dw, darkPasses)} · ${diw.n} icons below 3:1 · background ${widest.background} → ${dwid.background}`);
  } else if (darkPasses.length) {
    L.push(`- Dark mode: tried under a dark platform brightness: the screen did not change — no dark theme${opt.darkFirst ? '' : ' (or one read only at start: --dark-first)'}`);
  } else L.push('- Dark mode: not rendered (--no-dark)');
  const t24 = worst(counted, (p) => p.findings.below24.length), t48 = worst(counted, (p) => p.findings.below48.length), t44 = worst(counted, (p) => p.findings.below44);
  L.push(`- Targets: ${widest.tappable} tappable · ${t24.n} below 24${at(t24, counted)} · ${t44.n} below 44pt (iOS) · ${t24.n + t48.n} below 48dp (Android)${at(t48, counted)}`);
  const ul = worst(counted, (p) => p.findings.unlabeled.length);
  L.push(`- Names: ${ul.n} tappable without a label${at(ul, counted)} · ${(widest.headers || []).length} headers${(widest.headers || []).length ? ` (${widest.headers.slice(0, 3).map((h) => JSON.stringify(h)).join(', ')})` : ''}`);
  const ov = light.filter((p) => p.findings.overflow.length).map((p) => `${p.width} (${p.findings.overflow.length})`);
  L.push(`- Overflow: ${ov.length ? `at ${ov.join(', ')}` : `none at ${light.map((p) => p.width).join(' / ')}`}`);
  if (scaled.length) {
    const s = scaled[0];
    L.push(`- Text at ${Math.round(s.textScale * 100)} % (${s.width}): ${s.findings.overflow.length ? `${s.findings.overflow.length} overflow${s.findings.overflow.length > 1 ? 's' : ''} (${[...new Set(s.findings.overflow.map((o) => whereStr(o.where) || o.summary))].slice(0, 3).join(', ')})` : 'no overflow'}`);
  }
  const fonts = (rep.fonts || []).filter((f) => !/^(Roboto)$/.test(f));
  L.push(`- Fonts: Roboto and Material Icons from the SDK${fonts.length ? ` · declared: ${fonts.map((f) => f.replace(/^packages\/[^/]+\//, '')).join(', ')}` : ''}${gf.families.length ? ` · google_fonts: ${gf.families.map((f) => f.family).join(', ')} (fetched)` : ''} · Cupertino text is drawn in Roboto (San Francisco exists only on Apple platforms)`);
  const errN = (rep.errors || []).filter((e) => !/overflowed by/.test(e.summary) && !netErr(e)).length;
  const netN = (rep.errors || []).filter(netErr).length;
  L.push(`- Errors: ${errN ? `${errN} during the render (see errors above)` : 'none during the render'}${netN ? ` · ${netN} failed requests (${opt.network ? 'unreachable hosts' : 'no network in a widget test'})` : ''}${rep.crash ? ` · stopped during ${rep.crash.phase}` : ''}`);
  if (compare && !compare.error) {
    const changed = Object.entries(compare.files).filter(([, f]) => f.status === 'changed');
    L.push(`- Compared with ${rel(compare.baseline)}: ${changed.length ? changed.map(([n, f]) => `${n.replace('.png', '')} ${f.pct}% changed`).join(' · ') : `all ${Object.keys(compare.files).length} screenshots identical`}`);
  }
  console.log(`\nVerified (flutter_render.mjs · ${rel(out)}):\n${L.join('\n')}`);
}
console.log(`  full report: ${rel(join(out, 'report.json'))} · test log: ${rel(join(out, 'flutter-test.log'))} · took ${Math.round((Date.now() - tStart) / 1000)} s`);
process.exit(0);
