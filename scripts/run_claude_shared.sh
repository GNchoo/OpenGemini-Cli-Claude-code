#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARED_DIR="$ROOT/shared-session"
CONTEXT_FILE="$SHARED_DIR/CONTEXT.md"
TODO_FILE="$SHARED_DIR/TODO.md"
LAST_FILE="$SHARED_DIR/LAST_RESULT.md"
LOG_FILE="$SHARED_DIR/SESSION_LOG.md"
LOCK_FILE="$SHARED_DIR/.session.lock"

mkdir -p "$SHARED_DIR"

if ! command -v claude >/dev/null 2>&1; then
  echo "claude CLI not found in PATH" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: $(basename "$0") \"your request\"" >&2
  exit 1
fi

validate_todo_json() {
  python - "$TODO_FILE" <<'PY'
import json,sys
p=sys.argv[1]
with open(p,'r',encoding='utf-8') as f:
    data=json.load(f)
assert isinstance(data,dict), 'root must be object'
assert isinstance(data.get('version'),int), 'version must be int'
assert isinstance(data.get('tasks'),list), 'tasks must be array'
for i,t in enumerate(data['tasks']):
    assert isinstance(t,dict), f'tasks[{i}] must be object'
    for k in ('id','title','status','updated_at'):
        assert k in t, f'tasks[{i}] missing {k}'
print('ok')
PY
}

if ! validate_todo_json >/dev/null 2>&1; then
  echo "Invalid TODO.md JSON format. Fix $TODO_FILE first." >&2
  exit 1
fi

exec 9>"$LOCK_FILE"
if ! flock -w 120 9; then
  echo "Failed to acquire shared-session lock within 120s: $LOCK_FILE" >&2
  exit 1
fi

USER_PROMPT="$*"
TS="$(date '+%Y-%m-%d %H:%M:%S %z')"
TMP_OUT="$(mktemp)"
TODO_BACKUP="$(mktemp)"
cp "$TODO_FILE" "$TODO_BACKUP"

read -r -d '' COMPOSITE_PROMPT <<EOF || true
You are one engine in a shared dual-engine workflow.

Shared memory files (read first, then update when needed):
- $CONTEXT_FILE
- $TODO_FILE (strict JSON only)
- $LAST_FILE
- $LOG_FILE

Rules:
1) Treat those files as source of truth for continuity.
2) Keep edits minimal and concrete.
3) At the end, update $LAST_FILE with: timestamp, engine(claude), what changed, next steps.
4) If tasks changed, update $TODO_FILE as VALID JSON (no markdown), keeping schema keys.
5) Append one brief run note to $LOG_FILE.

User request:
$USER_PROMPT
EOF

(
  cd "$ROOT"
  claude --permission-mode bypassPermissions --print "$COMPOSITE_PROMPT"
) | tee "$TMP_OUT"

OUTPUT="$(cat "$TMP_OUT")"
rm -f "$TMP_OUT"

if ! validate_todo_json >/dev/null 2>&1; then
  cp "$TODO_BACKUP" "$TODO_FILE"
  OUTPUT="$OUTPUT

[wrapper-note] TODO.md became invalid JSON after run; restored previous valid version."
fi
rm -f "$TODO_BACKUP"

{
  echo ""
  echo "## $TS | claude"
  echo "$OUTPUT"
} >> "$LOG_FILE"

# Fallback update in case engine didn't touch LAST_RESULT.md
if ! grep -q "$TS" "$LAST_FILE" 2>/dev/null; then
  {
    echo "# Last Result"
    echo ""
    echo "- timestamp: $TS"
    echo "- engine: claude"
    echo "- request: $USER_PROMPT"
    echo ""
    echo "## Output (raw)"
    echo "$OUTPUT"
  } > "$LAST_FILE"
fi
