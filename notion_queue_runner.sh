#!/bin/bash
# notion_queue_runner.sh — Called by launchd when files appear in notion_queue/
# Processes all queued Notion API operations and moves them to notion_queue_results/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$SCRIPT_DIR/notion_queue_results/runner.log"

mkdir -p "$SCRIPT_DIR/notion_queue_results"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Queue runner triggered" >> "$LOG"

# Small delay to let file writes finish (Cowork may still be writing)
sleep 1

cd "$SCRIPT_DIR" && python3 notion_update.py run-queue >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — Queue runner finished" >> "$LOG"
echo "---" >> "$LOG"
