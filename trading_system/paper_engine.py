#!/usr/bin/env python3
"""
트레이더 마크 📊 - 모의투자 엔진
매일 실행하면 누적 성과가 쌓이는 구조
실제 업비트 시세 데이터 사용 (공개 API)
"""

import json, os, sys, time, random, statistics
from datetime import datetime, timedelta
from pathlib import Path

from ai_signal_engine   import AISignalEngine
from volatility_monitor import VolatilityCalculator, EmergencyStopManager, THRESHOLDS
from upbit_live_client  import UpbitLiveClient

# ─────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000      # 초기 자본 100만원
SYMBOLS         = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
DATA_FILE       = "paper_portfolio.json"   # 누적 상태 저장

RISK_CONFIG = {
    # pos_pct: 자본 대비 투자 비율
    # sl: 손절 비율 (Stop Loss)
    # tp: 익절 비율 (Take Profit)
    # 핵심 원칙: tp > sl*2 (익절이 손절의 2배 이상, Risk:Reward = 1:2)
    # 수수료 왕복 0.10% → tp는 최소 0.5% 이상이어야 의미있음
    # 긴급 수정 (2026-02-20): SL 확대 + 포지션 축소 (승률 0% 대응)
    "AGGRESSIVE":   {"pos_pct": 0.06, "sl": 0.035, "tp": 0.070},  # 자본 6%, 손절 3.5%, 익절 7% (2026-02-22 조정)
    "MODERATE":     {"pos_pct": 0.04, "sl": 0.025, "tp": 0.050},  # 자본 4%, 손절 2.5%, 익절 5%
    "CONSERVATIVE": {"pos_pct": 0.02, "sl": 0.020, "tp": 0.040},  # 자본 2%, 손절 2%, 익절 4%
}
MIN_ORDER = 5_000   # 최소 주문금액 5,000원 (수수료 의미있는 수준)
MAX_DAILY_LOSS = 0.05   # 일일 최대 손실 5%

# ── 업비트 수수료 설정 ──────────────────────────────────────
# KRW 마켓 기본 0.05% (부가세 포함)
# 매수 시: 주문금액의 0.05% 차감
# 매도 시: 매도금액의 0.05% 차감
FEE_RATE = 0.0005   # 0.05%
# 손익분기: 매수+매도 수수료 합산 → 0.10% 이상 상승해야 수익
BEP_RATE = FEE_RATE * 2   # 0.10%


# ─────────────────────────────────────────────────────────────
# 상태 관리 (JSON 파일로 영속성 유지)
# ─────────────────────────────────────────────────────────────
class PaperPortfolio:
    """모의 포트폴리오 — 파일로 상태 유지"""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.data     = self._load()

    def _load(self) -> dict:
        if Path(self.filepath).exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        # 초기화
        return {
            "capital":      INITIAL_CAPITAL,
            "positions":    {},        # {symbol: {entry, volume, sl, tp, strategy}}
            "trade_log":    [],        # 전체 거래 내역
            "daily_log":    [],        # 일별 요약
            "started_at":   datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "peak_capital": INITIAL_CAPITAL,
        }

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # 편의 프로퍼티
    @property
    def capital(self) -> float:
        return self.data["capital"]

    @capital.setter
    def capital(self, v: float):
        self.data["capital"] = v
        if v > self.data["peak_capital"]:
            self.data["peak_capital"] = v

    @property
    def positions(self) -> dict:
        return self.data["positions"]

    def add_trade(self, record: dict):
        self.data["trade_log"].append(record)

    def add_daily(self, summary: dict):
        self.data["daily_log"].append(summary)

    def max_drawdown(self) -> float:
        """최대 낙폭 계산"""
        peak = INITIAL_CAPITAL
        mdd  = 0.0
        for log in self.data["daily_log"]:
            cap = log.get("end_capital", INITIAL_CAPITAL)
            peak = max(peak, cap)
            dd   = (peak - cap) / peak if peak > 0 else 0
            mdd  = max(mdd, dd)
        return mdd


