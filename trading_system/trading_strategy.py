#!/usr/bin/env python3
"""
자동 매매 시스템 - 트레이딩 전략 모듈
트레이더 마크 📊
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from enum import Enum
import json
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class Action(Enum):
    """트레이딩 액션"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"

@dataclass
class TradeSignal:
    """트레이딩 신호"""
    ticker: str
    action: Action
    price: float
    confidence: float  # 0.0 ~ 1.0
    reason: str
    timestamp: datetime
    quantity: Optional[int] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class TradingStrategy:
    """트레이딩 전략 베이스 클래스"""

    def __init__(self, name: str, risk_level: float = 0.02):
        self.name = name
        self.risk_level = risk_level  # 포지션당 최대 손실 비율
        self.signals = []

    def analyze(self, data: pd.DataFrame, ticker: str) -> TradeSignal:
        """데이터 분석 및 트레이딩 신호 생성"""
        raise NotImplementedError

    def calculate_position_size(self, account_balance: float, entry_price: float,
                              stop_loss: float) -> int:
        """리스크 기반 포지션 사이즈 계산"""
        risk_amount = account_balance * self.risk_level
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share <= 0:
            return 0

        position_size = int(risk_amount / risk_per_share)
        return max(1, position_size)  # 최소 1주

class MovingAverageCrossover(TradingStrategy):
    """이동평균선 크로스오버 전략"""

    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__(name=f"MA_Crossover_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window

    def analyze(self, data: pd.DataFrame, ticker: str) -> TradeSignal:
        if len(data) < self.long_window:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=data['Close'].iloc[-1],
                confidence=0.0,
                reason="데이터 부족",
                timestamp=datetime.now()
            )

        # 이동평균 계산
        short_ma = data['Close'].rolling(window=self.short_window).mean()
        long_ma = data['Close'].rolling(window=self.long_window).mean()

        current_price = data['Close'].iloc[-1]
        prev_short_ma = short_ma.iloc[-2]
        prev_long_ma = long_ma.iloc[-2]
        curr_short_ma = short_ma.iloc[-1]
        curr_long_ma = long_ma.iloc[-1]

        # 크로스오버 확인
        golden_cross = (prev_short_ma <= prev_long_ma) and (curr_short_ma > curr_long_ma)
        death_cross = (prev_short_ma >= prev_long_ma) and (curr_short_ma < curr_long_ma)

        # RSI 확인 (과매수/과매도)
        rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50

        if golden_cross and rsi < 70:  # 골든크로스 + 과매수 아닐 때
            stop_loss = data['Close'].rolling(window=20).min().iloc[-1]
            confidence = min(0.8, (70 - rsi) / 50)  # RSI가 낮을수록 신뢰도 높음

            return TradeSignal(
                ticker=ticker,
                action=Action.BUY,
                price=current_price,
                confidence=confidence,
                reason=f"골든크로스 발생 (단기MA{self.short_window} > 장기MA{self.long_window}), RSI: {rsi:.1f}",
                timestamp=datetime.now(),
                stop_loss=stop_loss
            )

        elif death_cross and rsi > 30:  # 데드크로스 + 과매도 아닐 때
            take_profit = data['Close'].rolling(window=20).max().iloc[-1]
            confidence = min(0.8, (rsi - 30) / 50)  # RSI가 높을수록 신뢰도 높음

            return TradeSignal(
                ticker=ticker,
                action=Action.SELL,
                price=current_price,
                confidence=confidence,
                reason=f"데드크로스 발생 (단기MA{self.short_window} < 장기MA{self.long_window}), RSI: {rsi:.1f}",
                timestamp=datetime.now(),
                take_profit=take_profit
            )

        else:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=current_price,
                confidence=0.3,
                reason=f"신호 없음, RSI: {rsi:.1f}",
                timestamp=datetime.now()
            )

