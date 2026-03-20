#!/usr/bin/env bash
# install.sh — Idempotent environment setup for Jobbing
# Usage: bash scripts/install.sh
# Safe to re-run; skips steps already done.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
info() { echo -e "  $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }

echo ""
echo "Jobbing — environment setup"
echo "==========================="
echo ""

# ── Step 1: Homebrew ─────────────────────────────────────────────────────────

if ! command -v brew &>/dev/null; then
    warn "Homebrew not found. Install it first: https://brew.sh"
    warn "Skipping Obsidian installation (requires brew)."
    SKIP_OBSIDIAN=1
else
    ok "Homebrew found"
    SKIP_OBSIDIAN=0
fi

# ── Step 2: Obsidian ─────────────────────────────────────────────────────────

if [[ "${SKIP_OBSIDIAN:-0}" == "0" ]]; then
    if brew list --cask obsidian &>/dev/null 2>&1; then
        ok "Obsidian already installed"
    else
        echo "Installing Obsidian..."
        brew install --cask obsidian
        ok "Obsidian installed"
    fi
fi

# ── Step 3: Python venv ───────────────────────────────────────────────────────

if [[ -d ".venv" ]]; then
    ok "Python venv already exists (.venv/)"
else
    echo "Creating Python venv..."
    python3 -m venv .venv
    ok "Python venv created"
fi

echo "Installing/updating Python package..."
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e ".[dev]"
ok "Python package installed (jobbing CLI available at .venv/bin/jobbing)"

# ── Step 4: Things theme ─────────────────────────────────────────────────────

THINGS_DIR=".obsidian/themes/Things"
THINGS_RAW="https://raw.githubusercontent.com/colineckert/obsidian-things/main"

mkdir -p "$THINGS_DIR"

if [[ -f "$THINGS_DIR/theme.css" ]]; then
    ok "Things theme already present"
else
    echo "Downloading Things theme..."
    if curl -fsSL "$THINGS_RAW/theme.css" -o "$THINGS_DIR/theme.css" && \
       curl -fsSL "$THINGS_RAW/manifest.json" -o "$THINGS_DIR/manifest.json"; then
        ok "Things theme downloaded"
    else
        warn "Could not download Things theme (network issue?). Skipping."
        warn "Manual install: open Obsidian → Settings → Appearance → Community themes → search 'Things'"
    fi
fi

# ── Step 5: Kanban plugin ─────────────────────────────────────────────────────

KANBAN_DIR=".obsidian/plugins/obsidian-kanban"
KANBAN_BASE="https://github.com/mgmeyers/obsidian-kanban/releases/latest/download"

mkdir -p "$KANBAN_DIR"

if [[ -f "$KANBAN_DIR/main.js" ]]; then
    ok "Kanban plugin already present"
else
    echo "Downloading Kanban plugin..."
    if curl -fsSL "$KANBAN_BASE/main.js" -o "$KANBAN_DIR/main.js" && \
       curl -fsSL "$KANBAN_BASE/manifest.json" -o "$KANBAN_DIR/manifest.json" && \
       curl -fsSL "$KANBAN_BASE/styles.css" -o "$KANBAN_DIR/styles.css"; then
        ok "Kanban plugin downloaded"
    else
        warn "Could not download Kanban plugin. It may already be installed if you opened Obsidian before."
    fi
fi

# ── Step 6: Style Settings plugin ────────────────────────────────────────────

STYLE_DIR=".obsidian/plugins/obsidian-style-settings"
STYLE_BASE="https://github.com/mgmeyers/obsidian-style-settings/releases/latest/download"

mkdir -p "$STYLE_DIR"

if [[ -f "$STYLE_DIR/main.js" ]]; then
    ok "Style Settings plugin already present"
else
    echo "Downloading Style Settings plugin..."
    if curl -fsSL "$STYLE_BASE/main.js" -o "$STYLE_DIR/main.js" && \
       curl -fsSL "$STYLE_BASE/manifest.json" -o "$STYLE_DIR/manifest.json" && \
       curl -fsSL "$STYLE_BASE/styles.css" -o "$STYLE_DIR/styles.css" 2>/dev/null; then
        ok "Style Settings plugin downloaded"
    else
        warn "Could not download Style Settings plugin (optional — used for theme customisation)."
    fi
fi

# ── Step 7: .obsidian/app.json ───────────────────────────────────────────────

APP_JSON=".obsidian/app.json"

# Only write if theme isn't already set to Things
if grep -q '"cssTheme": "Things"' "$APP_JSON" 2>/dev/null; then
    ok "app.json already configured for Things theme"
else
    echo "Writing .obsidian/app.json (Things theme + appearance)..."
    cat > "$APP_JSON" <<'APPJSON'
{
  "promptDelete": false,
  "cssTheme": "Things",
  "baseFontSize": 16,
  "interfaceFontFamily": "",
  "textFontFamily": "",
  "monospaceFontFamily": "",
  "readableLineLength": true,
  "maxWidth": "720px",
  "showInlineTitle": true,
  "showViewHeader": true,
  "pdfExportSettings": {
    "pageSize": "Letter",
    "landscape": false,
    "margin": "0",
    "downscalePercent": 100
  }
}
APPJSON
    ok "app.json written"
fi

# ── Step 8: .obsidian/community-plugins.json ─────────────────────────────────

PLUGINS_JSON=".obsidian/community-plugins.json"

if grep -q "obsidian-style-settings" "$PLUGINS_JSON" 2>/dev/null; then
    ok "community-plugins.json already includes style-settings"
else
    echo "Writing .obsidian/community-plugins.json..."
    cat > "$PLUGINS_JSON" <<'PLUGINSJSON'
["obsidian-kanban", "obsidian-style-settings"]
PLUGINSJSON
    ok "community-plugins.json written"
fi

# ── Step 9: .env check ───────────────────────────────────────────────────────

echo ""
echo "Checking environment..."

if [[ -f ".env" ]]; then
    if grep -q "NOTION_API_KEY" .env 2>/dev/null; then
        ok ".env has NOTION_API_KEY (needed for one-time interview migration)"
    else
        warn ".env exists but NOTION_API_KEY not set"
        info "Add it if you need to run: python kanban/sync_notion_to_obsidian.py --include-interviews"
    fi
else
    warn ".env not found"
    info "If running the interview migration, create .env with:"
    info "  NOTION_API_KEY=secret_..."
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════"
echo " Setup complete. Next steps:"
echo "═══════════════════════════════════════════════"
echo ""
echo "1. Open Obsidian and open this folder as a vault:"
echo "   $REPO_ROOT"
echo ""
echo "2. In Obsidian: Settings → Community Plugins → enable if prompted"
echo "   (Kanban and Style Settings should be pre-enabled)"
echo ""
echo "3. Apply Things theme:"
echo "   Settings → Appearance → select 'Things'"
echo ""
echo "4. Open the kanban board:"
echo "   Navigate to kanban/Job Tracker.md"
echo ""
echo "5. (One-time) Migrate interview notes from Notion:"
echo "   python kanban/sync_notion_to_obsidian.py --include-interviews --dry-run"
echo "   python kanban/sync_notion_to_obsidian.py --include-interviews"
echo ""
echo "6. Activate the Python CLI:"
echo "   source .venv/bin/activate"
echo "   jobbing --help"
echo ""
