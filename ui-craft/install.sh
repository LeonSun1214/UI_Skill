#!/usr/bin/env bash
# ui-craft installer — copies the skill where Claude Code looks for skills and sets up the
# render loop. Run from anywhere:
#   bash install.sh            → ~/.claude/skills/ui-craft   (all projects)
#   bash install.sh --project  → ./.claude/skills/ui-craft   (this project only)
#   bash install.sh --link     → symlink instead of copy (develop the skill in place)
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills/ui-craft"
MODE="copy"
for a in "$@"; do
  case "$a" in
    --project) DEST="$(pwd)/.claude/skills/ui-craft" ;;
    --link) MODE="link" ;;
    -h|--help) sed -n 2,7p "$0"; exit 0 ;;
  esac
done

command -v node >/dev/null || { echo "node is required (18+): https://nodejs.org"; exit 1; }
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 18 ] || { echo "node $(node -v) is too old; need 18+"; exit 1; }
command -v python3 >/dev/null || echo "warning: python3 not found — inspect.py and contrast.py will not run"

mkdir -p "$(dirname "$DEST")"
if [ "$MODE" = "link" ]; then
  rm -rf "$DEST"; ln -s "$SRC" "$DEST"; echo "linked $DEST → $SRC"
else
  rm -rf "$DEST"; mkdir -p "$DEST"
  # the skill itself: SKILL.md, scripts, references (the evals benchmark stays in the repo)
  tar -C "$SRC" --exclude=node_modules --exclude=.ui-craft --exclude=__pycache__ --exclude=evals -cf - . | tar -C "$DEST" -xf -
  echo "copied to $DEST"
fi

echo "installing playwright…"
(cd "$DEST/scripts" && npm install --no-audit --no-fund --loglevel=error)
if ! (cd "$DEST/scripts" && node -e "import('./lib/browser.mjs').then(async (m) => { const pw = await import('playwright'); const { browser, via } = await m.launchChromium(pw); await browser.close(); console.log('chromium: ' + via); })" 2>/dev/null); then
  echo "no usable Chromium found — downloading the bundled one (~150 MB)…"
  (cd "$DEST/scripts" && npx playwright install chromium)
fi
echo
echo "installed ui-craft $(sed -n 's/^  version: //p' "$DEST/SKILL.md" | head -1) at $DEST"
(cd "$DEST/scripts" && node doctor.mjs) || true
echo
echo "done. In Claude Code, the skill loads automatically; say e.g. \"帮我做一个落地页\" or \"check the mobile view\"."