class RSIMeanReversion(TradingStrategy):
    """RSI 평균회귀 전략"""

    def __init__(self, oversold: int = 30, overbought: int = 70):
        super().__init__(name=f"RSI_MeanReversion_{oversold}_{overbought}")
        self.oversold = oversold
        self.overbought = overbought

    def analyze(self, data: pd.DataFrame, ticker: str) -> TradeSignal:
        if 'RSI' not in data.columns or len(data) < 14:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=data['Close'].iloc[-1],
                confidence=0.0,
                reason="RSI 데이터 없음",
                timestamp=datetime.now()
            )

        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        prev_rsi = data['RSI'].iloc[-2] if len(data) > 1 else current_rsi

        # 과매도 구매 신호
        if current_rsi < self.oversold and prev_rsi >= self.oversold:
            stop_loss = current_price * 0.95  # 5% 손절
            confidence = (self.oversold - current_rsi) / self.oversold

            return TradeSignal(
                ticker=ticker,
                action=Action.BUY,
                price=current_price,
                confidence=min(0.9, confidence),
                reason=f"RSI 과매도 구간 진입 ({current_rsi:.1f} < {self.oversold})",
                timestamp=datetime.now(),
                stop_loss=stop_loss
            )

        # 과매수 매도 신호
        elif current_rsi > self.overbought and prev_rsi <= self.overbought:
            take_profit = current_price * 1.05  # 5% 익절
            confidence = (current_rsi - self.overbought) / (100 - self.overbought)

            return TradeSignal(
                ticker=ticker,
                action=Action.SELL,
                price=current_price,
                confidence=min(0.9, confidence),
                reason=f"RSI 과매수 구간 진입 ({current_rsi:.1f} > {self.overbought})",
                timestamp=datetime.now(),
                take_profit=take_profit
            )

        else:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=current_price,
                confidence=0.4,
                reason=f"RSI 중립 구간 ({current_rsi:.1f})",
                timestamp=datetime.now()
            )

class BollingerBandStrategy(TradingStrategy):
    """볼린저밴드 전략"""

    def __init__(self):
        super().__init__(name="Bollinger_Band_Strategy")

    def analyze(self, data: pd.DataFrame, ticker: str) -> TradeSignal:
        if 'BB_upper' not in data.columns or 'BB_lower' not in data.columns:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=data['Close'].iloc[-1],
                confidence=0.0,
                reason="볼린저밴드 데이터 없음",
                timestamp=datetime.now()
            )

        current_price = data['Close'].iloc[-1]
        bb_upper = data['BB_upper'].iloc[-1]
        bb_lower = data['BB_lower'].iloc[-1]
        bb_middle = data['BB_middle'].iloc[-1]

        # 밴드 폭 확인 (변동성)
        bb_width = data['BB_width'].iloc[-1] if 'BB_width' in data.columns else 0

        # 하단 터치 시 매수
        if current_price <= bb_lower:
            stop_loss = bb_lower * 0.98
            confidence = 0.7 if bb_width > 0.1 else 0.5  # 변동성 높을수록 신뢰도 높음

            return TradeSignal(
                ticker=ticker,
                action=Action.BUY,
                price=current_price,
                confidence=confidence,
                reason=f"볼린저밴드 하단 터치 (가격: {current_price:.0f}, 하단: {bb_lower:.0f})",
                timestamp=datetime.now(),
                stop_loss=stop_loss
            )

        # 상단 터치 시 매도
        elif current_price >= bb_upper:
            take_profit = bb_upper * 1.02
            confidence = 0.7 if bb_width > 0.1 else 0.5

            return TradeSignal(
                ticker=ticker,
                action=Action.SELL,
                price=current_price,
                confidence=confidence,
                reason=f"볼린저밴드 상단 터치 (가격: {current_price:.0f}, 상단: {bb_upper:.0f})",
                timestamp=datetime.now(),
                take_profit=take_profit
            )

        else:
            return TradeSignal(
                ticker=ticker,
                action=Action.HOLD,
                price=current_price,
                confidence=0.3,
                reason=f"볼린저밴드 중간 구간",
                timestamp=datetime.now()
            )

