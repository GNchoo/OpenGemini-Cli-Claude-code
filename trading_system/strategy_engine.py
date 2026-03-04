#!/usr/bin/env python3
"""
트레이더 마크 📊 - 전략 엔진 v2
GitHub 검증 전략 (현실적 조건으로 조정):
  1. MA 크로스오버 (MA5/MA20) - 자체 백테스트 +73% 검증
  2. RSI 과매수/과매도 - 시장 보편 전략
  3. Supertrend (ATR 기반) - freqtrade 커뮤니티 표준
  4. ClucMay 완화 버전 - 원본 대비 진입 조건 현실화

참고:
  https://github.com/freqtrade/freqtrade-strategies (ClucMay, Strategy005)
  자체 백테스트: MA(5,20) +73.62% (삼성전자 6개월)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    action: str        # BUY / SELL / HOLD
    confidence: float  # 0.0 ~ 1.0
    reason: str
    strategy: str


# ── 지표 계산 유틸 ───────────────────────────────────────────

def ema(values: list, period: int) -> list:
    if len(values) < period:
        return [None] * len(values)
    k = 2 / (period + 1)
    result = [None] * (period - 1)
    result.append(sum(values[:period]) / period)
    for v in values[period:]:
        result.append(v * k + result[-1] * (1 - k))
    return result

def sma(values: list, period: int) -> list:
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1:i + 1]) / period)
    return result

def rsi(closes: list, period: int = 14) -> list:
    if len(closes) < period + 1:
        return [None] * len(closes)
    result = [None] * period
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    result.append(100 - 100 / (1 + rs))
    for i in range(period + 1, len(closes)):
        diff = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        result.append(100 - 100 / (1 + rs))
    return result

def bollinger_bands(closes: list, period: int = 20, std_mult: float = 2.0):
    upper, mid, lower = [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper.append(None); mid.append(None); lower.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            m = sum(window) / period
            std = (sum((x - m) ** 2 for x in window) / period) ** 0.5
            mid.append(m)
            upper.append(m + std_mult * std)
            lower.append(m - std_mult * std)
    return upper, mid, lower

def atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
    tr = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    result = [None] * period
    result.append(sum(tr[:period]) / period)
    for i in range(period, len(tr)):
        result.append((result[-1] * (period - 1) + tr[i]) / period)
    return result

def supertrend(highs: list, lows: list, closes: list, period: int = 10, mult: float = 3.0):
    atrs = atr(highs, lows, closes, period)
    hl2  = [(h + l) / 2 for h, l in zip(highs, lows)]
    upper_band = [None] * period
    lower_band = [None] * period
    trend      = [None] * period
    direction  = [None] * period

    for i in range(period, len(closes)):
        if atrs[i] is None:
            upper_band.append(None); lower_band.append(None)
            trend.append(None);      direction.append(None)
            continue
        ub = hl2[i] + mult * atrs[i]
        lb = hl2[i] - mult * atrs[i]
        prev_ub  = upper_band[-1] or ub
        prev_lb  = lower_band[-1] or lb
        if closes[i-1] > prev_ub: ub = max(ub, prev_ub)
        if closes[i-1] < prev_lb: lb = min(lb, prev_lb)
        upper_band.append(ub); lower_band.append(lb)
        prev_dir = direction[-1] or 1
        if prev_dir == -1 and closes[i] > prev_ub:
            direction.append(1);  trend.append(lb)
        elif prev_dir == 1 and closes[i] < prev_lb:
            direction.append(-1); trend.append(ub)
        else:
            direction.append(prev_dir)
            trend.append(lb if prev_dir == 1 else ub)
    return trend, direction

def macd_calc(closes: list, fast: int = 12, slow: int = 26, signal_p: int = 9):
    ef = ema(closes, fast)
    es = ema(closes, slow)
    ml = [f - s if f and s else None for f, s in zip(ef, es)]
    valid = [x for x in ml if x is not None]
    sig = ema(valid, signal_p)
    pad = len(ml) - len(sig)
    sig = [None] * pad + sig
    hist = [m - s if m is not None and s is not None else None for m, s in zip(ml, sig)]
    return ml, sig, hist


# ────────────────────────────────────────────────────────────
# 전략 1: MA 크로스오버 (MA5/MA20)
# 자체 백테스트 검증: +73.62% (삼성전자 6개월)
# 매수: MA5가 MA20 위로 돌파 (골든크로스)
# 매도: MA5가 MA20 아래로 하락 (데드크로스)
# ────────────────────────────────────────────────────────────

def strategy_ma_cross(candles: list) -> Signal:
    if len(candles) < 25:
        return Signal("HOLD", 0.0, f"데이터 부족 ({len(candles)}/25)", "MA_Cross")

    closes = [c.close for c in candles]
    ma5  = sma(closes, 5)
    ma20 = sma(closes, 20)

    cur_ma5  = ma5[-1]
    cur_ma20 = ma20[-1]
    prev_ma5 = ma5[-2]
    prev_ma20 = ma20[-2]

    if None in (cur_ma5, cur_ma20, prev_ma5, prev_ma20):
        return Signal("HOLD", 0.0, "지표 계산 중", "MA_Cross")

    # 골든크로스: MA5가 MA20 위로 돌파
    golden = prev_ma5 <= prev_ma20 and cur_ma5 > cur_ma20
    # 데드크로스: MA5가 MA20 아래로 하락
    dead   = prev_ma5 >= prev_ma20 and cur_ma5 < cur_ma20

    # 크로스 없어도 추세 방향으로 신호 (완화 조건)
    uptrend   = cur_ma5 > cur_ma20
    downtrend = cur_ma5 < cur_ma20
    gap_pct   = abs(cur_ma5 - cur_ma20) / cur_ma20 * 100

    if golden:
        return Signal("BUY", 0.80, f"골든크로스 MA5={cur_ma5:,.0f} > MA20={cur_ma20:,.0f}", "MA_Cross")
    if dead:
        return Signal("SELL", 0.80, f"데드크로스 MA5={cur_ma5:,.0f} < MA20={cur_ma20:,.0f}", "MA_Cross")
    if uptrend:
        conf = min(0.60, 0.30 + gap_pct * 5)
        return Signal("BUY", conf, f"상승 추세 유지 (MA5 MA20 상회 {gap_pct:.2f}%)", "MA_Cross")
    if downtrend:
        conf = min(0.60, 0.30 + gap_pct * 5)
        return Signal("SELL", conf, f"하락 추세 유지 (MA5 MA20 하회 {gap_pct:.2f}%)", "MA_Cross")

    return Signal("HOLD", 0.0, "MA5 ≈ MA20 횡보", "MA_Cross")


# ────────────────────────────────────────────────────────────
# 전략 2: RSI 과매수/과매도
# 매수: RSI < 40 (과매도 진입)
# 매도: RSI > 60 (과매수 청산)
# ────────────────────────────────────────────────────────────

def strategy_rsi(candles: list) -> Signal:
    if len(candles) < 20:
        return Signal("HOLD", 0.0, f"데이터 부족 ({len(candles)}/20)", "RSI")

    closes   = [c.close for c in candles]
    rsi_vals = rsi(closes, 14)
    cur_rsi  = rsi_vals[-1]
    prev_rsi = rsi_vals[-2]

    if cur_rsi is None or prev_rsi is None:
        return Signal("HOLD", 0.0, "RSI 계산 중", "RSI")

    # 과매도: RSI < 40
    if cur_rsi < 40:
        conf = min(0.85, 0.50 + (40 - cur_rsi) * 0.017)
        return Signal("BUY", conf, f"RSI 과매도 {cur_rsi:.1f} < 40", "RSI")

    # 과매수: RSI > 60
    if cur_rsi > 60:
        conf = min(0.85, 0.50 + (cur_rsi - 60) * 0.017)
        return Signal("SELL", conf, f"RSI 과매수 {cur_rsi:.1f} > 60", "RSI")

    return Signal("HOLD", 0.0, f"RSI 중립 {cur_rsi:.1f} (40~60 범위)", "RSI")


# ────────────────────────────────────────────────────────────
# 전략 3: Supertrend (ATR 기반 추세 추종)
# freqtrade 커뮤니티 표준 구현
# 매수: 상승 추세 + 직전 캔들이 하락에서 상승 전환
# 매도: 하락 전환 또는 하락 추세 유지
# ────────────────────────────────────────────────────────────

def strategy_supertrend(candles: list) -> Signal:
    if len(candles) < 20:
        return Signal("HOLD", 0.0, f"데이터 부족 ({len(candles)}/20)", "Supertrend")

    closes = [c.close for c in candles]
    highs  = [c.high  for c in candles]
    lows   = [c.low   for c in candles]

    _, directions = supertrend(highs, lows, closes, period=10, mult=3.0)

    cur_dir  = directions[-1]
    prev_dir = directions[-2] if len(directions) > 1 else cur_dir

    if cur_dir is None or prev_dir is None:
        return Signal("HOLD", 0.0, "계산 중", "Supertrend")

    # 방향 전환 (강한 신호)
    if prev_dir == -1 and cur_dir == 1:
        return Signal("BUY", 0.80, "Supertrend 상승 전환 ↑", "Supertrend")
    if prev_dir == 1 and cur_dir == -1:
        return Signal("SELL", 0.80, "Supertrend 하락 전환 ↓", "Supertrend")

    # 추세 유지 (약한 신호)
    if cur_dir == 1:
        return Signal("BUY", 0.45, "Supertrend 상승 추세 유지", "Supertrend")
    else:
        return Signal("SELL", 0.45, "Supertrend 하락 추세 유지", "Supertrend")


# ────────────────────────────────────────────────────────────
# 전략 4: ClucMay 완화 버전
# 원본: close < EMA100 AND close < BB하단*0.985 (너무 엄격)
# 완화: close < EMA50 AND close < BB하단 (현실적)
# + MACD 음→양 전환 시 추가 매수 신호
# ────────────────────────────────────────────────────────────

def strategy_clucmay(candles: list) -> Signal:
    if len(candles) < 60:
        return Signal("HOLD", 0.0, f"데이터 부족 ({len(candles)}/60)", "ClucMay")

    closes = [c.close for c in candles]

    ema50v       = ema(closes, 50)
    bb_u, bb_m, bb_l = bollinger_bands(closes, 20, 2.0)
    ml, sig, hist    = macd_calc(closes)

    cur   = closes[-1]
    e50   = ema50v[-1]
    bbl   = bb_l[-1]
    bbm   = bb_m[-1]
    h_cur = hist[-1]
    h_prv = hist[-2]

    if None in (e50, bbl, bbm, h_cur, h_prv):
        return Signal("HOLD", 0.0, "지표 계산 중", "ClucMay")

    # 매수: EMA50 아래 AND BB하단 이하 (완화된 조건)
    buy_bb  = cur < e50 and cur < bbl
    # 추가 매수: MACD 음→양 전환
    macd_cross_up = h_prv < 0 and h_cur >= 0

    # 매도: BB 중간선 도달
    sell_bb = cur > bbm

    if buy_bb:
        drop = (bbl - cur) / bbl * 100
        conf = min(0.85, 0.55 + drop * 8)
        return Signal("BUY", conf, f"BB하단 이탈 {drop:.2f}% + EMA50 하회", "ClucMay")

    if macd_cross_up and cur < e50:
        return Signal("BUY", 0.65, f"MACD 상향 돌파 + EMA50 하회", "ClucMay")

    # 매도: BB 상단 돌파 또는 중간선 +1% 이상 (포지션 청산용)
    if cur > bb_u[-1]:
        return Signal("SELL", 0.80, f"BB상단 돌파 (과매수)", "ClucMay")
    if sell_bb and (cur - bbm) / bbm > 0.005:
        rise = (cur - bbm) / bbm * 100
        return Signal("SELL", min(0.75, 0.55 + rise * 5), f"BB중간선 +{rise:.2f}% 충분히 회복", "ClucMay")

    # 현재 위치
    dist = (cur - bbl) / bbl * 100
    return Signal("HOLD", 0.0, f"BB하단 대비 +{dist:.2f}% 위 대기 중", "ClucMay")


# ────────────────────────────────────────────────────────────
# 통합 엔진: 검증형 3전략 (MA + RSI + Supertrend)
# ────────────────────────────────────────────────────────────

def decide(candles: list, min_confidence: float = 0.58) -> dict:
    """A전략(검증형): MA(5,20) + RSI + Supertrend

    원칙:
    - 진입은 보수적으로: 추세(МА) + 추세확인(Supertrend) 동시 충족 필요
    - RSI는 필터로 사용 (과매수면 신규 매수 차단)
    - 청산은 더 민감하게: MA/Supertrend 하락 합의 또는 RSI 과매수
    """
    signals = {
        "MA_Cross":   strategy_ma_cross(candles),
        "RSI":        strategy_rsi(candles),
        "Supertrend": strategy_supertrend(candles),
    }

    ma_sig = signals["MA_Cross"]
    rsi_sig = signals["RSI"]
    st_sig = signals["Supertrend"]

    closes = [c.close for c in candles]
    ma20 = sma(closes, 20)
    ma20_slope_pct = 0.0
    if ma20[-1] is not None and ma20[-4] is not None and ma20[-4] != 0:
        ma20_slope_pct = (ma20[-1] - ma20[-4]) / ma20[-4] * 100

    # 긴급 수정: MA20 상승 추세만 진입 허용 (하락 진입 금지)
    ma20_uptrend = ma20_slope_pct > 0.05  # 최소 0.05% 상승 필요
    ma20_down = ma20_slope_pct < -0.05

    # 신뢰도 계산 (더 보수적으로 재조정)
    buy_conf = (
        ma_sig.confidence * 2.0 +  # MA 가중치 증가 (추세 중시)
        st_sig.confidence * 1.5 +
        (rsi_sig.confidence if rsi_sig.action == "BUY" else 0.30 if rsi_sig.action == "HOLD" else 0.0) * 0.8
    ) / (2.0 + 1.5 + 0.8)

    sell_conf = (
        (ma_sig.confidence if ma_sig.action == "SELL" else 0.0) * 2.0 +
        (st_sig.confidence if st_sig.action == "SELL" else 0.0) * 1.5 +
        (rsi_sig.confidence if rsi_sig.action == "SELL" else 0.30 if rsi_sig.action == "HOLD" else 0.0) * 0.8
    ) / (2.0 + 1.5 + 0.8)

    # 긴급 수정: 더 엄격한 진입 조건 (3개 모두 동의 + MA20 상승)
    buy_ok = (
        ma_sig.action == "BUY" and
        st_sig.action == "BUY" and
        rsi_sig.action == "BUY" and  # RSI도 BUY 신호 필수
        ma20_uptrend  # MA20 상승 추세 필수
    )

    # 반등 진입 조건 강화: RSI 극단 과매도만 허용
    reversal_ok = False  # 당분간 반등 진입 비활성화

    sell_ok = (
        (ma_sig.action == "SELL" and st_sig.action == "SELL" and ma20_down) or
        (rsi_sig.action == "SELL" and ma_sig.action != "BUY")
    )

    sig_info = {k: {"action": v.action, "conf": v.confidence, "reason": v.reason}
                for k, v in signals.items()}

    # 긴급 수정: 진입 신뢰도 기준 대폭 상향 (0.70 이상만 진입)
    if buy_ok and buy_conf >= 0.70:
        reason = f"강한 상승 합의(MA+ST+RSI 모두 BUY) + MA20 상승추세 | conf={buy_conf:.0%}"
        return {"signal": "BUY", "confidence": buy_conf, "reason": reason, "signals": sig_info}

    # 반등 진입 비활성화 (승률 회복될 때까지)
    if reversal_ok and buy_conf >= 0.75:
        reason = f"극단 반등: RSI 과매도 + 추세 확인 | conf={buy_conf:.0%}"
        return {"signal": "BUY", "confidence": buy_conf, "reason": reason, "signals": sig_info}

    # 청산은 기존보다 민감하게 (빠른 손절)
    if sell_ok and sell_conf >= 0.48:
        reason = f"하락/과매수 청산 조건 충족 | conf={sell_conf:.0%}"
        return {"signal": "SELL", "confidence": sell_conf, "reason": reason, "signals": sig_info}

    blockers = []
    if not ma20_uptrend:
        blockers.append(f"MA20 상승부족({ma20_slope_pct:+.3f}%)")
    if rsi_sig.action == "SELL":
        blockers.append("RSI 과매수")
    if ma_sig.action != "BUY" or st_sig.action != "BUY":
        blockers.append("추세 합의 부족")

    return {
        "signal": "HOLD",
        "confidence": 0.0,
        "reason": f"진입보류: {', '.join(blockers[:3]) if blockers else '조건 미달'} | BUY {buy_conf:.0%} / SELL {sell_conf:.0%}",
        "signals": sig_info,
    }


LEGACY_WEIGHTS = {
    "MA_Cross":   1.5,
    "RSI":        1.2,
    "Supertrend": 1.3,
    "ClucMay":    1.0,
}

def decide_b_majority(candles: list, min_confidence: float = 0.55) -> dict:
    """B전략(실험형): 다수결 + ClucMay 포함 가중 투표"""
    signals = {
        "MA_Cross":   strategy_ma_cross(candles),
        "RSI":        strategy_rsi(candles),
        "Supertrend": strategy_supertrend(candles),
        "ClucMay":    strategy_clucmay(candles),
    }

    buy_score = sell_score = 0.0
    total_w = sum(LEGACY_WEIGHTS.values())
    buy_reasons, sell_reasons = [], []

    for name, sig in signals.items():
        w = LEGACY_WEIGHTS[name]
        if sig.action == "BUY":
            buy_score += w * sig.confidence
            buy_reasons.append(f"{name}({sig.confidence:.0%})")
        elif sig.action == "SELL":
            sell_score += w * sig.confidence
            sell_reasons.append(f"{name}({sig.confidence:.0%})")

    buy_conf = buy_score / total_w
    sell_conf = sell_score / total_w

    buy_votes = sum(1 for s in signals.values() if s.action == "BUY")
    sell_votes = sum(1 for s in signals.values() if s.action == "SELL")
    majority_buy = buy_votes >= 2 and buy_votes > sell_votes
    majority_sell = sell_votes >= 2 and sell_votes > buy_votes

    final_buy = (buy_conf >= min_confidence and buy_conf >= sell_conf) or \
                (majority_buy and buy_conf > sell_conf and buy_votes >= 2 and sell_votes == 0)
    final_sell = (sell_conf >= min_confidence and sell_conf > buy_conf) or \
                 (majority_sell and sell_conf > buy_conf and sell_votes >= 2 and buy_votes == 0)

    sig_info = {k: {"action": v.action, "conf": v.confidence, "reason": v.reason}
                for k, v in signals.items()}

    if final_buy and not final_sell:
        conf = max(buy_conf, 0.55 if majority_buy else 0.0)
        return {
            "signal": "BUY",
            "confidence": conf,
            "reason": f"가중:{buy_conf:.0%} 투표:{buy_votes}/4 | " + " + ".join(buy_reasons),
            "signals": sig_info,
        }

    if final_sell and not final_buy:
        conf = max(sell_conf, 0.55 if majority_sell else 0.0)
        return {
            "signal": "SELL",
            "confidence": conf,
            "reason": f"가중:{sell_conf:.0%} 투표:{sell_votes}/4 | " + " + ".join(sell_reasons),
            "signals": sig_info,
        }

    return {
        "signal": "HOLD",
        "confidence": 0.0,
        "reason": f"BUY {buy_conf:.0%}({buy_votes}표) / SELL {sell_conf:.0%}({sell_votes}표) 미달",
        "signals": sig_info,
    }


if __name__ == "__main__":
    import random
    random.seed(42)
    price = 100000.0
    candles = []
    for i in range(200):
        o = price
        h = o * (1 + random.uniform(0, 0.015))
        l = o * (1 - random.uniform(0, 0.015))
        c = random.uniform(l, h)
        v = random.uniform(1000, 5000)
        candles.append(Candle(o, h, l, c, v))
        price = c

    print("=== 전략 엔진 v2 테스트 ===")
    for name, fn in [("MA_Cross", strategy_ma_cross), ("RSI", strategy_rsi),
                     ("Supertrend", strategy_supertrend), ("ClucMay", strategy_clucmay)]:
        r = fn(candles)
        print(f"{name:<12}: {r.action} ({r.confidence:.0%}) - {r.reason}")
    r = decide(candles)
    print(f"\n통합 결정: {r['signal']} ({r['confidence']:.0%}) - {r['reason']}")
