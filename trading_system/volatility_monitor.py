#!/usr/bin/env python3
"""
트레이더 마크 📊 - 실시간 변동성 모니터링 모듈
실시간 대응 빈도: 긴급 3초 / 가격 5초 / 변동성 10초 / 포트폴리오 30초 / 분석 60초
"""

import time
import random
import statistics
import threading
from datetime import datetime
from collections import deque


# ─────────────────────────────────────────────────────────────
# 설정값
# ─────────────────────────────────────────────────────────────
FREQUENCIES = {
    "emergency":  3,   # 긴급 감지
    "price":      5,   # 가격 확인
    "volatility": 10,  # 변동성 계산
    "portfolio":  30,  # 포트폴리오
    "analysis":   60,  # 기술적 분석
}

# 변동성 임계값
THRESHOLDS = {
    "low":     0.03,   # 3% 이하  → AGGRESSIVE
    "medium":  0.05,   # 3~5%    → MODERATE
    "high":    0.07,   # 5~7%    → CONSERVATIVE
    "extreme": 0.10,   # 7% 이상 → EMERGENCY STOP
}

# 업비트 API 제한
UPBIT_LIMIT_PER_MINUTE = 600
UPBIT_LIMIT_PER_SECOND = 10

# 모니터링 대상 심볼
SYMBOLS = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA"]

# 기준 가격 (시뮬레이션용)
BASE_PRICES = {
    "KRW-BTC": 99_500_000,
    "KRW-ETH": 2_930_000,
    "KRW-XRP": 2_160,
    "KRW-ADA": 1_850,
}


# ─────────────────────────────────────────────────────────────
# API 제한 관리자
# ─────────────────────────────────────────────────────────────
class APIRateManager:
    """업비트 API 호출 횟수 관리"""

    def __init__(self):
        self.total = 0
        self.minute_calls = 0
        self.minute_reset_at = time.time()
        self._lock = threading.Lock()

    def call(self, endpoint: str = "") -> bool:
        with self._lock:
            now = time.time()
            # 1분 경과 시 분당 카운터 리셋
            if now - self.minute_reset_at >= 60:
                self.minute_calls = 0
                self.minute_reset_at = now

            # 제한 초과 방지 (안전 마진 10%)
            if self.minute_calls >= UPBIT_LIMIT_PER_MINUTE * 0.9:
                time.sleep(0.5)

            self.total += 1
            self.minute_calls += 1
            return True

    def stats(self) -> dict:
        with self._lock:
            elapsed_min = max((time.time() - self.minute_reset_at) / 60, 0.001)
            rate = self.minute_calls / elapsed_min
            return {
                "total": self.total,
                "minute_calls": self.minute_calls,
                "rate_per_min": rate,
                "limit_pct": rate / UPBIT_LIMIT_PER_MINUTE * 100,
            }


# ─────────────────────────────────────────────────────────────
# 가격 데이터 수집기
# ─────────────────────────────────────────────────────────────
class PriceCollector:
    """실시간 가격 수집 및 저장 (최근 200개 유지)"""

    def __init__(self):
        self.history: dict[str, deque] = {s: deque(maxlen=200) for s in SYMBOLS}
        self.current: dict[str, float] = dict(BASE_PRICES)
        self._lock = threading.Lock()

    def update(self, symbol: str, price: float):
        with self._lock:
            self.current[symbol] = price
            self.history[symbol].append((datetime.now(), price))

    def get_prices(self, symbol: str, n: int = 20) -> list:
        with self._lock:
            return [p for _, p in list(self.history[symbol])[-n:]]

    def get_change(self, symbol: str) -> float:
        """직전 가격 대비 변화율"""
        prices = self.get_prices(symbol, 2)
        if len(prices) < 2 or prices[-2] == 0:
            return 0.0
        return (prices[-1] - prices[-2]) / prices[-2]

    def simulate_tick(self, symbol: str) -> float:
        """가격 틱 시뮬레이션 (실제 API 연동 전)"""
        base = self.current.get(symbol, BASE_PRICES[symbol])
        # 최근 변동성이 높으면 더 큰 변화
        vol = random.uniform(0.001, 0.008)
        change = random.gauss(0, vol)
        new_price = base * (1 + change)
        self.update(symbol, new_price)
        return new_price


