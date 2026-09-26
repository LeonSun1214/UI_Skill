# Static sites: hand-written HTML, Eleventy, Jekyll, Hugo

Read when `inspect.py` says the stack is static HTML, Eleventy, Jekyll or Hugo. What differs from a framework project, and what to do about it.

## Hand-written HTML

- Every `.html` file under the site's folder is a page, and its route is its path (`index.html` is `/`, `blog/index.html` is `/blog/`). The inspector lists them with their titles and signals, measured on the page less its shared chrome: a search form in the header is not a form on every page.
- Without templates, the header, nav, sidebar, footer and shared modals are copies. The inspector names each block, how many pages hold it, and how many copies are identical once the current item (`active`, `aria-current`) is set aside. A change to the nav is therefore an edit to every one of those files. Make the same edit in each copy, or move the block into an include if the site gets a build step; never change one copy only.
- The kit is whatever the pages load: a `<link>` to a CDN (Bootstrap, Tailwind's prebuilt CSS or Play CDN, Bulma, Pico), or a copy in `vendor/`. The stack line names it with its version. Build with the kit's classes (`.card`, `.btn-primary`, Tailwind utilities), not new CSS. A site's own stylesheet may be compiled from `scss/` by a gulp or webpack script: edit the source, then run that script, or the change never reaches the CSS the pages link. The source's Sass variables (`$primary`, `$body-color`, the font stack) are listed under *Declared tokens*: a colour change is made there.
- Serving: `python3 -m http.server 8000` in the site's folder, and render `http://localhost:8000/<page>.html`. A `file://` path works too, unless the pages link assets from the root (`/css/…`).

## Assets from a CDN

A kit loaded from unpkg, jsDelivr or cdnjs needs the network. Where that host is blocked, the page renders unstyled, and the render says so on its `did not load` line before any measurement is read. To render it anyway, answer the request from a local copy (`npm pack tailwindcss@2.2.19` puts one in a tarball): `--mock '**/tailwind.min.css=./tailwind.min.css'`, and the same for a script. The page is then measured as its visitors see it.

## Eleventy

- The inspector reads the config (`eleventy.config.js` or `.eleventy.js`: `dir.input`, `includes`, `layouts`, `data`, `output`) and lists each template as a page with its route: its `permalink`, or its path (`blog/post.md` is `/blog/post/`; a file named like its folder is that folder's index).
- A page's layout comes from its front matter, or from a directory data file (`blog/blog.11tydata.js` sets `layout` and `tags` for everything in `blog/`). Layouts chain (`post.njk` sits in `base.njk`), and the page line prints the chain: the chrome is in the last one. Tags make collections (`collections.posts`).
- Site data (`_data/metadata.js`) holds titles, nav entries and URLs: change them there, not in the templates.
- Serving: `npx @11ty/eleventy --serve` builds into `_site/` and serves on :8080; render the built page. CSS is often inlined into a per-page bundle (`{% css %}`, `<style>{% include "css/index.css" %}</style>`): the file named in the layout line is the one to edit.

## Jekyll

- Pages are the `.md` and `.html` files with front matter; `_posts/YYYY-MM-DD-title.md` are posts, routed by `permalink` in `_config.yml` (`/:title/`, `pretty`, `date`). A file without front matter is copied as it is. Layouts are `_layouts/<name>.html`, chained through their own front matter; partials are `{% include x.html %}` from `_includes/`. `_config.yml`'s `defaults` can set a layout for every post.
- Styles: a `.scss` file with front matter (often `style.scss` at the root) is compiled with the partials in `_sass/`.
- Serving: `bundle exec jekyll serve` (with a Gemfile) or `jekyll serve` builds into `_site/` and serves on :4000. On Ruby 3, a site without a Gemfile also needs the `webrick` and `kramdown-parser-gfm` gems, plus the plugins `_config.yml` lists; the inspector prints the whole `gem install` line.

## Hugo

Content in `content/`, templates in `layouts/` (a theme's in `themes/<name>/layouts/`, overridden by the site's own file of the same path), built into `public/`. `hugo server` serves on :1313. The inspector names the folders and does not read the templates.

## Dark mode and checks

Dark mode here is plain CSS (`prefers-color-scheme`, or a class or `data-theme` a script sets), and the render's dark pass handles each; `--dark-storage KEY=dark` renders a stored choice. There is no type-check. Validate the HTML the build writes (`npx html-validate _site/**/*.html`), and check the links.
