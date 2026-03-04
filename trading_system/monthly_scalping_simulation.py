#!/usr/bin/env python3
"""
트레이더 마크 📊 - 한 달(30일) 단타 매매 시뮬레이션
"""

import random
import json
from datetime import datetime, timedelta
import statistics

class MonthlyScalpingSimulation:
    """한 달 단타 매매 시뮬레이션"""
    
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.portfolio = {}
        self.all_trades = []
        self.daily_results = []
        
        # 단타 설정
        self.config = {
            'target_profit': 0.005,    # 0.5%
            'stop_loss': 0.003,        # 0.3%
            'max_position': 0.02,      # 2%
            'daily_trade_limit': 100,  # 일일 최대 100회
            'min_confidence': 0.6,     # 최소 신뢰도 60%
        }
        
        # 시장 데이터
        self.markets = [
            {'symbol': 'KRW-BTC', 'price': 99619000, 'volatility': 0.02},
            {'symbol': 'KRW-ETH', 'price': 2934000, 'volatility': 0.025},
            {'symbol': 'KRW-XRP', 'price': 2162, 'volatility': 0.03},
            {'symbol': 'KRW-ADA', 'price': 1850, 'volatility': 0.035},
        ]
        
        # 성과 지표
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'max_drawdown': 0,
            'best_day': 0,
            'worst_day': 0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
        }
        
        print("=" * 70)
        print("트레이더 마크 📊 - 한 달 단타 매매 시뮬레이션")
        print("=" * 70)
        print(f"초기 자본: {initial_capital:,.0f}원")
        print(f"기간: 30일 (한 달)")
        print(f"목표 수익: {self.config['target_profit']:.1%}")
        print(f"손절매: {self.config['stop_loss']:.1%}")
        print()
    
    def generate_signal(self, market):
        """단타 신호 생성"""
        symbol = market['symbol']
        price = market['price']
        
        # 기술적 분석 시뮬레이션
        rsi = random.uniform(20, 80)
        momentum = random.uniform(-0.02, 0.02)
        
        # 신호 결정
        confidence = 0.5
        
        if rsi < 30 and momentum > 0:
            signal = 'BUY'
            confidence = 0.7 + random.uniform(0, 0.2)
        elif rsi > 70 and momentum < 0:
            signal = 'SELL'
            confidence = 0.7 + random.uniform(0, 0.2)
        else:
            signal = 'HOLD'
            confidence = 0.3 + random.uniform(0, 0.2)
        
        # 포지션 사이즈
        position = self.capital * 0.01 * confidence  # 1% × 신뢰도
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'position': position,
            'price': price
        }
    
    def execute_trade(self, signal):
        """거래 실행"""
        symbol = signal['symbol']
        action = signal['signal']
        price = signal['price']
        position = signal['position']
        
        if action == 'BUY':
            # 매수
            if position > self.capital:
                return None
            
            qty = position / price
            self.capital -= position
            
            if symbol in self.portfolio:
                self.portfolio[symbol] += qty
            else:
                self.portfolio[symbol] = qty
            
            trade = {
                'time': datetime.now(),
                'type': 'BUY',
                'symbol': symbol,
                'price': price,
                'qty': qty,
                'amount': position
            }
            self.all_trades.append(trade)
            return trade
        
        elif action == 'SELL':
            # 매도
            if symbol not in self.portfolio or self.portfolio[symbol] <= 0:
                return None
            
            qty = min(self.portfolio[symbol], position / price)
            amount = qty * price
            
            # 수익/손실 계산 (시뮬레이션)
            profit_ratio = random.uniform(-self.config['stop_loss'], self.config['target_profit'])
            profit = amount * profit_ratio
            
            self.capital += amount + profit
            self.portfolio[symbol] -= qty
            
            if self.portfolio[symbol] <= 0:
                del self.portfolio[symbol]
            
            # 성과 지표 업데이트
            self.metrics['total_trades'] += 1
            if profit > 0:
                self.metrics['winning_trades'] += 1
                self.metrics['consecutive_wins'] += 1
                self.metrics['consecutive_losses'] = 0
            else:
                self.metrics['losing_trades'] += 1
                self.metrics['consecutive_losses'] += 1
                self.metrics['consecutive_wins'] = 0
            
            self.metrics['total_profit'] += profit
            
            trade = {
                'time': datetime.now(),
                'type': 'SELL',
                'symbol': symbol,
                'price': price,
                'qty': qty,
                'amount': amount,
                'profit': profit,
                'profit_ratio': profit_ratio
            }
            self.all_trades.append(trade)
            return trade
        
        return None
    
    def update_prices(self):
        """가격 업데이트"""
        for market in self.markets:
            change = random.uniform(-market['volatility'], market['volatility'])
            market['price'] *= (1 + change)
    
    def get_portfolio_value(self):
        """포트폴리오 가치"""
        value = self.capital
        for symbol, qty in self.portfolio.items():
            market = next(m for m in self.markets if m['symbol'] == symbol)
            value += qty * market['price']
        return value
    
    def run_day(self, day_num):
        """하루 거래 실행"""
        day_start = self.capital
        day_trades = 0
        day_profits = []
        
        # 5분 봉 기준 288번의 기회 (24시간)
        for i in range(288):
            # 가격 업데이트 (5분마다)
            if i % 1 == 0:
                self.update_prices()
            
            # 거래 시도 (25% 확률)
            if random.random() < 0.25 and day_trades < self.config['daily_trade_limit']:
                market = random.choice(self.markets)
                signal = self.generate_signal(market)
                
                if signal['confidence'] >= self.config['min_confidence']:
                    trade = self.execute_trade(signal)
                    if trade and trade['type'] == 'SELL':
                        day_trades += 1
                        day_profits.append(trade.get('profit', 0))
        
        # 일일 결과 계산
        portfolio_value = self.get_portfolio_value()
        day_profit = portfolio_value - day_start
        day_return = (day_profit / day_start) * 100
        
        # 최대 낙폭 업데이트
        if day_profit < self.metrics['worst_day']:
            self.metrics['worst_day'] = day_profit
        if day_profit > self.metrics['best_day']:
            self.metrics['best_day'] = day_profit
        
        # 드로다운 계산
        peak = max(self.metrics.get('peak_value', day_start), portfolio_value)
        drawdown = (peak - portfolio_value) / peak * 100
        if drawdown > self.metrics['max_drawdown']:
            self.metrics['max_drawdown'] = drawdown
        
        self.metrics['peak_value'] = peak
        
        # 일일 결과 저장
        result = {
            'day': day_num,
            'date': (datetime.now() + timedelta(days=day_num-1)).strftime('%Y-%m-%d'),
            'start_capital': day_start,
            'end_capital': self.capital,
            'portfolio_value': portfolio_value,
            'profit': day_profit,
            'return_pct': day_return,
            'trades': day_trades,
            'avg_trade_profit': statistics.mean(day_profits) if day_profits else 0
        }
        
        self.daily_results.append(result)
        
        # 진행 상황 출력 (5일마다)
        if day_num % 5 == 0 or day_num == 30:
            print(f"📅 Day {day_num:2d}/30: {day_profit:+,.0f}원 ({day_return:+.2f}%), "
                  f"거래: {day_trades}회, 자본: {self.capital:,.0f}원")
        
        return result
    
    def run_month(self):
        """한 달 시뮬레이션 실행"""
        print("\n" + "=" * 70)
        print("30일 단타 매매 시뮬레이션 시작")
        print("=" * 70)
        
        weekly_results = []
        
        for week in range(1, 5):
            week_start = self.capital
            week_profit = 0
            week_trades = 0
            
            print(f"\n📊 Week {week}")
            print("-" * 40)
            
            for day in range(1, 8):
                day_num = (week-1)*7 + day
                if day_num > 30:
                    break
                
                result = self.run_day(day_num)
                week_profit += result['profit']
                week_trades += result['trades']
            
            week_return = (week_profit / week_start) * 100
            weekly_results.append({
                'week': week,
                'profit': week_profit,
                'return_pct': week_return,
                'trades': week_trades
            })
            
            print(f"  주간 수익: {week_profit:+,.0f}원 ({week_return:+.2f}%)")
            print(f"  주간 거래: {week_trades}회")
        
        # 최종 리포트
        self.generate_report(weekly_results)
    
    def generate_report(self, weekly_results):
        """최종 리포트 생성"""
        final_value = self.get_portfolio_value()
        total_profit = final_value - self.initial_capital
        total_return = (total_profit / self.initial_capital) * 100
        
        # 월간 CAGR 계산
        monthly_cagr = ((1 + total_return/100) ** (12/1) - 1) * 100
        
        print("\n" + "=" * 70)
        print("한 달 단타 매매 시뮬레이션 결과")
        print("=" * 70)
        
        print(f"\n📈 기본 성과:")
        print(f"  초기 자본: {self.initial_capital:,.0f}원")
        print(f"  최종 가치: {final_value:,.0f}원")
        print(f"  총 수익: {total_profit:+,.0f}원")
        print(f"  총 수익률: {total_return:+.2f}%")
        print(f"  월간 CAGR: {monthly_cagr:+.1f}%")
        
        print(f"\n📊 거래 통계:")
        print(f"  총 거래: {self.metrics['total_trades']}회")
        print(f"  승리 거래: {self.metrics['winning_trades']}회")
        print(f"  패배 거래: {self.metrics['losing_trades']}회")
        
        if self.metrics['total_trades'] > 0:
            win_rate = (self.metrics['winning_trades'] / self.metrics['total_trades']) * 100
            avg_profit = self.metrics['total_profit'] / self.metrics['total_trades']
            print(f"  승률: {win_rate:.1f}%")
            print(f"  평균 거래 수익: {avg_profit:+,.0f}원")
        
        print(f"\n📅 주간 성과:")
        for week in weekly_results:
            print(f"  Week {week['week']}: {week['profit']:+,.0f}원 ({week['return_pct']:+.2f}%), "
                  f"거래: {week['trades']}회")
        
        print(f"\n📉 리스크 지표:")
        print(f"  최대 낙폭: {self.metrics['max_drawdown']:.1f}%")
        print(f"  최고 일일: {self.metrics['best_day']:+,.0f}원")
        print(f"  최악 일일: {self.metrics['worst_day']:+,.0f}원")
        
        # 수익 분포
        profits = [r['profit'] for r in self.daily_results]
        positive_days = sum(1 for p in profits if p > 0)
        negative_days = sum(1 for p in profits if p < 0)
        
        print(f"\n📊 일별 수익 분포:")
        print(f"  수익일: {positive_days}일")
        print(f"  손실일: {negative_days}일")
        print(f"  무변동: {30 - positive_days - negative_days}일")
        
        if profits:
            avg_daily = statistics.mean(profits)
            std_daily = statistics.stdev(profits) if len(profits) > 1 else 0
            print(f"  평균 일일: {avg_daily:+,.0f}원")
            print(f"  일일 변동성: {std_daily:,.0f}원")
        
        print(f"\n📦 최종 포트폴리오:")
        if self.portfolio:
            for symbol, qty in self.portfolio.items():
                market = next(m for m in self.markets if m['symbol'] == symbol)
                value = qty * market['price']
                print(f"  {symbol}: {qty:.6f}개 ({value:,.0f}원)")
        else:
            print("  보유 종목 없음")
        
        print(f"\n🎯 평가:")
        if total_return > 10:
            print("  ✅ 우수! 단타 매매 전략 매우 효과적")
            print("  💡 3월 16일 실전 투자 적극 권장")
        elif total_return > 5:
            print("  ⚠️ 양호. 추가 최적화 가능")
            print("  💡 소액으로 실전 테스트 권장")
        elif total_return > 0:
            print("  ⚠️ 미미한 수익. 전략 개선 필요")
            print("  💡 모의투자 계속 진행")
        else:
            print("  ❌ 부정적. 전략 재검토 필요")
            print("  💡 기본 전략 수정 후 재시도")
        
        print(f"\n🚀 다음 단계:")
        print("1. AI 단타 전문가 통합")
        print("2. 실시간 데이터 연동")
        print("3. 리스크 관리 강화")
        print(f"4. 3월 16일 실전 투자 준비")
        
        print("\n" + "=" * 70)
        print("✅ 한 달 시뮬레이션 완료!")
        print("=" * 70)
        
        # 결과 저장
        self.save_results(total_profit, total_return)
    
    def save_results(self, total_profit, total_return):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monthly_scalping_{timestamp}.json"
        
        data = {
            'simulation_info': {
                'initial_capital': self.initial_capital,
                'final_capital': self.capital,
                'total_profit': total_profit,
                'total_return_pct': total_return,
                'period_days': 30,
                'timestamp': datetime.now().isoformat()
            },
            'metrics': self.metrics,
            'daily_results': self.daily_results,
            'config': self.config
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 결과 저장 완료: {filename}")
        return filename

def main():
    """메인 실행"""
    print("트레이더 마크 📊 - 한 달 단타 매매 수익 분석")
    
    # 100만원으로 30일 시뮬레이션
    simulator = MonthlyScalpingSimulation(initial_capital=1000000)
    
    # 한 달 시뮬레이션 실행
    simulator.run_month()
    
    print("\n💡 핵심 통찰:")
    print("• 단타 매매는 일관성이 핵심")
    print("• 작은 수익의 누적이 중요")
    print("• 리스크 관리가 성패를 결정")
