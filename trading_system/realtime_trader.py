#!/usr/bin/env python3
"""
트레이더 마크 📊 - 실시간 모의투자 모니터링 서비스
WebSocket + AI 신호 + 자동 거래 실행
"""

import json, os, sys, time, threading, asyncio
from datetime import datetime, timedelta
from pathlib import Path
import websocket
import requests

from ai_signal_engine   import AISignalEngine
from volatility_monitor import VolatilityCalculator, EmergencyStopManager
from upbit_live_client  import UpbitLiveClient
from paper_engine       import PaperEngine, FEE_RATE, BEP_RATE

# ─────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────
SYMBOLS = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
CHECK_INTERVAL = 5  # 초 (신호 체크 간격)
MIN_CONFIDENCE = 0.65  # AI 신호 최소 신뢰도
MAX_TRADES_PER_HOUR = 20  # 시간당 최대 거래 수

# ─────────────────────────────────────────────────────────────
# 실시간 모니터링 클래스
# ─────────────────────────────────────────────────────────────
class RealtimeTrader:
    """WebSocket 기반 실시간 모의투자 모니터링"""

    def __init__(self):
        self.paper_engine = PaperEngine()
        self.ai_engine = AISignalEngine()
        self.vol_calc = VolatilityCalculator()
        self.upbit = UpbitLiveClient()
        
        self.running = True
        self.trade_counts = {}  # 시간별 거래 카운트
        self.last_prices = {}
        self.websocket = None
        
        print("=" * 70)
        print("트레이더 마크 📊 - 실시간 모의투자 모니터링")
        print("=" * 70)
        print(f"심볼: {', '.join(SYMBOLS)}")
        print(f"체크 간격: {CHECK_INTERVAL}초")
        print(f"AI 최소 신뢰도: {MIN_CONFIDENCE*100:.0f}%")
        print()

    def update_price(self, symbol: str, price: float):
        """가격 업데이트 및 신호 체크"""
        self.last_prices[symbol] = price
        
        # 변동성 계산
        if symbol not in self.vol_calc.price_history:
            self.vol_calc.price_history[symbol] = []
        self.vol_calc.price_history[symbol].append(price)
        if len(self.vol_calc.price_history[symbol]) > 200:
            self.vol_calc.price_history[symbol].pop(0)
        
        # AI 신호 생성
        if len(self.vol_calc.price_history[symbol]) >= 20:  # 최소 데이터
            prices = self.vol_calc.price_history[symbol][-50:]  # 최근 50개
            signal, confidence = self.ai_engine.decide(prices)
            
            if confidence >= MIN_CONFIDENCE:
                self.process_signal(symbol, price, signal, confidence)

    def process_signal(self, symbol: str, price: float, signal: str, confidence: float):
        """AI 신호 처리"""
        # 거래 제한 체크
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        if hour_key not in self.trade_counts:
            self.trade_counts[hour_key] = 0
        
        if self.trade_counts[hour_key] >= MAX_TRADES_PER_HOUR:
            return
        
        # 현재 포지션 확인
        positions = self.paper_engine.portfolio.positions
        
        if signal == "BUY" and symbol not in positions:
            # 매수 신호
            vol = self.vol_calc.calculate(symbol, self.vol_calc.price_history[symbol])
            strategy = self.vol_calc.suggest_strategy(vol)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 BUY 신호 {symbol}")
            print(f"   가격: {price:,.0f}원 | 신뢰도: {confidence:.1%} | 전략: {strategy}")
            
            self.paper_engine.open_position(symbol, price, strategy)
            self.trade_counts[hour_key] += 1
            self.paper_engine.portfolio.save()
            
        elif signal == "SELL" and symbol in positions:
            # 매도 신호
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 SELL 신호 {symbol}")
            print(f"   가격: {price:,.0f}원 | 신뢰도: {confidence:.1%}")
            
            self.paper_engine.close_position(symbol, price, "AI_SELL")
            self.trade_counts[hour_key] += 1
            self.paper_engine.portfolio.save()

    def fetch_realtime_prices(self):
        """WebSocket 대신 REST API로 실시간 가격 조회 + AI 신호 + 거래"""
        print(f"실시간 거래 모니터링 시작 (간격: {CHECK_INTERVAL}초)")
        
        while self.running:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 가격 조회 시작")
                
                for symbol in SYMBOLS:
                    try:
                        # 실시간 가격 조회
                        tickers = self.upbit.get_ticker([symbol])
                        if tickers and len(tickers) > 0:
                            price = float(tickers[0]["trade_price"])
                            self.last_prices[symbol] = price
                            
                            # 변동성 계산을 위한 가격 기록
                            if symbol not in self.vol_calc.price_history:
                                self.vol_calc.price_history[symbol] = []
                            self.vol_calc.price_history[symbol].append(price)
                            if len(self.vol_calc.price_history[symbol]) > 200:
                                self.vol_calc.price_history[symbol].pop(0)
                            
                            print(f"   {symbol}: {price:,.0f}원", end="")
                            
                            # AI 신호 생성 (최소 20개 데이터 필요)
                            if len(self.vol_calc.price_history[symbol]) >= 20:
                                prices = self.vol_calc.price_history[symbol][-50:]  # 최근 50개
                                signal, confidence = self.ai_engine.decide(prices)
                                
                                if confidence >= MIN_CONFIDENCE:
                                    print(f" | {signal} 신호 ({confidence:.1%})", end="")
                                    self.process_signal(symbol, price, signal, confidence)
                            
                            print()  # 줄바꿈
                            
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"   {symbol} 오류: {e}")
                
                # 손절/익절 체크
                positions = self.paper_engine.portfolio.positions
                if positions:
                    for symbol in list(positions.keys()):
                        if symbol in self.last_prices:
                            self.paper_engine.check_exits(symbol, self.last_prices[symbol])
                
                # 포트폴리오 파일 업데이트 시간 표시
                import os, time as ttime
                if os.path.exists("paper_portfolio.json"):
                    mtime = os.path.getmtime("paper_portfolio.json")
                    age = ttime.time() - mtime
                    print(f"   📁 포트폴리오: {datetime.fromtimestamp(mtime).strftime('%H:%M:%S')} ({age:.0f}초 전)")
                
                print(f"[{timestamp}] 다음 조회까지 {CHECK_INTERVAL}초 대기...")
                print("-" * 50)
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self.running = False
                print("\n모니터링 종료")
                break
            except Exception as e:
                print(f"메인 루프 오류: {e}")
                time.sleep(5)

    def run(self):
        """실시간 모니터링 시작"""
        import sys
        sys.stdout.flush()
        print("실시간 모니터링 시작... (Ctrl+C로 종료)", flush=True)
        print("-" * 70, flush=True)
        
        try:
            self.fetch_realtime_prices()
        except KeyboardInterrupt:
            print("\n모니터링 종료")
        finally:
            self.running = False
            print("포트폴리오 저장 완료")

    def status(self):
        """현재 상태 출력"""
        print("\n" + "=" * 70)
        print("실시간 모니터링 상태")
        print("=" * 70)
        
        # 가격 정보
        print("📈 실시간 가격:")
        for symbol in SYMBOLS:
            price = self.last_prices.get(symbol, 0)
            if price > 0:
                print(f"   {symbol}: {price:,.0f}원")
        
        # 포지션 정보
        positions = self.paper_engine.portfolio.positions
        if positions:
            print("\n📊 현재 포지션:")
            for symbol, pos in positions.items():
                current = self.last_prices.get(symbol, pos["entry"])
                pnl_pct = (current - pos["entry"]) / pos["entry"] * 100
                color = "🟢" if pnl_pct >= 0 else "🔴"
                print(f"   {color} {symbol}: 진입 {pos['entry']:,.0f}원 → 현재 {current:,.0f}원 ({pnl_pct:+.2f}%)")
        
        # 오늘 거래 통계
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = [t for t in self.paper_engine.portfolio.data["trade_log"]
                       if t["date"].startswith(today)]
        
        print(f"\n📅 오늘 거래: {len(today_trades)}회")
        print(f"💰 현재 자본: {self.paper_engine.portfolio.capital:,.0f}원")
        print("=" * 70)