# ─────────────────────────────────────────────────────────────
# 변동성 계산기
# ─────────────────────────────────────────────────────────────
class VolatilityCalculator:
    """ATR 기반 변동성 계산기"""

    def __init__(self):
        self.cache: dict[str, float] = {s: 0.02 for s in SYMBOLS}

    def calculate(self, prices: list) -> float:
        """표준편차 기반 변동성 계산 (ATR 근사)"""
        if len(prices) < 2:
            return 0.02
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                   for i in range(1, len(prices)) if prices[i-1] != 0]
        if not returns:
            return 0.02
        try:
            return statistics.stdev(returns) if len(returns) > 1 else abs(returns[0])
        except statistics.StatisticsError:
            return 0.02

    def update(self, symbol: str, prices: list):
        vol = self.calculate(prices)
        self.cache[symbol] = vol
        return vol

    def get(self, symbol: str) -> float:
        return self.cache.get(symbol, 0.02)

    def suggest_strategy(self, volatility: float) -> str:
        if volatility < THRESHOLDS["low"]:
            return "AGGRESSIVE"
        elif volatility < THRESHOLDS["medium"]:
            return "MODERATE"
        elif volatility < THRESHOLDS["high"]:
            return "CONSERVATIVE"
        else:
            return "EMERGENCY_STOP"

    def describe(self, volatility: float) -> str:
        if volatility < THRESHOLDS["low"]:
            return "낮음 (정상)"
        elif volatility < THRESHOLDS["medium"]:
            return "보통 (주의)"
        elif volatility < THRESHOLDS["high"]:
            return "높음 (경고)"
        else:
            return "극단적 (위험)"


# ─────────────────────────────────────────────────────────────
# 긴급 정지 매니저
# ─────────────────────────────────────────────────────────────
class EmergencyStopManager:
    """긴급 정지 조건 감지 및 실행"""

    def __init__(self):
        self.active = False
        self.reason = None
        self.triggered_at = None
        self.consecutive_losses = 0
        self._lock = threading.Lock()

    def check(self, vol_cache: dict, portfolio_loss_pct: float, daily_drop: float) -> bool:
        with self._lock:
            if self.active:
                return True

            reason = None

            # 조건 1: 극단적 변동성
            max_vol = max(vol_cache.values()) if vol_cache else 0
            if max_vol >= THRESHOLDS["extreme"]:
                reason = f"극단적 변동성 {max_vol:.2%}"

            # 조건 2: 포트폴리오 5% 이상 손실
            elif portfolio_loss_pct >= 0.05:
                reason = f"포트폴리오 손실 {portfolio_loss_pct:.2%}"

            # 조건 3: 일일 시장 10% 이상 하락
            elif daily_drop >= 0.10:
                reason = f"시장 폭락 {daily_drop:.2%}"

            # 조건 4: 연속 손실 5회 이상
            elif self.consecutive_losses >= 5:
                reason = f"연속 손실 {self.consecutive_losses}회"

            if reason:
                self.active = True
                self.reason = reason
                self.triggered_at = datetime.now()
                return True

            return False

    def reset(self):
        with self._lock:
            self.active = False
            self.reason = None
            self.triggered_at = None
            self.consecutive_losses = 0


