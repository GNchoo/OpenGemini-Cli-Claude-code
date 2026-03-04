#!/bin/bash
# 일일 리포트 cron 작업 설정
# 매일 09:00에 리포트 생성

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_SCRIPT="$SCRIPT_DIR/daily_report.py"

# crontab에 추가
(crontab -l 2>/dev/null | grep -v "daily_report.py"; echo "0 9 * * * cd $SCRIPT_DIR && python3 $REPORT_SCRIPT >> $SCRIPT_DIR/logs/daily_report.log 2>&1") | crontab -

echo "✅ 일일 리포트 cron 작업 추가 완료"
echo "매일 09:00에 실행됩니다"
crontab -l | grep daily_report
