# AI 트레이딩 베스트 프랙티스 참고 자료

**작성일**: 2026-02-20 16:25
**출처**: Freqtrade, Jesse, QuantConnect 등 주요 오픈소스 프로젝트

---

## 주요 프로젝트 파라미터 비교

### Freqtrade (가장 인기 있는 오픈소스 봇)
**최소 수익률 (Minimal ROI)**:
- 60분 보유: +1.0%
- 30분 보유: +2.0%
- 20분 보유: +3.0%
- 즉시: +4.0%

**손절 (Stoploss)**: -10%

**신호 신뢰도**: 전략마다 다르지만 일반적으로 60-70%

**최소 보유 시간**: 대부분 전략에서 5-15분

**수수료 고려**:
```python
# Freqtrade 기본 설정
fee = 0.001  # 0.1% (업비트보다 낮음)
minimal_profit = fee * 2  # 최소 0.2% 목표
```

### Jesse (Python 백테스팅 프레임워크)
**리스크/리워드 비율**: 최소 1:2 권장
- 손실 -1% 감수 → 수익 +2% 기대

**승률 기대치**: 
- 리스크/리워드 1:2 → 승률 40% 이상 필요
- 리스크/리워드 1:3 → 승률 30% 이상 가능

**Kelly Criterion** 활용:
```
최적 포지션 크기 = (승률 × 평균이익 - (1-승률) × 평균손실) / 평균이익
```

### QuantConnect/Lean
**리스크 관리**:
- 일일 최대 손실: 계좌의 2-5%
- 포지션당 리스크: 계좌의 0.5-2%

**신호 검증**:
- 백테스트 승률 50% 이상
- Sharpe Ratio 1.0 이상

---

## 소액 계좌 (5만원) 최적 설정

### 현재 문제점
- **최소 순이익 30원**: 너무 작음 (수수료의 약 3배에 불과)
- **신뢰도 80%**: 너무 높아서 거래 기회 적음
- **최소 보유 300초**: 적절하지만 유연성 부족

### 권장 설정 (베스트 프랙티스 기반)

#### ALL_IN 프로필
```python
'ALL_IN': {
    'risk_scale': 1.0,
    'min_conf': 0.70,  # 70% (80% → 70%)
    'max_order_ratio': 0.98,
    'max_symbol_cap_ratio': 1/3,
    'ai_sell_min_hold_sec': 600,  # 10분 (300초 → 600초)
    'min_net_profit_krw': 100,  # 100원 (30원 → 100원)
    'risk_reward_ratio': 2.0,  # 손실 1 : 수익 2
}
```

**근거**:
- 신뢰도 70%: Freqtrade 평균값, 적절한 거래 기회 확보
- 최소 보유 10분: 수수료 회수 + 추세 확인 시간
- 최소 순이익 100원: 수수료(~8원 편도)의 약 12배, 안전 마진
- 리스크/리워드 2.0: Jesse 권장 최소값

#### SCALP 프로필
```python
'SCALP': {
    'risk_scale': 1.0,
    'min_conf': 0.65,  # 65% (60% → 65%)
    'scalp_take_profit': 0.0050,  # 0.5% (0.3% → 0.5%)
    'scalp_trail_arm': 0.0030,  # 0.3%
    'scalp_trail_gap': 0.0020,  # 0.2%
    'scalp_time_exit_min': 15,  # 15분 (40분 → 15분)
    'max_order_ratio': 0.60,
    'ai_sell_min_hold_sec': 180,  # 3분 (30초 → 180초)
    'min_net_profit_krw': 50,  # 50원
}
```

**근거**:
- 익절 0.5%: 수수료 0.1% 제외해도 0.4% 순이익
- 최소 보유 3분: 초단타지만 과도한 회전 방지
- 시간 청산 15분: Freqtrade 스캘핑 평균값

#### 일반 프로필 (BALANCED)
```python
'BALANCED': {
    'risk_scale': 1.0,
    'min_conf': 0.65,  # 65% (60% → 65%)
    'max_order_ratio': 0.60,
    'ai_sell_min_hold_sec': 900,  # 15분 (120초 → 900초)
    'min_net_profit_krw': 150,  # 150원
    'stop_loss': 0.03,  # -3%
    'take_profit': 0.06,  # +6% (리스크/리워드 1:2)
}
```

---

## AI 신호 엔진 개선 방향

### 1. 동적 신뢰도 조정
**현재**: 고정 임계값 (70-85%)

**개선**:
```python
def calculate_dynamic_confidence(strategy, recent_win_rate):
    base = {'AGGRESSIVE': 0.70, 'MODERATE': 0.75, 'CONSERVATIVE': 0.85}
    threshold = base[strategy]
    
    # 최근 승률이 높으면 임계값 하향 (더 많은 기회)
    if recent_win_rate > 0.60:
        threshold -= 0.05
    # 최근 승률이 낮으면 임계값 상향 (더 신중)
    elif recent_win_rate < 0.40:
        threshold += 0.05
    
    return min(max(threshold, 0.60), 0.90)
```

### 2. 리스크/리워드 비율 체크
**추가 로직**:
```python
def check_risk_reward(entry_price, stop_loss, take_profit):
    risk = entry_price - stop_loss
    reward = take_profit - entry_price
    ratio = reward / risk if risk > 0 else 0
    
    # 최소 1:2 비율 요구
    return ratio >= 2.0
```

### 3. 시장 상황별 가중치 조정
**추가 로직**:
```python
def adjust_agent_weights(volatility, trend):
    # 고변동성: Risk_Manager 가중치 증가
    if volatility > 0.03:
        risk_manager.weight = 2.0
    
    # 강한 추세: Trend followers 가중치 증가
    if abs(trend) > 0.02:
        ma_expert.weight = 1.5
```

### 4. 백테스팅 결과 반영
**추가 필요**:
```python
class PerformanceTracker:
    def __init__(self):
        self.win_rate = 0.5
        self.avg_profit = 0.0
        self.trades = []
    
    def update(self, trade):
        self.trades.append(trade)
        # 최근 20거래 기준
        recent = self.trades[-20:]
        wins = [t for t in recent if t['pnl'] > 0]
        self.win_rate = len(wins) / len(recent)
```

---

## 즉시 적용 권장 사항

### Phase 1: 파라미터 조정 (안전)
1. ALL_IN 신뢰도: 80% → 70%
2. ALL_IN 최소 순이익: 30원 → 100원
3. ALL_IN 최소 보유: 300초 → 600초

### Phase 2: AI 로직 개선 (중급)
1. 동적 신뢰도 조정 구현
2. 리스크/리워드 체크 추가
3. 성과 추적 시스템 구현

### Phase 3: 고급 최적화 (장기)
1. Kelly Criterion 포지션 사이징
2. 머신러닝 기반 신호 개선
3. Multi-timeframe 분석

---

## 참고 문헌

- **Freqtrade**: https://github.com/freqtrade/freqtrade
  - 설정 예시: docs/configuration.md
  
- **Jesse**: https://github.com/jesse-ai/jesse
  - 전략 예시: examples/
  
- **QuantConnect**: https://github.com/QuantConnect/Lean
  - 알고리즘 라이브러리: Algorithm/

- **Backtrader**: https://github.com/mementum/backtrader
  - 전략 패턴: docs/strategies/

---

**결론**: 
현재 시스템은 너무 보수적 (신뢰도 80%, 순이익 30원)이어서 거래 기회가 적고,
발생해도 수익이 미미합니다. 업계 표준에 맞춰 조정 필요합니다.
