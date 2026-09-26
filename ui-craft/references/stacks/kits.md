# Component kits and CSS-in-JS: MUI, Ant Design, Chakra, styled-components, CSS Modules, Element Plus, Vuetify

Read when `inspect.py` names one of these kits. In these projects the look is not in utility classes. It is in a theme object and the kit's components, so a match task builds with those. Each section says where the theme is, how dark mode switches, and which of the kit's defaults the render will flag, with the one-line fix. The render measures what the page shows; a default that fails is the kit's, and the project inherits it.

## MUI (Material UI)

- The theme is `createTheme({...})` (or `extendTheme`), often split across `src/theme/`: `palette` (`primary.main` …), `shape.borderRadius`, `typography.fontFamily`, and `components` (`MuiButton: { styleOverrides }`). The inspector prints the palette, the radius, the fonts and the overridden components. Build with the kit's components (`Box`, `Card`, `Typography`, `Button`) and the theme's values: `color="primary"`, `sx={{ color: 'text.secondary', borderRadius: 1 }}` (one unit is `shape.borderRadius`), never a hex or a pixel radius.
- Styling is `sx` or `styled()`; the inspector counts both. A project that uses `sx` everywhere expects `sx` in a new component.
- Dark mode: `colorSchemes: { light, dark }` with `cssVariables` switches through CSS variables under `colorSchemeSelector` (`class` is `.dark` on `<html>`, `data` is `[data-dark]`, a custom attribute is `[data-…=dark]`). `useColorScheme()` keeps the choice in localStorage `mui-mode`: render dark with `--dark-storage mui-mode=dark`. A theme with only a `light` scheme has no dark mode, whatever its selector says.
- Focus: MUI shows keyboard focus as a ripple, a circle of `currentColor` at 30% that pulses inside the button. On a text or icon button that measures about 1.5–1.9:1, and the render reports it as a faint ring (`ripple inside it`). Fix it once in the theme: `MuiButtonBase: { styleOverrides: { root: ({ theme }) => ({ '&.Mui-focusVisible': { outline: \`2px solid ${theme.palette.primary.main}\`, outlineOffset: 2 } }) } }`.
- Minimal-style templates use `grey[500]` (`#919EAB`, 2.73:1 on white) for captions: `text.secondary` or `grey[600]` (`#637381`, 4.88:1) passes.
- Fonts from `@fontsource/*` are bundled: they load with no network.

## Ant Design and Ant Design Pro

- The theme is `ConfigProvider theme={{ token, components, algorithm }}`; in umi (Ant Design Pro) it is `antd.configProvider.theme` in `config/config.ts`, with the layout's `colorPrimary`, `navTheme` and `layout` in `config/defaultSettings.ts`. Read tokens in code with `theme.useToken()`; never hard-code a colour a token names.
- Pro pages start from `PageContainer`, with `ProTable`, `ProForm` and `ModalForm` for the usual shapes. A new page is a folder in `src/pages/` plus an entry in `config/routes.ts` (`access` guards it, `layout: false` takes it out of ProLayout).
- Serving: `npm start` (`max dev`) listens on :8000 and answers `/api` from `mock/`; `dev` sets `MOCK=none` and needs the backend in `config/proxy.ts`. The mock sign-in is in `mock/user.ts` (`admin` / `ant.design`); its session lives in the mock server, so `--save-state` writes an empty file and the pages after sign-in render without it while `max dev` runs. The sign-in button is not `type=submit`: click `button.ant-btn-primary`.
- Dark mode: `algorithm: theme.darkAlgorithm`, chosen in JS. The render cannot switch it from outside: render dark through the app's own toggle, or not at all.
- Defaults the render flags: the focus outline is `colorPrimaryBorder` (`#91caff`, 1.74:1 on white): set `token.colorPrimaryBorder` to `#1677ff` (4.10:1). Secondary text is `rgba(0,0,0,.45)` (3.36:1): `token.colorTextSecondary: 'rgba(0,0,0,.65)'` (7.0:1). White on the default primary `#1677ff` is 4.10:1: a darker primary (`#0958d9`, 6.16:1) passes for text.

## Chakra UI

