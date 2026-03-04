#!/bin/bash
# 주간 성과 분석 도구

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$SCRIPT_DIR/reports"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 주간 트레이딩 성과 분석"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 최근 7일 리포트 파일 찾기
reports=$(find "$REPORT_DIR" -name "report_*.json" -mtime -7 | sort)

if [ -z "$reports" ]; then
    echo "⚠️ 최근 7일 리포트가 없습니다."
    exit 0
fi

echo "📁 분석 기간: 최근 7일"
echo ""

python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime

report_dir = Path('reports')
reports = sorted(report_dir.glob('report_*.json'), reverse=True)[:7]

if not reports:
    print("리포트 없음")
    exit()

total_trades = 0
total_pnl = 0
wins = 0
losses = 0
profit_factors = []

print("일별 요약:")
print(f"{'날짜':<12} {'거래':<6} {'손익':<10} {'승률':<8}")
print("="*50)

for report_file in reversed(reports):
    try:
        data = json.loads(report_file.read_text())
        date = data.get('date', 'N/A')
        trades = data.get('total_trades', 0)
        pnl = data.get('total_pnl_pct', 0)
        win_rate = data.get('win_rate', 0)
        
        total_trades += trades
        total_pnl += pnl
        wins += data.get('win_count', 0)
        losses += data.get('loss_count', 0)
        
        if 'profit_factor' in data:
            pf = data['profit_factor']
            if pf != float('inf'):
                profit_factors.append(pf)
        
        print(f"{date:<12} {trades:<6} {pnl:>8.2%} {win_rate:>7.1%}")
    except Exception as e:
        print(f"⚠️ {report_file.name}: {e}")

print("="*50)
print(f"\n📊 주간 종합:")
print(f"총 거래: {total_trades}회")
print(f"총 손익: {total_pnl:+.2%}")
print(f"주간 승률: {wins/(wins+losses):.1%} ({wins}승 {losses}패)")
if profit_factors:
    avg_pf = sum(profit_factors) / len(profit_factors)
    print(f"평균 Profit Factor: {avg_pf:.2f}")

PY
