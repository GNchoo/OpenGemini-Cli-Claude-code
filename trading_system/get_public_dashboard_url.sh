#!/usr/bin/env bash
set -euo pipefail

URL=$(journalctl --user -u trader-cloudflared.service --no-pager -n 200 \
  | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' \
  | tail -1 || true)

if [[ -z "${URL}" ]]; then
  echo "URL_NOT_FOUND"
  exit 1
fi

echo "${URL}"