# ─────────────────────────────────────────────────────────────
# 시스템 서비스 등록
# ─────────────────────────────────────────────────────────────
def create_systemd_service():
    """systemd 서비스 파일 생성"""
    service_content = f"""[Unit]
Description=트레이더 마크 실시간 모의투자 모니터링
After=network.target trader-dashboard.service
Requires=trader-dashboard.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 {Path(__file__).absolute()}
WorkingDirectory={Path(__file__).parent.absolute()}
Restart=always
RestartSec=10
Environment=HOME=/home/fallman

[Install]
WantedBy=default.target
"""
    
    service_path = Path.home() / ".config/systemd/user/trader-realtime.service"
    service_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(service_path, "w") as f:
        f.write(service_content)
    
    print(f"서비스 파일 생성: {service_path}")
    print("등록 명령어:")
    print(f"  systemctl --user daemon-reload")
    print(f"  systemctl --user enable trader-realtime.service")
    print(f"  systemctl --user start trader-realtime.service")


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="트레이더 마크 실시간 모니터링")
    parser.add_argument("--service", action="store_true", help="systemd 서비스 파일 생성")
    parser.add_argument("--status", action="store_true", help="현재 상태 확인")
    parser.add_argument("--run", action="store_true", help="실시간 모니터링 실행")
    
    args = parser.parse_args()
    
    if args.service:
        create_systemd_service()
    elif args.status:
        trader = RealtimeTrader()
        trader.status()
    elif args.run:
        trader = RealtimeTrader()
        trader.run()
    else:
        # 기본: 실시간 모니터링 실행
        trader = RealtimeTrader()
        trader.run()
