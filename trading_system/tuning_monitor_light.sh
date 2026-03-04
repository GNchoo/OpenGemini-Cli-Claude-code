#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/fallman/.openclaw/workspace/trading_system"
STATUS_FILE="$BASE_DIR/ai_status_live.json"
LOG_FILE="$BASE_DIR/live_trade_log.json"

echo "🔍 튜닝 경량 모니터링 시작 ($(date '+%Y-%m-%d %H:%M:%S %Z'))"

if [[ ! -f "$STATUS_FILE" ]]; then
  echo "⚠️ 상태 파일 없음: $STATUS_FILE"
  exit 1
fi

# 최근 상태 파일 갱신 시간 확인
status_mtime=$(date -r "$STATUS_FILE" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || true)
if [[ -n "$status_mtime" ]]; then
  echo "✅ 상태 파일 확인: ai_status_live.json (수정시각: $status_mtime)"
else
  echo "ℹ️ 상태 파일 확인: ai_status_live.json"
fi

# 로그 파일 존재 여부 (선택)
if [[ -f "$LOG_FILE" ]]; then
  log_mtime=$(date -r "$LOG_FILE" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || true)
  echo "ℹ️ 거래 로그 확인: live_trade_log.json (수정시각: ${log_mtime:-unknown})"
else
  echo "ℹ️ 거래 로그 없음: live_trade_log.json"
fi

echo "✅ 튜닝 모니터링 정상 종료"
