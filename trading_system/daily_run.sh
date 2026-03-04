#!/bin/bash
# 트레이더 마크 📊 - 매일 모의투자 실행 스크립트
# 사용법: bash daily_run.sh

cd "$(dirname "$0")"
source trader_env/bin/activate

echo "====================================="
echo "트레이더 마크 📊 - 오늘의 모의투자"
echo "날짜: $(date '+%Y-%m-%d %H:%M')"
echo "====================================="

python3 paper_engine.py 2>&1

echo ""
echo "✅ 완료. 누적 성과:"
python3 paper_engine.py --report 2>&1 | tail -30