# ─────────────────────────────────────────────────────────────
# 기술적 신호 생성기
# ─────────────────────────────────────────────────────────────
class TechnicalSignalGenerator:
    """기술적 지표 기반 신호 생성"""

    def analyze(self, symbol: str, prices: list, volatility: float) -> dict:
        if len(prices) < 20:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "데이터 부족"}

        # 이동평균선 (MA5, MA20)
        ma5  = statistics.mean(prices[-5:])  if len(prices) >= 5  else prices[-1]
        ma20 = statistics.mean(prices[-20:]) if len(prices) >= 20 else prices[-1]
        current = prices[-1]

        # RSI 근사값
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains  = [c for c in changes if c > 0]
        losses = [-c for c in changes if c < 0]
        avg_gain = statistics.mean(gains)  if gains  else 0
        avg_loss = statistics.mean(losses) if losses else 0.001
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

        # 신호 결정
        reasons = []
        bullish_score = 0
        bearish_score = 0

        if ma5 > ma20:
            bullish_score += 1
            reasons.append("MA5 > MA20 (상승)")
        else:
            bearish_score += 1
            reasons.append("MA5 < MA20 (하락)")

        if rsi < 30:
            bullish_score += 2
            reasons.append(f"RSI {rsi:.1f} 과매도")
        elif rsi > 70:
            bearish_score += 2
            reasons.append(f"RSI {rsi:.1f} 과매수")

        if current > ma20:
            bullish_score += 1
        else:
            bearish_score += 1

        # 변동성 높으면 신뢰도 감소
        confidence_adj = 1.0 - min(volatility / THRESHOLDS["extreme"], 0.5)

        if bullish_score > bearish_score + 1:
            return {
                "signal": "BUY",
                "confidence": round(min(0.9, 0.6 + bullish_score * 0.1) * confidence_adj, 2),
                "reason": " | ".join(reasons),
                "rsi": round(rsi, 1),
                "ma5": round(ma5, 0),
                "ma20": round(ma20, 0),
            }
        elif bearish_score > bullish_score + 1:
            return {
                "signal": "SELL",
                "confidence": round(min(0.9, 0.6 + bearish_score * 0.1) * confidence_adj, 2),
                "reason": " | ".join(reasons),
                "rsi": round(rsi, 1),
                "ma5": round(ma5, 0),
                "ma20": round(ma20, 0),
            }
        else:
            return {
                "signal": "HOLD",
                "confidence": round(0.4 * confidence_adj, 2),
                "reason": "중립 구간",
                "rsi": round(rsi, 1),
            }


