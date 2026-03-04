#!/usr/bin/env python3
"""
트레이더 마크 📊 - 한 달 단타 매매 간단 시뮬레이션
"""

import random

def simulate_month():
    """한 달 단타 매매 시뮬레이션"""
    capital = 1000000
    total_trades = 0
    winning_trades = 0
    daily_results = []
    
    print("=" * 70)
    print("트레이더 마크 📊 - 한 달 단타 매매 시뮬레이션")
    print("=" * 70)
    print(f"초기 자본: {capital:,.0f}원")
    print(f"기간: 30일")
    print(f"목표: 0.5%, 손절: 0.3%")
    print()
    
    for day in range(1, 31):
        day_start = capital
        day_trades = random.randint(20, 60)  # 하루 20~60회 거래
        day_profit = 0
        
        for _ in range(day_trades):
            total_trades += 1
            
            # 거래 결과 (70% 승률 가정)
            if random.random() < 0.7:
                # 승리: 0.2%~0.5% 수익
                profit = capital * 0.0001 * random.uniform(2, 5)
                winning_trades += 1
            else:
                # 패배: 0.1%~0.3% 손실
                profit = -capital * 0.0001 * random.uniform(1, 3)
            
            capital += profit
            day_profit += profit
        
        day_return = (day_profit / day_start) * 100
        daily_results.append({
            'day': day,
            'profit': day_profit,
            'return': day_return,
            'trades': day_trades
        })
        
        # 5일마다 출력
        if day % 5 == 0:
            print(f"📅 Day {day:2d}: {day_profit:+,.0f}원 ({day_return:+.2f}%), "
                  f"거래: {day_trades}회, 자본: {capital:,.0f}원")
    
    # 결과 분석
    total_profit = capital - 1000000
    total_return = (total_profit / 1000000) * 100
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    # 일별 수익 분석
    profits = [r['profit'] for r in daily_results]
    positive_days = sum(1 for p in profits if p > 0)
    negative_days = sum(1 for p in profits if p < 0)
    
    print("\n" + "=" * 70)
    print("한 달 단타 매매 결과")
    print("=" * 70)
    
    print(f"\n📈 최종 성과:")
    print(f"  초기 자본: 1,000,000원")
    print(f"  최종 자본: {capital:,.0f}원")
    print(f"  총 수익: {total_profit:+,.0f}원")
    print(f"  수익률: {total_return:+.2f}%")
    
    print(f"\n📊 거래 통계:")
    print(f"  총 거래: {total_trades}회")
    print(f"  승리 거래: {winning_trades}회")
    print(f"  패배 거래: {total_trades - winning_trades}회")
    print(f"  승률: {win_rate:.1f}%")
    
    print(f"\n📅 일별 분포:")
    print(f"  수익일: {positive_days}일")
    print(f"  손실일: {negative_days}일")
    print(f"  무변동: {30 - positive_days - negative_days}일")
    
    # 주간 분석
    print(f"\n📊 주간 성과:")
    for week in range(1, 5):
        week_start = (week-1)*7
        week_end = min(week*7, 30)
        week_profits = profits[week_start:week_end]
        week_total = sum(week_profits)
        week_return = (week_total / 1000000) * 100
        
        print(f"  Week {week}: {week_total:+,.0f}원 ({week_return:+.2f}%)")
    
    print(f"\n🎯 평가:")
    if total_return > 15:
        print("  ✅ 우수! 단타 매매 매우 효과적")
        print("  💡 실전 투자 적극 권장")
    elif total_return > 8:
        print("  ⚠️ 양호. 추가 최적화 가능")
        print("  💡 소액 실전 테스트 권장")
    elif total_return > 0:
        print("  ⚠️ 미미한 수익. 전략 개선 필요")
        print("  💡 모의투자 계속 진행")
    else:
        print("  ❌ 부정적. 전략 재검토 필요")
        print("  💡 기본 전략 수정")
    
    print(f"\n🚀 3월 16일까지 계획:")
    print("1. AI 단타 전문가 통합")
    print("2. 실시간 데이터 연동")
    print("3. 리스크 관리 강화")
    print("4. 실전 투자 준비 완료")
    
    print("\n" + "=" * 70)
    print("✅ 한 달 시뮬레이션 완료!")
    print("=" * 70)
    
    return total_return

def main():
    """메인 실행"""
    print("트레이더 마크 📊 - 단타 매매 한 달 수익 분석")
    
    # 시뮬레이션 실행
    return_rate = simulate_month()
    
    print(f"\n💡 예상 연간 수익률: {return_rate * 12:.1f}%")
    print(f"💡 100만원 → 1억원 예상 기간: {100 / return_rate:.1f}개월")
    
    print("\n📊 핵심 통찰:")
    print("• 단타 매매는 일관성이 핵심")
    print("• 작은 수익의 누적이 중요")
    print("• 승률보다 평균 수익/손실 비율이 중요")
    print("• 리스크 관리가 성패 결정")

if __name__ == "__main__":
    main()