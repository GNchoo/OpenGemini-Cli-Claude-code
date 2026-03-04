#!/usr/bin/env python3
"""
트레이더 마크 📊 - 통합 실시간 모니터링 시스템
WebSocket 실시간 스트림 + 변동성 분석 + AI 신호 + 긴급 정지
"""

import time
import threading
import statistics
from datetime import datetime
from typing import Optional

from volatility_monitor import (
    VolatilityCalculator,
    EmergencyStopManager,
    TechnicalSignalGenerator,
    APIRateManager,
    THRESHOLDS,
)
from websocket_client import get_client, TickerData, OrderbookData, DEFAULT_SYMBOLS


class IntegratedMonitor:
    """
    WebSocket + 변동성 분석 + 긴급 정지 통합 모니터링
    """

    def __init__(self, symbols: list = None, simulate: bool = True):
        self.symbols   = symbols or DEFAULT_SYMBOLS
        self.simulate  = simulate

        # 서브 모듈
        self.ws        = get_client(self.symbols, simulate=simulate)
        self.vol_calc  = VolatilityCalculator()
        self.emergency = EmergencyStopManager()
        self.signals   = TechnicalSignalGenerator()
        self.api_mgr   = APIRateManager()

        # 현재 전략
        self.current_strategy = "MODERATE"
        self._strategy_lock   = threading.Lock()

        # 거래 신호 큐
        self.signal_queue: list[dict] = []
        self._sig_lock = threading.Lock()

        # 통계
        self.stats = {
            "tickers_received":   0,
            "orderbooks_received": 0,
            "signals_generated":  0,
            "strategy_changes":   0,
            "emergency_triggers": 0,
            "alerts":             [],
        }

        print("=" * 70)
        print("트레이더 마크 📊 - 통합 실시간 모니터링 시스템")
        print("=" * 70)
        mode = "시뮬레이션" if simulate else "실제 업비트 연결"
        print(f"모드: {mode}")
        print(f"심볼: {', '.join(self.symbols)}")
        print()

    # ── 콜백 핸들러 ────────────────────────────────────────

    def _handle_ticker(self, ticker: TickerData):
        """가격 틱 처리 (WebSocket 이벤트)"""
        self.stats["tickers_received"] += 1

        prices = self.ws.get_price_history(ticker.symbol, 20)
        if len(prices) < 5:
            return

        # 변동성 계산
        vol      = self.vol_calc.update(ticker.symbol, prices)
        strategy = self.vol_calc.suggest_strategy(vol)

        # 전략 전환 감지
        with self._strategy_lock:
            if strategy != self.current_strategy:
                old = self.current_strategy
                self.current_strategy = strategy
                self.stats["strategy_changes"] += 1
                self._alert("STRATEGY",
                    f"전략 전환 {old} → {strategy} "
                    f"| {ticker.symbol} 변동성 {vol:.2%}")

        # 긴급 정지 체크 (포트폴리오 손실은 별도 REST로 조회)
        triggered = self.emergency.check(
            self.vol_calc.cache,
            portfolio_loss_pct=0.0,   # 실전에서는 accounts API
            daily_drop=max(0, -ticker.change_rate),
        )
        if triggered and self.stats["emergency_triggers"] == 0:
            self.stats["emergency_triggers"] += 1
            self._alert("CRITICAL",
                f"긴급 정지! 이유: {self.emergency.reason}")

        # 기술적 신호 생성 (20틱마다)
        if self.stats["tickers_received"] % 20 == 0:
            sig = self.signals.analyze(ticker.symbol, prices, vol)
            if sig["confidence"] >= 0.65:
                self.stats["signals_generated"] += 1
                with self._sig_lock:
                    self.signal_queue.append({
                        "symbol":     ticker.symbol,
                        "price":      ticker.price,
                        "signal":     sig["signal"],
                        "confidence": sig["confidence"],
                        "reason":     sig["reason"],
                        "strategy":   strategy,
                        "timestamp":  datetime.now(),
                    })
                self._alert("SIGNAL",
                    f"{ticker.symbol} {sig['signal']} "
                    f"신뢰도 {sig['confidence']:.0%} | {sig['reason']}")

    def _handle_orderbook(self, ob: OrderbookData):
        """호가 처리 (WebSocket 이벤트)"""
        self.stats["orderbooks_received"] += 1

        # 스프레드 이상 감지
        if ob.spread_pct > 0.1:
            self._alert("WARNING",
                f"{ob.symbol} 스프레드 이상: {ob.spread_pct:.3f}% "
                f"(매도 {ob.best_ask:,.0f} / 매수 {ob.best_bid:,.0f})")

    def _alert(self, level: str, msg: str):
        """알림 출력 및 저장"""
        icons = {
            "CRITICAL": "🚨", "WARNING": "⚠️",
            "SIGNAL":   "📈", "STRATEGY": "🔄",
            "INFO":     "📊",
        }
        ts   = datetime.now().strftime("%H:%M:%S")
        icon = icons.get(level, "🔔")
        line = f"  [{ts}] {icon} [{level}] {msg}"
        print(line)
        self.stats["alerts"].append({"ts": ts, "level": level, "msg": msg})

    # ── 상태 출력 ───────────────────────────────────────────

    def _print_status(self, elapsed: float):
        ws_stats = self.ws.stats()
        print(f"\n{'─'*70}")
        print(f"  📊 통합 모니터 [{datetime.now().strftime('%H:%M:%S')}] "
              f"경과 {elapsed:.0f}초 | 전략: {self.current_strategy}")
        print(f"{'─'*70}")
        print(f"  {'심볼':<12} {'가격':>14} {'변동성':>8} {'전략':<16}")
        print(f"  {'─'*55}")

        for sym in self.symbols:
            price = self.ws.get_price(sym)
            vol   = self.vol_calc.get(sym)
            strat = self.vol_calc.suggest_strategy(vol)
            p_str = f"{price:,.0f}원" if price else "수신 대기"
            print(f"  {sym:<12} {p_str:>14} {vol:>7.2%}  {strat}")

        print(f"\n  📡 WebSocket | 메시지 {ws_stats['msg_count']}개 "
              f"| {ws_stats['msg_per_sec']:.1f}개/초")
        print(f"  📊 신호 {self.stats['signals_generated']}개 "
              f"| 전략 전환 {self.stats['strategy_changes']}회 "
              f"| 긴급 정지 {self.stats['emergency_triggers']}회")

        # 대기 중인 신호 출력
        with self._sig_lock:
            if self.signal_queue:
                print(f"\n  🎯 대기 신호:")
                for sig in self.signal_queue[-3:]:
                    print(f"    [{sig['timestamp'].strftime('%H:%M:%S')}] "
                          f"{sig['symbol']} {sig['signal']} "
                          f"({sig['confidence']:.0%}) @ {sig['price']:,.0f}원")

        if self.emergency.active:
            print(f"\n  🚨 긴급 정지 활성화: {self.emergency.reason}")

    # ── 최종 리포트 ─────────────────────────────────────────

    def _print_final(self, duration: float):
        ws = self.ws.stats()
        print(f"\n{'='*70}")
        print(f"  트레이더 마크 📊 - 통합 모니터링 최종 리포트")
        print(f"{'='*70}")
        print(f"  ⏱️  실행 시간     : {duration:.0f}초")
        print(f"  📡 WebSocket    : {ws['msg_count']}개 수신 ({ws['msg_per_sec']:.1f}개/초)")
        print(f"  🔌 REST API     : {self.api_mgr.stats()['total']}회 (보조 용도)")
        print(f"  📈 티커 이벤트  : {self.stats['tickers_received']}개")
        print(f"  📖 호가 이벤트  : {self.stats['orderbooks_received']}개")
        print(f"  📊 신호 생성    : {self.stats['signals_generated']}개")
        print(f"  🔄 전략 전환    : {self.stats['strategy_changes']}회")
        print(f"  🚨 긴급 정지    : {self.stats['emergency_triggers']}회")
        print(f"  🔔 총 알림      : {len(self.stats['alerts'])}개")

        # API 절약 계산
        saved = ws["msg_count"]
        pmin  = saved / max(duration / 60, 0.01)
        print(f"\n  💰 REST API 절약:")
        print(f"    WebSocket 메시지: {saved}개 → REST 호출 {saved}회 절약")
        print(f"    분당 절약: {pmin:.0f}회 (업비트 제한 {pmin/600*100:.1f}% 절약)")

        print(f"\n  🎯 최종 전략: {self.current_strategy}")
        if self.current_strategy == "AGGRESSIVE":
            print(f"    포지션 1.0% | 손절 3.0% | 일 최대 100회")
        elif self.current_strategy == "MODERATE":
            print(f"    포지션 0.5% | 손절 2.0% | 일 최대 50회")
        elif self.current_strategy == "CONSERVATIVE":
            print(f"    포지션 0.2% | 손절 1.0% | 일 최대 20회")
        else:
            print(f"    거래 중지 | 포지션 청산")

        print(f"\n  🚀 다음 단계:")
        print(f"    1. 업비트 REST API 실제 연동")
        print(f"    2. AI 합의 시스템 통합")
        print(f"    3. 자동 주문 실행 모듈")
        print(f"    4. 3월 16일 실전 투자 준비")
        print(f"{'='*70}")

    # ── 메인 실행 ───────────────────────────────────────────

    def start(self, duration: int = 60):
        """통합 모니터링 시작"""
        # WebSocket 콜백 등록
        self.ws.on_ticker    = self._handle_ticker
        self.ws.on_orderbook = self._handle_orderbook

        # WebSocket 연결
        tick_interval = 0.5 if self.simulate else None
        if self.simulate:
            self.ws.connect(tick_interval=tick_interval)
        else:
            self.ws.connect()

        print(f"✅ 스트림 연결 완료\n")

        start_wall = time.time()
        last_report = -1

        try:
            while time.time() - start_wall < duration:
                elapsed = time.time() - start_wall
                slot    = int(elapsed) // 20

                if slot > last_report:
                    last_report = slot
                    self._print_status(elapsed)

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n  ⏹️  사용자 중단")

        self.ws.disconnect()
        self._print_final(time.time() - start_wall)


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    monitor = IntegratedMonitor(simulate=True)
    monitor.start(duration=60)