- v2: `extendTheme({ colors, fonts, components, config })`, often merged from several files (`src/theme/`). The inspector prints each colour scale by its 500 step, the fonts and the component styles. Build with `colorScheme="brand"`, `color="brand.500"`, not hex values.
- v2 dark mode: `useColorModeValue(light, dark)` in the components, the choice in localStorage `chakra-ui-color-mode`, shown as `data-theme` on `<html>` and `.chakra-ui-dark` on `<body>`. Render dark with `--dark-storage chakra-ui-color-mode=dark`. A new component takes both values from `useColorModeValue`.
- v3: `createSystem(defaultConfig, defineConfig({ theme: { tokens } }))` and `next-themes` for the mode (the inspector's theme line names its key).
- Focus is the `outline` shadow token. A theme that sets `_focus: { boxShadow: 'none' }` (Horizon UI does, on every Button) leaves none, and the render lists those buttons as focus invisible: restore a `_focusVisible` ring instead of removing `_focus`.

## styled-components and Emotion

- The theme is an object passed to `<ThemeProvider theme={…}>`; the inspector names the file with its colours and the theme keys the components read most (`theme.accent`, `theme.text`). A new component is a styled component that reads those keys: `color: ${({ theme }) => theme.textSecondary}`.
- Global styles are in `createGlobalStyle` (or Emotion's `<Global>`); the inspector names the file.
- Dark mode is a second theme object (`darkTheme`, `buildDarkTheme`) picked at runtime, usually from a stored choice: the inspector's theme line names the key, and `--dark-storage KEY=dark` renders it.
- Emotion inside MUI or Chakra is the kit's engine, not the project's styling; the inspector leaves it out.

## CSS Modules

- Each component imports its own `X.module.css`; the class names are local to it and hashed in the page (`_card_1x2y3`). A new component gets its own module next to it, and takes colours and spacing from the global variables (`:root` in the global stylesheet), not literals.
- A selector in the render's findings with a hashed class points at the module next to the component with that class name.

## Element Plus

- The default theme is `element-plus/dist/index.css`: primary `#409eff`. Projects change it with `--el-color-primary` in `:root`, a SCSS `@forward 'element-plus/theme-chalk/src/common/var.scss' with ($colors: …)`, or at runtime from a theme picker (`setProperty('--el-color-primary', …)`, kept in localStorage). The inspector names the runtime file: a colour change goes there too.
- Build with `<el-button type="primary">`, `el-form` / `el-form-item`, `el-table`, `el-dialog`. The locale (`zh-cn`) is set in `app.use(ElementPlus, { locale })`: new copy is in that language.
- Dark mode: `import 'element-plus/theme-chalk/dark/css-vars.css'` and `.dark` on `<html>`, usually set by VueUse's `useDark()`, which keeps the choice in localStorage `vueuse-color-scheme`: `--dark-storage vueuse-color-scheme=dark`. A page with hard-coded white (a sign-in page with its own background) stays light; the render says the dark pass left it unchanged.
- Defaults the render flags: white on `#409eff` is 2.78:1, and so are `el-link` text and the input's focus ring (a 1px inset shadow in the primary). `--el-color-primary: #2b6cb0` (5.42:1) fixes all three. The theme's generated `light-3 … light-9` steps do not follow a runtime override; set them with it, or rebuild the SCSS.
- Admin templates (RuoYi, vue-element-admin) add most routes at runtime from a menu the backend sends: the inspector says so. Without the backend only the static routes (the sign-in page) render.

## Vuetify

- The theme is `createVuetify({ theme: { defaultTheme, themes: { name: { dark, colors } } }, defaults })`. The inspector prints each theme's colours and the component defaults (`VCard: { rounded: 'md' }`, `VTextField: { variant: 'outlined' }`): those apply to every instance, so a new component inherits them without repeating them.
- Build with `color="primary"`, `bg-surface`, `text-medium-emphasis`, not hex values.
- Dark mode: a theme with `dark: true`, switched with `theme.global.name.value = 'dark'` (or `theme.change('dark')`), often stored by the app (the inspector names the key: `--dark-storage KEY=dark`). Vuetify writes variables for its built-in `dark` theme even when the app never uses it; a dark class on `<html>` then changes nothing, because the app root carries its own theme class, and the render says the dark pass moved nothing instead of reporting its findings twice.
- Focus: buttons and list items show focus by raising an overlay element to 12% (`.v-btn__overlay`): about 1.2–1.3:1, reported as a faint tint. Add a ring: `.v-btn:focus-visible, .v-list-item:focus-visible { outline: 2px solid rgb(var(--v-theme-primary)); outline-offset: 2px; }`.
- A temporary navigation drawer that opens over the page at 375 covers the header; the render reports focus obscured "behind nav.v-navigation-drawer".

## All of them

- The first render of a Vite dev server can time out while Vite optimises dependencies and reloads the page; the render retries once and says so. A Create React App project on React 19 may need `npm install ajv@8` before `react-scripts start` runs.
- Check with the project's own tools after the last render: `tsc --noEmit`, `vue-tsc`, the linter.
