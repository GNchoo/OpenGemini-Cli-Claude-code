#!/usr/bin/env bash
set -euo pipefail

BASE="/home/fallman/.openclaw/workspace/trading_system"
URL_SCRIPT="$BASE/get_public_dashboard_url.sh"
STATE_FILE="$BASE/.dashboard_public_url_last"

url="$($URL_SCRIPT 2>/dev/null || true)"
if [[ -z "$url" ]]; then
  echo "ERROR:URL_UNAVAILABLE"
  exit 1
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "$url" > "$STATE_FILE"
  echo "INIT:$url"
  exit 0
fi

prev="$(cat "$STATE_FILE" 2>/dev/null || true)"
if [[ "$url" != "$prev" ]]; then
  echo "$url" > "$STATE_FILE"
  echo "CHANGED:$prev->$url"
  exit 0
fi

echo "UNCHANGED:$url"
