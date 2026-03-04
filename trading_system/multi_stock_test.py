#!/usr/bin/env python3
"""
트레이더 마크 📊 - 다중 종목 테스트 (간소화 버전)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_collector import DataCollector
from trading_strategy import MovingAverageCrossover

def run_multi_stock_test():
    """다중 종목 테스트 실행"""
    print("=" * 70)
    print("트레이더 마크 📊 - 다중 종목 테스트")
    print("=" * 70)
    
    # 종목 정보
    stocks = {
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '035420.KS': '네이버',
        '035720.KS': '카카오',
        '005380.KS': '현대차',
        '373220.KS': 'LG에너지솔루션'
    }
    
    # 데이터 수집
    print("\n1. 다중 종목 데이터 수집 중...")
    collector = DataCollector()
    
    all_data = {}
    for ticker, name in stocks.items():
        print(f"  • {name}({ticker})...", end=" ")
        data = collector.get_stock_data(ticker, period="6mo")
        if not data.empty:
            all_data[ticker] = data
            price_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100)
            print(f"✓ {len(data)}일, {price_change:+.1f}%")
        else:
            print("✗ 실패")
    
    if not all_data:
        print("데이터 수집 실패")
        return
    
    print(f"\n총 {len(all_data)}개 종목 데이터 수집 완료")
    
    # 전략 설정
    strategy = MovingAverageCrossover(5, 20)
    print(f"\n2. 트레이딩 전략: {strategy.name}")
    
    # 종목별 테스트
    print("\n3. 종목별 성과 분석...")
    print("-" * 70)
    
    results = []
    
    for ticker, data in all_data.items():
        stock_name = stocks[ticker]
        
        # 간단한 백테스팅
        capital = 10000000  # 1000만원
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(20, len(data)):
            historical_data = data.iloc[:i+1]
            current_price = historical_data['Close'].iloc[-1]
            
            signal = strategy.analyze(historical_data, ticker)
            
            # 간단한 거래 로직
            if signal.action.value == 'BUY' and position <= 0:
                if position == -1:  # 숏 청산
                    pnl = (entry_price - current_price) * 100
                    capital += pnl
                
                position = 1
                entry_price = current_price
                trades.append({'action': 'BUY', 'price': current_price})
                
            elif signal.action.value == 'SELL' and position >= 0:
                if position == 1:  # 롱 청산
                    pnl = (current_price - entry_price) * 100
                    capital += pnl
                
                position = -1
                entry_price = current_price
                trades.append({'action': 'SELL', 'price': current_price})
        
        # 최종 청산
        if position == 1:
            final_price = data['Close'].iloc[-1]
            pnl = (final_price - entry_price) * 100
            capital += pnl
        elif position == -1:
            final_price = data['Close'].iloc[-1]
            pnl = (entry_price - final_price) * 100
            capital += pnl
        
        # 결과 계산
        initial_capital = 10000000
        strategy_return = ((capital - initial_capital) / initial_capital) * 100
        buy_hold_return = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        alpha = strategy_return - buy_hold_return
        volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
        
        results.append({
            '종목': stock_name,
            '티커': ticker,
            '전략수익률(%)': strategy_return,
            '보유수익률(%)': buy_hold_return,
            '알파(%)': alpha,
            '거래횟수': len([t for t in trades if t['action'] in ['BUY', 'SELL']]),
            '변동성(%)': volatility,
            '최종자본(만원)': capital / 10000
        })
    
    # 결과 분석
    results_df = pd.DataFrame(results)
    
    print("\n📊 종목별 성과 요약:")
    print("-" * 70)
    
    display_df = results_df[['종목', '전략수익률(%)', '보유수익률(%)', '알파(%)', '거래횟수', '변동성(%)']].copy()
    display_df['전략수익률(%)'] = display_df['전략수익률(%)'].map(lambda x: f'{x:+.1f}%')
    display_df['보유수익률(%)'] = display_df['보유수익률(%)'].map(lambda x: f'{x:+.1f}%')
    display_df['알파(%)'] = display_df['알파(%)'].map(lambda x: f'{x:+.1f}%')
    display_df['변동성(%)'] = display_df['변동성(%)'].map(lambda x: f'{x:.1f}%')
    
    print(display_df.to_string(index=False))
    
    # 종합 통계
    print("\n📈 종합 통계:")
    print("-" * 70)
    
    avg_strategy_return = results_df['전략수익률(%)'].mean()
    avg_buy_hold_return = results_df['보유수익률(%)'].mean()
    avg_alpha = results_df['알파(%)'].mean()
    
    print(f"평균 전략 수익률: {avg_strategy_return:+.1f}%")
    print(f"평균 보유 수익률: {avg_buy_hold_return:+.1f}%")
    print(f"평균 알파(초과수익): {avg_alpha:+.1f}%")
    print(f"양수 수익률 종목: {sum(results_df['전략수익률(%)'] > 0)}/{len(results_df)}개")
    print(f"양수 알파 종목: {sum(results_df['알파(%)'] > 0)}/{len(results_df)}개")
    
    # 최고/최저 성과
    best_return = results_df.loc[results_df['전략수익률(%)'].idxmax()]
    worst_return = results_df.loc[results_df['전략수익률(%)'].idxmin()]
    
    print(f"\n🎯 최고 성과: {best_return['종목']} ({best_return['전략수익률(%)']:+.1f}%)")
    print(f"⚠️  최저 성과: {worst_return['종목']} ({worst_return['전략수익률(%)']:+.1f}%)")
    
    # 알파 기준 최고 성과
    best_alpha = results_df.loc[results_df['알파(%)'].idxmax()]
    print(f"💡 최고 알파: {best_alpha['종목']} ({best_alpha['알파(%)']:+.1f}%)")
    
    # 포트폴리오 시뮬레이션
    print("\n🏦 포트폴리오 시뮬레이션 (균등가중):")
    print("-" * 70)
    
    portfolio_return = avg_strategy_return
    portfolio_volatility = results_df['변동성(%)'].mean()
    portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
    
    print(f"포트폴리오 수익률: {portfolio_return:+.1f}%")
    print(f"포트폴리오 변동성: {portfolio_volatility:.1f}%")
    print(f"포트폴리오 샤프비율: {portfolio_sharpe:.2f}")
    
    # 투자 권장사항
    print("\n✅ 투자 권장사항:")
    print("-" * 70)
    
    # 알파가 양수인 종목 추천
    positive_alpha_stocks = results_df[results_df['알파(%)'] > 0]
    if not positive_alpha_stocks.empty:
        print("알파(초과수익)가 양수인 종목:")
        for _, row in positive_alpha_stocks.iterrows():
            print(f"  • {row['종목']}: 알파 {row['알파(%)']:+.1f}%, 수익률 {row['전략수익률(%)']:+.1f}%")
    else:
        print("알파가 양수인 종목이 없습니다.")
    
    # 변동성 분석
    high_vol_stocks = results_df[results_df['변동성(%)'] > results_df['변동성(%)'].mean() * 1.5]
    if not high_vol_stocks.empty:
        print("\n⚠️  고변동성 주의 종목:")
        for _, row in high_vol_stocks.iterrows():
            print(f"  • {row['종목']}: 변동성 {row['변동성(%)']:.1f}% (평균의 {row['변동성(%)']/results_df['변동성(%)'].mean():.1f}배)")
    
    # 리포트 저장
    save_detailed_report(results_df)
    
    print("\n" + "=" * 70)
    print("다중 종목 테스트 완료!")
    print("=" * 70)
    
    return results_df

def save_detailed_report(results_df):
    """상세 리포트 저장"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'multi_stock_test_report_{timestamp}.txt'
    
    with open(report_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("트레이더 마크 📊 - 다중 종목 테스트 리포트\n")
        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("테스트 개요:\n")
        f.write("- 테스트 기간: 6개월\n")
        f.write(f"- 테스트 종목: {len(results_df)}개\n")
        f.write("- 트레이딩 전략: 이동평균선 크로스오버 (5,20)\n")
        f.write("- 초기 자본 (종목당): 10,000,000원\n\n")
        
        f.write("종목별 상세 성과:\n")
        f.write("-" * 70 + "\n")
        
        for _, row in results_df.iterrows():
            f.write(f"\n[{row['종목']} ({row['티커']})]\n")
            f.write(f"  • 전략 수익률: {row['전략수익률(%)']:+.2f}%\n")
            f.write(f"  • 단순 보유 수익률: {row['보유수익률(%)']:+.2f}%\n")
            f.write(f"  • 알파(초과수익): {row['알파(%)']:+.2f}%\n")
            f.write(f"  • 거래 횟수: {row['거래횟수']}회\n")
            f.write(f"  • 변동성: {row['변동성(%)']:.1f}%\n")
            f.write(f"  • 최종 자본: {row['최종자본(만원)']:,.1f}만원\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("종합 분석:\n")
        f.write("-" * 70 + "\n\n")
        
        f.write("성과 지표:\n")
        f.write(f"  • 평균 전략 수익률: {results_df['전략수익률(%)'].mean():+.2f}%\n")
        f.write(f"  • 평균 보유 수익률: {results_df['보유수익률(%)'].mean():+.2f}%\n")
        f.write(f"  • 평균 알파: {results_df['알파(%)'].mean():+.2f}%\n")
        f.write(f"  • 양수 수익률 종목: {sum(results_df['전략수익률(%)'] > 0)}/{len(results_df)}개\n")
        f.write(f"  • 양수 알파 종목: {sum(results_df['알파(%)'] > 0)}/{len(results_df)}개\n\n")
        
        f.write("포트폴리오 시뮬레이션 (균등가중):\n")
        portfolio_return = results_df['전략수익률(%)'].mean()
        portfolio_volatility = results_df['변동성(%)'].mean()
        portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
        f.write(f"  • 포트폴리오 수익률: {portfolio_return:+.2f}%\n")
        f.write(f"  • 포트폴리오 변동성: {portfolio_volatility:.1f}%\n")
        f.write(f"  • 포트폴리오 샤프비율: {portfolio_sharpe:.2f}\n\n")
        
        f.write("투자 권장사항:\n")
        f.write("  1. 알파가 양수인 종목 우선 투자\n")
        f.write("  2. 고변동성 종목은 리스크 관리 강화\n")
        f.write("  3. 포트폴리오 다각화로 리스크 분산\n")
        f.write("  4. 정기적인 성과 모니터링\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("트레이더 마크 📊 분석 완료\n")
        f.write("=" * 70 + "\n")
    
    print(f"상세 리포트 저장 완료: {report_file}")

if __name__ == "__main__":
    run_multi_stock_test()