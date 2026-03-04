#!/usr/bin/env python3
"""
일일 트레이딩 성과 리포트 생성
매일 09:00 cron으로 실행
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from telegram_notifier import send_message as telegram_send
    TELEGRAM_AVAILABLE = True
except Exception:
    TELEGRAM_AVAILABLE = False

TRADE_LOG_FILE = Path(__file__).parent / 'live_trade_log.json'
REPORT_DIR = Path(__file__).parent / 'reports'
REPORT_DIR.mkdir(exist_ok=True)

def generate_daily_report():
    """어제 거래 분석 리포트 생성"""
    try:
        if not TRADE_LOG_FILE.exists():
            print("거래 로그 파일 없음")
            return
        
        trades = json.loads(TRADE_LOG_FILE.read_text(encoding='utf-8'))
        
        # 어제 날짜 범위
        yesterday = datetime.now().date() - timedelta(days=1)
        start_ts = datetime.combine(yesterday, datetime.min.time()).timestamp()
        end_ts = datetime.combine(yesterday, datetime.max.time()).timestamp()
        
        # 어제 거래만 필터 (timestamp/date 모두 지원)
        daily_trades = []
        for t in trades:
            ts = t.get('timestamp')
            if ts is None:
                d = t.get('date')
                if d:
                    try:
                        ts = datetime.fromisoformat(str(d).replace('Z', '+00:00')).timestamp()
                    except Exception:
                        ts = None
            if ts is None:
                continue
            if start_ts <= ts <= end_ts:
                daily_trades.append(t)
        
        if not daily_trades:
            print(f"어제({yesterday}) 거래 없음")
            return
        
        # 통계 계산
        stats = {
            'date': str(yesterday),
            'total_trades': len(daily_trades),
            'buys': sum(1 for t in daily_trades if (t.get('action') or t.get('side')) == 'BUY'),
            'sells': sum(1 for t in daily_trades if (t.get('action') or t.get('side')) == 'SELL'),
        }
        
        # 매도 거래만 분석 (손익 있음)
        sell_trades = [t for t in daily_trades if (t.get('action') or t.get('side')) == 'SELL' and 'pnl' in t]
        
        if sell_trades:
            total_pnl = sum(t['pnl'] for t in sell_trades)
            wins = [t for t in sell_trades if t['pnl'] > 0]
            losses = [t for t in sell_trades if t['pnl'] < 0]
            
            stats['total_pnl_pct'] = total_pnl
            stats['win_count'] = len(wins)
            stats['loss_count'] = len(losses)
            stats['win_rate'] = len(wins) / len(sell_trades) if sell_trades else 0
            stats['avg_win'] = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
            stats['avg_loss'] = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
            stats['largest_win'] = max((t['pnl'] for t in wins), default=0)
            stats['largest_loss'] = min((t['pnl'] for t in losses), default=0)
            stats['profit_factor'] = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses else float('inf')
        
        # 심볼별 분석
        by_symbol = defaultdict(list)
        for t in sell_trades:
            by_symbol[t['symbol']].append(t)
        
        stats['by_symbol'] = {}
        for sym, trades_list in by_symbol.items():
            stats['by_symbol'][sym] = {
                'count': len(trades_list),
                'total_pnl': sum(t['pnl'] for t in trades_list),
                'win_rate': sum(1 for t in trades_list if t['pnl'] > 0) / len(trades_list)
            }
        
        # 리포트 저장
        report_file = REPORT_DIR / f"report_{yesterday}.json"
        report_file.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 요약 출력
        print(f"\n{'='*60}")
        print(f"📊 일일 리포트 - {yesterday}")
        print(f"{'='*60}")
        print(f"거래 횟수: {stats['total_trades']}회 (매수 {stats['buys']}, 매도 {stats['sells']})")
        
        if sell_trades:
            print(f"\n수익/손실:")
            print(f"  총 손익: {stats['total_pnl_pct']:+.2%}")
            print(f"  승률: {stats['win_rate']:.1%} ({stats['win_count']}승 {stats['loss_count']}패)")
            print(f"  평균 수익: {stats['avg_win']:+.2%}")
            print(f"  평균 손실: {stats['avg_loss']:+.2%}")
            print(f"  최대 수익: {stats['largest_win']:+.2%}")
            print(f"  최대 손실: {stats['largest_loss']:+.2%}")
            print(f"  Profit Factor: {stats['profit_factor']:.2f}")
            
            if stats['by_symbol']:
                print(f"\n심볼별:")
                for sym, sym_stats in stats['by_symbol'].items():
                    print(f"  {sym}: {sym_stats['count']}회, PnL {sym_stats['total_pnl']:+.2%}, 승률 {sym_stats['win_rate']:.1%}")
        
        print(f"\n리포트 저장: {report_file}")
        print(f"{'='*60}\n")
        
        # Telegram으로 요약 전송
        if TELEGRAM_AVAILABLE and sell_trades:
            summary = f"""📊 *일일 트레이딩 리포트* - {yesterday}

💰 *수익/손실*
총 손익: `{stats['total_pnl_pct']:+.2%}`
승률: `{stats['win_rate']:.1%}` ({stats['win_count']}승 {stats['loss_count']}패)

📈 *성과*
평균 수익: `{stats['avg_win']:+.2%}`
평균 손실: `{stats['avg_loss']:+.2%}`
최대 수익: `{stats['largest_win']:+.2%}`
최대 손실: `{stats['largest_loss']:+.2%}`
Profit Factor: `{stats['profit_factor']:.2f}`

📊 *거래*
총 거래: {stats['total_trades']}회 (매수 {stats['buys']}, 매도 {stats['sells']})
"""
            try:
                telegram_send(summary)
                print("✅ Telegram 리포트 전송 완료")
            except Exception as e:
                print(f"⚠️ Telegram 전송 실패: {e}")
        
        return stats
        
    except Exception as e:
        print(f"리포트 생성 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_daily_report()
