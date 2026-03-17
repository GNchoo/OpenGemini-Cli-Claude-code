#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARED_DIR="$ROOT/shared-session"
CONTEXT_FILE="$SHARED_DIR/CONTEXT.md"
TODO_FILE="$SHARED_DIR/TODO.md"
LAST_FILE="$SHARED_DIR/LAST_RESULT.md"
LOG_FILE="$SHARED_DIR/SESSION_LOG.md"

mkdir -p "$SHARED_DIR"

if ! command -v gemini >/dev/null 2>&1; then
  echo "gemini CLI not found in PATH" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: $(basename "$0") \"your request\"" >&2
  exit 1
fi

USER_PROMPT="$*"
TS="$(date '+%Y-%m-%d %H:%M:%S %z')"
TMP_OUT="$(mktemp)"

read -r -d '' COMPOSITE_PROMPT <<EOF || true
You are one engine in a shared dual-engine workflow.

Shared memory files (read first, then update when needed):
- $CONTEXT_FILE
- $TODO_FILE
- $LAST_FILE
- $LOG_FILE

Rules:
1) Treat those files as source of truth for continuity.
2) Keep edits minimal and concrete.
3) At the end, update $LAST_FILE with: timestamp, engine(gemini), what changed, next steps.
4) If tasks changed, update $TODO_FILE checkboxes.
5) Append one brief run note to $LOG_FILE.

User request:
$USER_PROMPT
EOF

(
  cd "$ROOT"
  gemini -p "$COMPOSITE_PROMPT"
) | tee "$TMP_OUT"

OUTPUT="$(cat "$TMP_OUT")"
rm -f "$TMP_OUT"

{
  echo ""
  echo "## $TS | gemini"
  echo "$OUTPUT"
} >> "$LOG_FILE"

# Fallback update in case engine didn't touch LAST_RESULT.md
if ! grep -q "$TS" "$LAST_FILE" 2>/dev/null; then
  {
    echo "# Last Result"
    echo ""
    echo "- timestamp: $TS"
    echo "- engine: gemini"
    echo "- request: $USER_PROMPT"
    echo ""
    echo "## Output (raw)"
    echo "$OUTPUT"
  } > "$LAST_FILE"
fi