# ─────────────────────────────────────────────────────────────
# 메인 모니터링 시스템
# ─────────────────────────────────────────────────────────────
class RealtimeVolatilityMonitor:
    """실시간 변동성 모니터링 시스템 (멀티스레드)"""

    def __init__(self):
        self.api         = APIRateManager()
        self.prices      = PriceCollector()
        self.volatility  = VolatilityCalculator()
        self.emergency   = EmergencyStopManager()
        self.signals     = TechnicalSignalGenerator()

        self.running = False
        self.threads = []
        self.alerts: list[dict] = []
        self.portfolio_loss = 0.0
        self.daily_drop = 0.0
        self._alert_lock = threading.Lock()

        # 성과 통계
        self.stats = {
            "strategy_changes": 0,
            "emergency_stops": 0,
            "signals_generated": 0,
            "alerts_total": 0,
        }
        self.current_strategy = "MODERATE"

        print("=" * 70)
        print("트레이더 마크 📊 - 실시간 변동성 모니터링 시스템")
        print("=" * 70)
        print("\n📡 모니터링 빈도:")
        for task, sec in FREQUENCIES.items():
            total_ph = 3600 / sec
            pct = (total_ph / 60) / UPBIT_LIMIT_PER_MINUTE * 100
            print(f"  • {task:<12}: {sec:>2}초마다 | {total_ph:>5.0f}회/시간 | 제한 대비 {pct:.1f}%")

        total_ph = sum(3600 / s for s in FREQUENCIES.values())
        total_pct = (total_ph / 60) / UPBIT_LIMIT_PER_MINUTE * 100
        print(f"\n  {'합계':<12}: {'':>5} | {total_ph:>5.0f}회/시간 | 제한 대비 {total_pct:.1f}%")
        print()

    # ── 알림 헬퍼 ──────────────────────────────────────────
    def _alert(self, level: str, msg: str, **kwargs):
        with self._alert_lock:
            entry = {"ts": datetime.now(), "level": level, "msg": msg, **kwargs}
            self.alerts.append(entry)
            self.stats["alerts_total"] += 1

        icons = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "📊", "SIGNAL": "📈"}
        icon = icons.get(level, "🔔")
        ts = entry["ts"].strftime("%H:%M:%S")
        print(f"  [{ts}] {icon} [{level}] {msg}")

    # ── 스레드: 긴급 감지 (3초) ────────────────────────────
    def _thread_emergency(self):
        while self.running:
            start = time.time()
            try:
                self.api.call("ticker")

                # 폭락 시뮬레이션 (0.5% 확률)
                if random.random() < 0.005:
                    self.daily_drop = random.uniform(0.10, 0.20)
                    self._alert("CRITICAL", f"시장 폭락 감지 {self.daily_drop:.2%} ↓")

                triggered = self.emergency.check(
                    self.volatility.cache,
                    self.portfolio_loss,
                    self.daily_drop,
                )
                if triggered and self.stats["emergency_stops"] == 0:
                    self.stats["emergency_stops"] += 1
                    self._alert("CRITICAL",
                        f"긴급 정지 활성화 | 이유: {self.emergency.reason}")

            except Exception as e:
                print(f"  [긴급 스레드 오류] {e}")

            elapsed = time.time() - start
            time.sleep(max(0, FREQUENCIES["emergency"] - elapsed))

    # ── 스레드: 가격 확인 (5초) ────────────────────────────
    def _thread_price(self):
        while self.running:
            start = time.time()
            try:
                for symbol in SYMBOLS:
                    self.api.call("ticker")
                    price = self.prices.simulate_tick(symbol)
                    change = self.prices.get_change(symbol)

                    # 3% 이상 급변 시 알림
                    if abs(change) >= 0.03:
                        direction = "↑" if change > 0 else "↓"
                        self._alert("WARNING",
                            f"{symbol} 급변 {change:+.2%} {direction} | 현재: {price:,.0f}원")

            except Exception as e:
                print(f"  [가격 스레드 오류] {e}")

            elapsed = time.time() - start
            time.sleep(max(0, FREQUENCIES["price"] - elapsed))

    # ── 스레드: 변동성 계산 (10초) ─────────────────────────
    def _thread_volatility(self):
        while self.running:
            start = time.time()
            try:
                for symbol in SYMBOLS:
                    self.api.call("candles")
                    prices = self.prices.get_prices(symbol, 20)
                    vol = self.volatility.update(symbol, prices)
                    strategy = self.volatility.suggest_strategy(vol)

                    # 전략 전환 감지
                    if strategy != self.current_strategy:
                        old = self.current_strategy
                        self.current_strategy = strategy
                        self.stats["strategy_changes"] += 1
                        self._alert("WARNING",
                            f"전략 전환 {old} → {strategy} | {symbol} 변동성 {vol:.2%}")

                    # 높은 변동성 알림
                    if vol >= THRESHOLDS["high"]:
                        self._alert("WARNING",
                            f"{symbol} 변동성 {vol:.2%} ({self.volatility.describe(vol)})")

            except Exception as e:
                print(f"  [변동성 스레드 오류] {e}")

            elapsed = time.time() - start
            time.sleep(max(0, FREQUENCIES["volatility"] - elapsed))

    # ── 스레드: 포트폴리오 (30초) ──────────────────────────
    def _thread_portfolio(self):
        while self.running:
            start = time.time()
            try:
                self.api.call("accounts")

                # 손실 시뮬레이션 (실전에서는 API로 실제 잔고 조회)
                self.portfolio_loss = random.uniform(0, 0.04)

                if self.portfolio_loss >= 0.05:
                    self._alert("WARNING",
                        f"포트폴리오 손실 {self.portfolio_loss:.2%} | 리스크 관리 필요")

            except Exception as e:
                print(f"  [포트폴리오 스레드 오류] {e}")

            elapsed = time.time() - start
            time.sleep(max(0, FREQUENCIES["portfolio"] - elapsed))

    # ── 스레드: 기술적 분석 (60초) ─────────────────────────
    def _thread_analysis(self):
        while self.running:
            start = time.time()
            try:
                for symbol in SYMBOLS:
                    self.api.call("candles")
                    prices = self.prices.get_prices(symbol, 50)
                    vol = self.volatility.get(symbol)
                    result = self.signals.analyze(symbol, prices, vol)

                    if result["confidence"] >= 0.7:
                        self.stats["signals_generated"] += 1
                        self._alert("SIGNAL",
                            f"{symbol} {result['signal']} | 신뢰도 {result['confidence']:.0%} | {result['reason']}")

            except Exception as e:
                print(f"  [분석 스레드 오류] {e}")

            elapsed = time.time() - start
            time.sleep(max(0, FREQUENCIES["analysis"] - elapsed))

    # ── 상태 출력 ───────────────────────────────────────────
    def _print_status(self, elapsed: float):
        print(f"\n{'─'*70}")
        print(f"  📊 상태 리포트 [{datetime.now().strftime('%H:%M:%S')}] "
              f"| 경과 {elapsed:.0f}초 | 전략: {self.current_strategy}")
        print(f"{'─'*70}")

        # 변동성 테이블
        print(f"  {'심볼':<12} {'가격':>14} {'변동성':>8} {'설명':<16} {'전략'}")
        print(f"  {'─'*60}")
        for sym in SYMBOLS:
            price = self.prices.current.get(sym, 0)
            vol   = self.volatility.get(sym)
            desc  = self.volatility.describe(vol)
            strat = self.volatility.suggest_strategy(vol)
            print(f"  {sym:<12} {price:>14,.0f} {vol:>7.2%}  {desc:<16} {strat}")

        # API 통계
        s = self.api.stats()
        print(f"\n  🔌 API | 총 {s['total']}회 | 분당 {s['rate_per_min']:.1f}회 "
              f"| 제한 대비 {s['limit_pct']:.1f}%")

        # 긴급 상태
        if self.emergency.active:
            print(f"\n  🚨 긴급 정지 활성화: {self.emergency.reason}")
        else:
            print(f"\n  ✅ 시스템 정상 운영 중 | 전략 전환: {self.stats['strategy_changes']}회 "
                  f"| 신호: {self.stats['signals_generated']}개 "
                  f"| 알림: {self.stats['alerts_total']}개")

    # ── 최종 리포트 ─────────────────────────────────────────
    def _print_final_report(self, duration: float):
        s = self.api.stats()
        avg_vol = statistics.mean(self.volatility.cache.values())

        print(f"\n{'='*70}")
        print(f"  트레이더 마크 📊 - 실시간 모니터링 최종 리포트")
        print(f"{'='*70}")
        print(f"\n  ⏱️  실행 시간  : {duration:.0f}초")
        print(f"  🔌 API 호출   : 총 {s['total']}회 | 분당 {s['rate_per_min']:.1f}회 | 제한 {s['limit_pct']:.1f}%")
        print(f"  📈 평균 변동성: {avg_vol:.2%} → 권장 전략: {self.volatility.suggest_strategy(avg_vol)}")
        print(f"  🔄 전략 전환  : {self.stats['strategy_changes']}회")
        print(f"  📊 신호 생성  : {self.stats['signals_generated']}개")
        print(f"  🔔 알림 총계  : {self.stats['alerts_total']}개")
        print(f"  🚨 긴급 정지  : {self.stats['emergency_stops']}회")

        print(f"\n  ✅ 평가:")
        pct = s["limit_pct"]
        if pct < 15:
            print(f"    API 사용률 {pct:.1f}% — 매우 안정적, 빈도 확장 가능")
        elif pct < 40:
            print(f"    API 사용률 {pct:.1f}% — 정상 운영 중")
        else:
            print(f"    API 사용률 {pct:.1f}% — 빈도 조정 권장")

        print(f"\n  🚀 다음 단계:")
        print(f"    1. WebSocket으로 실시간 가격 수신 (API 호출 70% 감소)")
        print(f"    2. 업비트 API 실제 연동")
        print(f"    3. AI 합의 시스템 통합")
        print(f"    4. 3월 16일 실전 투자 준비")
        print(f"{'='*70}")

    # ── 모니터링 시작 ───────────────────────────────────────
    def start(self, duration: int = 60):
        print(f"\n🚀 실시간 모니터링 시작 ({duration}초)\n")
        self.running = True

        thread_funcs = [
            ("긴급감지",   self._thread_emergency),
            ("가격확인",   self._thread_price),
            ("변동성계산", self._thread_volatility),
            ("포트폴리오", self._thread_portfolio),
            ("기술분석",   self._thread_analysis),
        ]

        for name, func in thread_funcs:
            t = threading.Thread(target=func, name=name, daemon=True)
            t.start()
            self.threads.append(t)
            print(f"  ✅ {name} 스레드 시작")

        print()

        start_wall = time.time()
        last_report = 0

        try:
            while time.time() - start_wall < duration:
                elapsed = time.time() - start_wall

                # 20초마다 상태 출력
                if int(elapsed) // 20 > last_report:
                    last_report = int(elapsed) // 20
                    self._print_status(elapsed)

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n  ⏹️  사용자 중단")

        self.running = False
        for t in self.threads:
            t.join(timeout=2)

        self._print_final_report(time.time() - start_wall)


# ─────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    monitor = RealtimeVolatilityMonitor()
    monitor.start(duration=60)   # 60초 테스트 실행