class StrategyManager:
    """전략 매니저 - 여러 전략 통합 관리"""

    def __init__(self):
        self.strategies = []
        self.weights = {}  # 전략별 가중치

    def add_strategy(self, strategy: TradingStrategy, weight: float = 1.0):
        """전략 추가"""
        self.strategies.append(strategy)
        self.weights[strategy.name] = weight

    def analyze_all(self, data: pd.DataFrame, ticker: str) -> List[TradeSignal]:
        """모든 전략으로 분석"""
        signals = []

        for strategy in self.strategies:
            signal = strategy.analyze(data, ticker)
            signals.append(signal)

        return signals

    def get_consensus_signal(self, signals: List[TradeSignal]) -> TradeSignal:
        """전략 합의 신호 생성"""
        if not signals:
            return TradeSignal(
                ticker="",
                action=Action.HOLD,
                price=0,
                confidence=0.0,
                reason="신호 없음",
                timestamp=datetime.now()
            )

        # 액션별 투표
        action_votes = {}
        weighted_confidence = {}

        for signal in signals:
            action = signal.action
            weight = self.weights.get(signal.ticker, 1.0)

            if action not in action_votes:
                action_votes[action] = 0
                weighted_confidence[action] = 0

            action_votes[action] += weight
            weighted_confidence[action] += signal.confidence * weight

        # 가장 많은 투표를 받은 액션 선택
        best_action = max(action_votes.items(), key=lambda x: x[1])[0]
        total_weight = sum(action_votes.values())

        if total_weight > 0:
            avg_confidence = weighted_confidence[best_action] / action_votes[best_action]
        else:
            avg_confidence = 0.5

        # 첫 번째 신호 정보 사용 (티커, 가격 등)
        base_signal = signals[0]

        return TradeSignal(
            ticker=base_signal.ticker,
            action=best_action,
            price=base_signal.price,
            confidence=min(0.95, avg_confidence),
            reason=f"전략 합의: {best_action.value} ({len([s for s in signals if s.action == best_action])}/{len(signals)}개 전략 동의)",
            timestamp=datetime.now()
        )

def test_strategies():
    """전략 테스트"""
    print("=" * 50)
    print("트레이더 마크 📊 - 트레이딩 전략 테스트")
    print("=" * 50)

    # 샘플 데이터 생성 (테스트용)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)

    sample_data = pd.DataFrame({
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)

    # 기술적 지표 추가
    from data_collector import DataCollector
    collector = DataCollector()
    sample_data = collector.add_technical_indicators(sample_data)

    # 전략 생성
    ma_strategy = MovingAverageCrossover(short_window=5, long_window=20)
    rsi_strategy = RSIMeanReversion(oversold=30, overbought=70)
    bb_strategy = BollingerBandStrategy()

    # 전략 매니저 설정
    manager = StrategyManager()
    manager.add_strategy(ma_strategy, weight=1.0)
    manager.add_strategy(rsi_strategy, weight=0.8)
    manager.add_strategy(bb_strategy, weight=0.7)

    # 분석 실행
    print("\n개별 전략 분석 결과:")
    individual_signals = manager.analyze_all(sample_data, "TEST")

    for i, signal in enumerate(individual_signals):
        strategy_name = manager.strategies[i].name if i < len(manager.strategies) else "알 수 없음"
        print(f"- {strategy_name}: {signal.action.value} (신뢰도: {signal.confidence:.2f})")
        print(f"  이유: {signal.reason}")

    # 합의 신호
    consensus = manager.get_consensus_signal(individual_signals)
    print(f"\n합의 신호: {consensus.action.value} (신뢰도: {consensus.confidence:.2f})")
    print(f"이유: {consensus.reason}")

    # 포지션 사이즈 계산 예시
    account_balance = 10000000  # 1000만원
    entry_price = sample_data['Close'].iloc[-1]
    stop_loss = entry_price * 0.95

    position_size = ma_strategy.calculate_position_size(
        account_balance, entry_price, stop_loss
    )

    print(f"\n포지션 사이즈 계산:")
    print(f"계좌 잔고: {account_balance:,.0f}원")
    print(f"진입 가격: {entry_price:,.0f}원")
    print(f"손절 가격: {stop_loss:,.0f}원")
    print(f"권장 포지션: {position_size}주")
    print(f"투자 금액: {position_size * entry_price:,.0f}원")

    print("\n" + "=" * 50)
    print("전략 테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    test_strategies()