# ─────────────────────────────────────────────────────────────
# 모의투자 엔진
# ─────────────────────────────────────────────────────────────
class PaperEngine:
    """실제 업비트 시세 기반 모의투자 엔진"""

    def __init__(self):
        self.portfolio = PaperPortfolio()
        self.upbit     = UpbitLiveClient()
        self.ai        = AISignalEngine()
        self.vol_calc  = VolatilityCalculator()
        self.emergency = EmergencyStopManager()

        self.today_trades = 0
        self.today_pnl    = 0.0
        self.today_start  = self.portfolio.capital

        print("=" * 70)
        print("트레이더 마크 📊 - 모의투자 엔진")
        print("=" * 70)
        total_return = (self.portfolio.capital / INITIAL_CAPITAL - 1) * 100
        days_running = len(self.portfolio.data["daily_log"])
        print(f"  초기 자본  : {INITIAL_CAPITAL:,.0f}원")
        print(f"  현재 자본  : {self.portfolio.capital:,.0f}원")
        print(f"  누적 수익률: {total_return:+.2f}%")
        print(f"  운영 일수  : {days_running}일")
        print(f"  심볼       : {', '.join(SYMBOLS)}")
        print()

    # ── 실제 시세 가져오기 ──────────────────────────────────
    # 캔들 캐시 (API 호출 최소화)
    _candle_cache: dict = {}
    _cache_time:   dict = {}
    CACHE_TTL = 30   # 30초 캐시

    def fetch_candles(self, symbol: str, count: int = 60) -> list:
        """실제 업비트 5분봉 데이터 가져오기 (캐시 + 속도 제한)"""
        now = time.time()
        # 캐시 유효하면 재사용
        if (symbol in self._candle_cache and
                now - self._cache_time.get(symbol, 0) < self.CACHE_TTL):
            return self._candle_cache[symbol]
        try:
            time.sleep(0.12)   # 초당 8회 이하 유지
            candles = self.upbit.get_candles(symbol, unit=5, count=count)
            prices  = [float(c["trade_price"]) for c in reversed(candles)]
            self._candle_cache[symbol] = prices
            self._cache_time[symbol]   = now
            return prices
        except Exception as e:
            # 캐시 있으면 캐시 반환
            if symbol in self._candle_cache:
                return self._candle_cache[symbol]
            return self._simulate_prices(symbol, count)

    def fetch_current_price(self, symbol: str) -> float:
        """실제 현재가 조회"""
        try:
            return self.upbit.get_current_price(symbol)
        except Exception:
            return self.portfolio.positions.get(symbol, {}).get("entry", 0)

    def _simulate_prices(self, symbol: str, count: int) -> list:
        """API 실패 시 시뮬레이션"""
        base = {"KRW-BTC": 99_500_000, "KRW-ETH": 2_930_000, "KRW-XRP": 2_160}.get(symbol, 1_000_000)
        prices = [base]
        for _ in range(count - 1):
            prices.append(prices[-1] * (1 + random.gauss(0, 0.003)))
        return prices

    # ── 전략 결정 ───────────────────────────────────────────
    def decide_strategy(self, symbol: str, prices: list) -> tuple:
        """변동성 → 전략 결정"""
        vol      = self.vol_calc.update(symbol, prices)
        strategy = self.vol_calc.suggest_strategy(vol)
        return strategy, vol

    # ── 매수/매도 ───────────────────────────────────────────
    def open_position(self, symbol: str, price: float, strategy: str):
        """포지션 진입"""
        if symbol in self.portfolio.positions:
            return

        cfg       = RISK_CONFIG.get(strategy, RISK_CONFIG["MODERATE"])
        order_krw = self.portfolio.capital * cfg["pos_pct"]

        if order_krw < MIN_ORDER or order_krw > self.portfolio.capital:
            return

        # 수수료 차감 후 실제 투자금액 계산
        buy_fee    = order_krw * FEE_RATE        # 매수 수수료
        actual_krw = order_krw - buy_fee         # 수수료 빼고 실제 투자
        volume     = actual_krw / price          # 실제 매수 수량
        self.portfolio.capital -= order_krw      # 수수료 포함 총 차감

        # 손익분기 가격 (매수+매도 수수료 커버)
        bep_price = price * (1 + BEP_RATE)

        self.portfolio.positions[symbol] = {
            "entry":      price,
            "volume":     volume,
            "cost":       order_krw,      # 수수료 포함 총 비용
            "actual_krw": actual_krw,     # 수수료 제외 순 투자
            "buy_fee":    buy_fee,        # 매수 수수료
            "sl":         price * (1 - cfg["sl"]),
            "tp":         price * (1 + cfg["tp"]),
            "bep":        bep_price,      # 손익분기 가격
            "strategy":   strategy,
            "opened_at":  datetime.now().isoformat(),
            "hold_bars":  0,
        }

        print(f"  🟢 BUY  {symbol:12} @ {price:>12,.0f}원  "
              f"({order_krw:,.0f}원 | 수수료 {buy_fee:.1f}원 | BEP {bep_price:,.0f} | "
              f"SL {price*(1-cfg['sl']):,.0f} TP {price*(1+cfg['tp']):,.0f})")

        self.portfolio.add_trade({
            "date":     datetime.now().isoformat(),
            "side":     "BUY",
            "symbol":   symbol,
            "price":    price,
            "volume":   volume,
            "cost":     order_krw,
            "strategy": strategy,
        })
        self.today_trades += 1

    def close_position(self, symbol: str, price: float, reason: str):
        """포지션 청산"""
        if symbol not in self.portfolio.positions:
            return

        pos       = self.portfolio.positions[symbol]
        gross     = pos["volume"] * price        # 매도 전 금액
        sell_fee  = gross * FEE_RATE             # 매도 수수료
        value     = gross - sell_fee             # 수수료 차감 후 실수령액
        total_fee = pos["buy_fee"] + sell_fee    # 왕복 수수료 합계
        profit    = value - pos["cost"]          # 수수료 포함 순손익
        pnl       = profit / pos["cost"]         # 손익률 (수수료 반영)

        self.portfolio.capital += value
        self.today_pnl         += pnl

        icon = "🟢" if profit >= 0 else "🔴"
        print(f"  {icon} SELL {symbol:12} @ {price:>12,.0f}원  "
              f"PnL {pnl:+.2%} ({profit:+,.0f}원) | 수수료 {total_fee:.1f}원 [{reason}]")

        self.portfolio.add_trade({
            "date":      datetime.now().isoformat(),
            "side":      "SELL",
            "symbol":    symbol,
            "price":     price,
            "volume":    pos["volume"],
            "gross":     gross,          # 수수료 전 금액
            "sell_fee":  sell_fee,       # 매도 수수료
            "buy_fee":   pos["buy_fee"], # 매수 수수료
            "total_fee": total_fee,      # 왕복 수수료
            "value":     value,          # 수수료 후 실수령
            "pnl":       pnl,            # 수수료 반영 손익률
            "profit":    profit,         # 수수료 반영 손익(원)
            "reason":    reason,
            "strategy":  pos["strategy"],
        })

        del self.portfolio.positions[symbol]
        self.today_trades += 1

    # ── 포지션 손절/익절 체크 ──────────────────────────────
    def check_exits(self, symbol: str, price: float):
        pos = self.portfolio.positions.get(symbol)
        if not pos:
            return
        if price <= pos["sl"]:
            self.close_position(symbol, price, "STOP_LOSS")
        elif price >= pos["tp"]:
            self.close_position(symbol, price, "TAKE_PROFIT")

    # ── 일일 모의투자 실행 ──────────────────────────────────
    def run_day(self, candle_count: int = 200, interval_sec: float = 0.05):
        """
        하루 분량 모의투자 실행
        실제 5분봉 200개를 한 번에 가져와서 슬라이딩 윈도우로 처리
        200개 × 5분 = 약 16시간 분량
        """
        print(f"\n📅 모의투자 실행: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  자본: {self.portfolio.capital:,.0f}원")
        print("-" * 70)

        # 일일 손실 한도 체크
        daily_loss_pct = (self.today_start - self.portfolio.capital) / self.today_start
        if daily_loss_pct >= MAX_DAILY_LOSS:
            print(f"  ⛔ 일일 손실 한도 도달 ({daily_loss_pct:.2%}) — 오늘 거래 중지")
            self._save_daily_summary()
            return

        # 심볼별 전체 캔들 미리 로드
        print(f"  📡 실제 시세 로드 중...")
        all_prices: dict[str, list] = {}
        for symbol in SYMBOLS:
            prices = self.fetch_candles(symbol, count=200)
            all_prices[symbol] = prices
            print(f"     {symbol}: {len(prices)}개 캔들 로드")
            time.sleep(0.3)

        actual_count = min(candle_count, min(len(p) for p in all_prices.values()))
        print(f"\n  캔들 {actual_count}개 처리 시작 (5분봉 × {actual_count} = {actual_count*5//60}시간)")
        print()

        for i in range(20, actual_count):  # 최소 20개 이후부터 처리
            for symbol in SYMBOLS:
                full_prices   = all_prices[symbol]
                window_prices = full_prices[max(0, i-50):i+1]  # 최대 50봉 윈도우
                if len(window_prices) < 20:
                    continue

                current_price = window_prices[-1]

                # 전략 결정
                strategy, vol = self.decide_strategy(symbol, window_prices)

                # 긴급 정지 체크
                if self.emergency.check(
                    self.vol_calc.cache,
                    abs(min(self.today_pnl, 0)),
                    0.0
                ):
                    if symbol in self.portfolio.positions:
                        self.close_position(symbol, current_price, "EMERGENCY_STOP")
                    continue

                # 손절/익절 체크
                self.check_exits(symbol, current_price)

                # 보유 봉 수 업데이트
                if symbol in self.portfolio.positions:
                    self.portfolio.positions[symbol]["hold_bars"] = \
                        self.portfolio.positions[symbol].get("hold_bars", 0) + 1

                # AI 신호 (3봉마다)
                if i % 3 == 0:
                    decision = self.ai.decide(
                        symbol, window_prices, vol, strategy=strategy
                    )
                    min_conf = {"AGGRESSIVE": 0.55, "MODERATE": 0.60, "CONSERVATIVE": 0.70}.get(strategy, 0.60)

                    if decision["confidence"] >= min_conf:
                        sig = decision["signal"]
                        pos = self.portfolio.positions.get(symbol)
                        if sig == "BUY" and pos is None:
                            self.open_position(symbol, current_price, strategy)
                        elif sig == "SELL" and pos is not None:
                            # 최소 5봉(25분) 이상 보유 후에만 AI SELL 허용
                            if pos.get("hold_bars", 0) >= 5:
                                self.close_position(symbol, current_price, "AI_SELL")

            time.sleep(interval_sec)

            # 진행률 출력 (40봉마다)
            if (i + 1) % 40 == 0:
                positions_str = ", ".join(self.portfolio.positions.keys()) or "없음"
                print(f"  [{i+1:>3}/{actual_count}] 자본 {self.portfolio.capital:,.0f}원 "
                      f"| 포지션: {positions_str}")

        # 마감 시 미청산 포지션 정리
        print(f"\n  📋 마감 시 미청산 포지션 정리:")
        for symbol in list(self.portfolio.positions.keys()):
            price = self.fetch_current_price(symbol)
            if price > 0:
                self.close_position(symbol, price, "DAY_END")

        # 일별 요약 저장
        self._save_daily_summary()

    def _save_daily_summary(self):
        """일별 요약 저장"""
        total_return = (self.portfolio.capital / INITIAL_CAPITAL - 1) * 100
        day_return   = (self.portfolio.capital / self.today_start - 1) * 100

        # 오늘 수수료 합산
        today_str   = datetime.now().strftime("%Y-%m-%d")
        today_sells = [t for t in self.portfolio.data["trade_log"]
                       if t["side"] == "SELL" and t["date"].startswith(today_str)]
        today_fee   = sum(t.get("total_fee", 0) for t in today_sells)

        summary = {
            "date":          today_str,
            "start_capital": self.today_start,
            "end_capital":   self.portfolio.capital,
            "day_return":    day_return,
            "total_return":  total_return,
            "trades":        self.today_trades,
            "day_pnl":       self.today_pnl,
            "total_fee":     today_fee,   # 오늘 납부 수수료
        }

        self.portfolio.add_daily(summary)
        self.portfolio.save()

        print(f"\n{'─'*70}")
        print(f"  📊 오늘 결과:")
        print(f"     시작 자본: {self.today_start:,.0f}원")
        print(f"     종료 자본: {self.portfolio.capital:,.0f}원")
        icon = "🟢" if day_return >= 0 else "🔴"
        print(f"     {icon} 일일 수익률: {day_return:+.2f}%  ({self.portfolio.capital-self.today_start:+,.0f}원)")
        print(f"     누적 수익률: {total_return:+.2f}%")
        print(f"     오늘 거래: {self.today_trades}회")
        print(f"     💸 오늘 수수료: {today_fee:,.1f}원 (왕복 0.10% × {self.today_trades//2}회)")

    # ── 누적 성과 리포트 ────────────────────────────────────
    def print_report(self):
        """전체 누적 성과 리포트"""
        log      = self.portfolio.data["daily_log"]
        trade_log = self.portfolio.data["trade_log"]

        if not log:
            print("  아직 거래 기록이 없습니다.")
            return

        total_return = (self.portfolio.capital / INITIAL_CAPITAL - 1) * 100
        days_run     = len(log)
        mdd          = self.portfolio.max_drawdown()

        # 거래 통계
        sells      = [t for t in trade_log if t["side"] == "SELL"]
        pnls       = [t["pnl"] for t in sells if "pnl" in t]
        wins       = [p for p in pnls if p > 0]
        losses     = [p for p in pnls if p <= 0]
        win_rate   = len(wins) / len(pnls) if pnls else 0
        avg_win    = statistics.mean(wins)   if wins   else 0
        avg_loss   = statistics.mean(losses) if losses else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # 일별 수익률
        daily_returns = [d["day_return"] for d in log]
        profit_days   = sum(1 for r in daily_returns if r > 0)
        loss_days     = sum(1 for r in daily_returns if r <= 0)

        print("=" * 70)
        print("트레이더 마크 📊 - 모의투자 누적 성과 리포트")
        print("=" * 70)

        started = self.portfolio.data.get("started_at", "")[:10]
        print(f"\n📅 기간: {started} ~ {datetime.now().strftime('%Y-%m-%d')} ({days_run}일)")
        print(f"\n💰 자본 현황:")
        print(f"   초기 자본: {INITIAL_CAPITAL:,.0f}원")
        print(f"   현재 자본: {self.portfolio.capital:,.0f}원")
        print(f"   최대 자본: {self.portfolio.data['peak_capital']:,.0f}원")
        icon = "🟢" if total_return >= 0 else "🔴"
        print(f"   {icon} 누적 수익률: {total_return:+.2f}%  ({self.portfolio.capital-INITIAL_CAPITAL:+,.0f}원)")
        print(f"   📉 최대 낙폭: {mdd:.2%}")

        print(f"\n📈 일별 성과:")
        print(f"   수익일: {profit_days}일  손실일: {loss_days}일")
        if daily_returns:
            print(f"   최대 수익일: {max(daily_returns):+.2f}%")
            print(f"   최대 손실일: {min(daily_returns):+.2f}%")
            print(f"   평균 일수익: {statistics.mean(daily_returns):+.2f}%")

        # 수수료 통계
        total_fee  = sum(t.get("total_fee", 0) for t in sells)
        total_gross = sum(t.get("gross", t.get("value",0)) for t in sells)

        print(f"\n🎯 거래 통계:")
        print(f"   총 거래: {len(trade_log)}회  (매수 {len(trade_log)-len(sells)}회 | 매도 {len(sells)}회)")
        if pnls:
            print(f"   승률: {win_rate:.1%}  ({len(wins)}승 {len(losses)}패)")
            print(f"   평균 수익: {avg_win:+.3%}  평균 손실: {avg_loss:+.3%}")
            print(f"   손익비: {profit_factor:.2f}")

        print(f"\n💸 수수료 분석 (KRW 마켓 0.05%):")
        print(f"   총 수수료 납부: {total_fee:,.1f}원")
        print(f"   거래당 평균 수수료: {total_fee/len(sells) if sells else 0:.2f}원")
        print(f"   손익분기 최소 상승폭: {BEP_RATE*100:.2f}% (왕복 수수료 커버)")
        print(f"   수수료가 손익에 미친 영향: {-total_fee:+,.1f}원")

        print(f"\n📅 최근 5일 성과:")
        for d in log[-5:]:
            icon = "🟢" if d["day_return"] >= 0 else "🔴"
            print(f"   {d['date']}  {icon} {d['day_return']:+.2f}%  "
                  f"({d['end_capital']:,.0f}원  거래 {d['trades']}회)")

        # 3월 16일까지 예측
        if days_run > 0 and daily_returns:
            avg_daily = statistics.mean(daily_returns) / 100
            days_left = (datetime(2026, 3, 16) - datetime.now()).days
            projected = self.portfolio.capital * ((1 + avg_daily) ** days_left)
            print(f"\n🔮 3월 16일 예측 (현재 추세 유지 시):")
            print(f"   남은 일수: {days_left}일")
            print(f"   평균 일수익률: {avg_daily*100:+.3f}%")
            print(f"   예상 자본: {projected:,.0f}원  ({(projected/INITIAL_CAPITAL-1)*100:+.1f}%)")

        print("=" * 70)


# ─────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="트레이더 마크 모의투자 엔진")
    parser.add_argument("--report", action="store_true", help="누적 성과 리포트 출력")
    parser.add_argument("--reset",  action="store_true", help="포트폴리오 초기화")
    parser.add_argument("--candles", type=int, default=200, help="처리할 캔들 수 (기본 200)")
    args = parser.parse_args()

    if args.reset:
        if Path(DATA_FILE).exists():
            os.remove(DATA_FILE)
            print("✅ 포트폴리오 초기화 완료")
        return

    engine = PaperEngine()

    if args.report:
        engine.print_report()
        return

    # 모의투자 실행
    engine.run_day(candle_count=args.candles, interval_sec=0.2)
    print()
    engine.print_report()

if __name__ == "__main__":
    main()
