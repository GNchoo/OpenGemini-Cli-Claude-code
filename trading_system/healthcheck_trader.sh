#!/bin/bash
# 트레이더 봇 헬스체크 및 자동 재시작

set -u

SERVICE="trader-autotrader.service"
LOG_FILE="/home/fallman/.openclaw/workspace/trading_system/healthcheck.log"
STATE_FILE="/home/fallman/.openclaw/workspace/trading_system/.healthcheck_state"
HEALTH_JSON="/home/fallman/.openclaw/workspace/trading_system/ws_health.json"
RESTART_COOLDOWN_SEC=480   # 재시작 후 8분간 재시작 금지 (루프 방지)
MIN_UPTIME_SEC=120         # 기동 직후 2분은 관찰만
MAX_TICK_STALE_SEC=30      # ws tick 30초 이상 없으면 이상
MAX_HEALTH_STALE_SEC=120   # health 파일 120초 이상 갱신 없으면 이상

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

now_ts=$(date +%s)
last_restart_ts=0
last_restart_reason=""
if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE" 2>/dev/null || true
  last_restart_ts=${last_restart_ts:-0}
  last_restart_reason=${last_restart_reason:-""}
fi

record_restart() {
  local reason="${1:-manual_or_unknown}"
  cat > "$STATE_FILE" <<EOF
last_restart_ts=$now_ts
last_restart_reason="$reason"
EOF
}

restart_with_reason() {
  local reason="$1"
  local since_last=$((now_ts - last_restart_ts))

  if [ "$since_last" -lt "$RESTART_COOLDOWN_SEC" ]; then
    log "⏭️ 재시작 스킵(쿨다운): $reason | 최근 재시작 ${since_last}초 전"
    return 0
  fi

  log "🚨 $reason - 봇 재시작"
  systemctl --user restart "$SERVICE"
  record_restart "$reason"
  log "✅ 트레이더 봇 재시작 완료"
}

# 1) 서비스 다운이면 즉시 시작
if ! systemctl --user is-active --quiet "$SERVICE"; then
  log "⚠️ 트레이더 봇이 실행되지 않음 - 시작 시도"
  systemctl --user start "$SERVICE"
  record_restart "service_was_down"
  exit 0
fi

# 2) 기동 직후엔 관찰만 (오탐 방지)
active_since=$(systemctl --user show "$SERVICE" -p ActiveEnterTimestampMonotonic --value 2>/dev/null || echo 0)
now_mono=$(cat /proc/uptime | awk '{print int($1*1000000)}')
uptime_sec=$(( (now_mono - active_since) / 1000000 ))
if [ "$uptime_sec" -lt "$MIN_UPTIME_SEC" ]; then
  log "ℹ️ 서비스 기동 ${uptime_sec}초 - 워밍업 구간, 재시작 판단 보류"
  exit 0
fi

# 3) health json 우선 점검
if [ -f "$HEALTH_JSON" ]; then
  # 값 추출 (python 사용)
  read -r health_age ws_connected tick_age fallback_1m <<< "$(python3 - <<PY
import json,time
p='$HEALTH_JSON'
try:
    d=json.load(open(p,'r',encoding='utf-8'))
    now=time.time()
    ts=float(d.get('ts',0) or 0)
    last_tick=float(d.get('last_ws_tick_at',0) or 0)
    ws=1 if d.get('ws_connected') else 0
    f1=int(d.get('rest_fallback_count_1m',0) or 0)
    print(int(now-ts), ws, int(now-last_tick) if last_tick>0 else 999999, f1)
except Exception:
    print(999999,0,999999,999)
PY
)"

  if [ "$health_age" -gt "$MAX_HEALTH_STALE_SEC" ]; then
    restart_with_reason "health 파일 갱신 정지(${health_age}초)"
    exit 0
  fi

  # ws 연결 끊김 + tick stale 동시 충족시 재시작
  if [ "$ws_connected" -eq 0 ] && [ "$tick_age" -gt "$MAX_TICK_STALE_SEC" ]; then
    restart_with_reason "WebSocket 연결 끊김 + tick 지연(${tick_age}초)"
    exit 0
  fi

  # fallback 과다면 재시작
  if [ "$fallback_1m" -ge 6 ]; then
    restart_with_reason "REST fallback 과다(${fallback_1m}회/1분)"
    exit 0
  fi
else
  # health 파일 없으면 기존 로그 기반 fallback
  recent_ws_fallback=$(journalctl --user -u "$SERVICE" --since "2 minutes ago" --no-pager 2>/dev/null | grep -c "WebSocket 시세 없음 → REST API 사용" || true)
  if [ "$recent_ws_fallback" -ge 4 ]; then
    restart_with_reason "WebSocket 시세 실패 감지(${recent_ws_fallback}회/2분)"
    exit 0
  fi
fi

# 4) 오류 폭증 감지 (최근 5분)
error_count=$(journalctl --user -u "$SERVICE" --since "5 minutes ago" --no-pager 2>/dev/null | grep -Eic "error|exception|failed|timeout")
if [ "$error_count" -ge 8 ]; then
  restart_with_reason "과도한 오류 감지(${error_count}개/5분)"
  exit 0
fi

log "✅ 트레이더 봇 정상 작동 중"
exit 0
