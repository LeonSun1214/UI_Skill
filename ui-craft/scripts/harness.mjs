#!/usr/bin/env node
/**
 * ui-craft harness — render one component in isolation (Vite + React projects).
 *
 *   node harness.mjs <project-root> --component src/components/ui/Button.tsx [--export Button]
 *                    [--states '[{"children":"Save"},{"variant":"secondary","children":"Cancel"},{"disabled":true,"children":"Off"}]']
 *                    [--css src/index.css] [--wrap "p-8"] [--out .ui-craft/harness]
 *
 * Writes <project>/.ui-craft/harness/index.html + harness.tsx, a page that mounts the component
 * once per state with the project's own CSS, and prints the dev-server URL to render:
 *   node render.mjs http://localhost:5173/.ui-craft/harness/index.html --out .ui-craft/button-1
 * Vite serves any HTML under the project root, so no config changes are needed. Delete the
 * folder when done (.ui-craft/ should be git-ignored anyway).
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, relative, resolve } from 'node:path';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help') || argv.includes('-h')) {
  console.log('usage: node harness.mjs <project-root> --component <file.tsx> [--export Name] [--states JSON] [--css file] [--wrap classes] [--out dir]');
  process.exit(argv.length ? 0 : 1);
}
const opt = { project: null, component: null, exportName: null, states: null, css: null, wrap: 'p-8', out: '.ui-craft/harness' };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--component') opt.component = argv[++i];
  else if (a === '--export') opt.exportName = argv[++i];
  else if (a === '--states') opt.states = argv[++i];
  else if (a === '--css') opt.css = argv[++i];
  else if (a === '--wrap') opt.wrap = argv[++i];
  else if (a === '--out') opt.out = argv[++i];
  else opt.project = a;
}
if (!opt.project || !opt.component) { console.error('need <project-root> and --component'); process.exit(1); }
const project = resolve(opt.project);
const compPath = resolve(project, opt.component);
if (!existsSync(compPath)) { console.error(`component not found: ${compPath}`); process.exit(1); }

// export name: --export, else the first `export function X` / `export const X` / default
const src = readFileSync(compPath, 'utf8');
let exportName = opt.exportName;
let isDefault = false;
if (!exportName) {
  const m = /export\s+(?:function|const|class)\s+([A-Z]\w*)/.exec(src);
  if (m) exportName = m[1];
  else if (/export\s+default/.test(src)) { isDefault = true; exportName = basename(compPath).replace(/\.\w+$/, '').replace(/[^\w]/g, '') || 'Component'; }
  else { console.error('no export found; pass --export Name'); process.exit(1); }
} else if (exportName === 'default') { isDefault = true; exportName = basename(compPath).replace(/\.\w+$/, '').replace(/[^\w]/g, ''); }

// css: --css, else the first .css imported by src/main.tsx | src/index.tsx | app entry
let css = opt.css;
if (!css) {
  for (const entry of ['src/main.tsx', 'src/main.jsx', 'src/index.tsx', 'src/index.jsx', 'src/App.tsx']) {
    const ep = join(project, entry);
    if (!existsSync(ep)) continue;
    const m = /import\s+["']([^"']+\.css)["']/.exec(readFileSync(ep, 'utf8'));
    if (m) { css = join(dirname(entry), m[1]); break; }
  }
}
let states = [{}];
if (opt.states) {
  try { states = JSON.parse(opt.states); if (!Array.isArray(states)) states = [states]; }
  catch (e) { console.error(`--states is not valid JSON: ${e.message}`); process.exit(1); }
}

const outDir = join(project, opt.out);
mkdirSync(outDir, { recursive: true });
const rel = (p) => { let r = relative(outDir, resolve(project, p)).replace(/\\/g, '/'); if (!r.startsWith('.')) r = './' + r; return r; };
const importLine = isDefault ? `import ${exportName} from '${rel(opt.component).replace(/\.(tsx|jsx|ts|js)$/, '')}';`
  : `import { ${exportName} } from '${rel(opt.component).replace(/\.(tsx|jsx|ts|js)$/, '')}';`;
const cssLine = css && existsSync(resolve(project, css)) ? `import '${rel(css)}';` : '';
const tsx = `${cssLine}
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
${importLine}

const states: Record<string, unknown>[] = ${JSON.stringify(states, null, 2)};

function Harness() {
  return (
    <main className="${opt.wrap}">
      <h1 style={{ font: '600 14px/1.4 system-ui, sans-serif', color: '#222', margin: '0 0 16px' }}>${exportName} · ${states.length} state${states.length === 1 ? '' : 's'}</h1>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 24, alignItems: 'flex-start' }}>
        {states.map((props, i) => (
          <section key={i} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <p style={{ font: '12px/1.4 ui-monospace, monospace', color: '#444', margin: 0, maxWidth: 320, wordBreak: 'break-all' }}>{JSON.stringify(props)}</p>
            <div><${exportName} {...(props as any)} /></div>
          </section>
        ))}
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<StrictMode><Harness /></StrictMode>);
`;
const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${exportName} harness</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./harness.tsx"></script>
  </body>
</html>
`;
writeFileSync(join(outDir, 'harness.tsx'), tsx);
writeFileSync(join(outDir, 'index.html'), html);
const urlPath = `/${relative(project, outDir).replace(/\\/g, '/')}/index.html`;
console.log(`harness written: ${join(outDir, 'index.html')}`);
console.log(`  component: ${exportName} from ${opt.component}${css ? ` · css: ${css}` : ' · css: none found (pass --css)'} · ${states.length} state(s)`);
console.log(`  render:    node <skill-dir>/scripts/render.mjs http://localhost:<port>${urlPath} --out .ui-craft/${exportName.toLowerCase()}-1`);
