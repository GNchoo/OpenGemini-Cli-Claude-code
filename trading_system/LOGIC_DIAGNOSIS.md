# 트레이딩 시스템 로직 충돌 진단 리포트
**작성일**: 2026-02-20 16:10
**현재 프로필**: ALL_IN
**현재 자본**: ~49,700원 (초기 대비 손실 발생 중)

## 🚨 발견된 주요 문제점

### 1. **Position 기반 손익절 vs ALL_IN 최소 순이익 충돌**
**문제**: 
- `Position` 객체는 생성 시 `RISK_CONFIG` 기반으로 고정 손절가/익절가를 설정
- ALL_IN 모드에서도 이 값들이 설정되어 `monitor_positions()`에서 체크됨
- 하지만 이 손익절은 **수수료를 고려하지 않음**

**코드 위치**:
```python
# Position.__init__()
cfg = RISK_CONFIG.get(strategy, RISK_CONFIG["MODERATE"])
self.stop_loss   = entry_price * (1 - cfg["stop_loss"])     # 3% 하락
self.take_profit = entry_price * (1 + cfg["take_profit"])   # 0.5% 상승
```

**충돌 시나리오**:
1. BTC를 99,850,000원에 매수 (16,626원어치)
2. Position.take_profit = 99,850,000 * 1.005 = 100,349,250원
3. 가격이 100,000,000원 도달 → take_profit 미달이지만
4. `monitor_positions()`가 아닌 다른 경로(AI_SIGNAL)로 매도 시도
5. 실제 순이익 = -7.9원 (수수료 때문)

### 2. **monitor_positions() 경로의 수수료 미고려**
**문제**:
```python
def monitor_positions(self, current_prices: dict):
    for symbol, pos in list(self.positions.items()):
        price  = current_prices.get(symbol, pos.entry_price)
        reason = pos.should_close(price)  # ← 수수료 체크 없음
        if reason:
            self.execute_sell(symbol, price, reason)
```

**execute_sell()에서 ALL_IN 필터 적용되지만**:
- `reason`이 'TAKE_PROFIT'이면 ALL_IN 필터 통과
- 하지만 실제로는 수수료 차감하면 손실일 수 있음

### 3. **AI_SIGNAL 과다 발생**
**현재 설정**:
- `min_conf`: 0.60 (60%)
- AI 에이전트들이 60% 이상 합의하면 매도 신호

**로그 분석**:
- SELL 신호가 초당 여러 번 발생 (90-100% 신뢰도)
- 하지만 대부분 필터에 걸려 실제 매도는 안 됨
- 이는 **CPU/메모리 낭비 + 로그 오염**

### 4. **최소 보유시간 충돌**
**현재 설정**:
- ALL_IN: 120초 (2분)
- 하지만 16:01:49 SELL → 16:01:51 BUY 같은 패턴 보임
- 2초 간격으로 매도→매수 발생

**원인**:
- 최소 보유시간은 AI_SIGNAL 경로에만 적용
- monitor_positions()의 TAKE_PROFIT/STOP_LOSS는 즉시 실행

### 5. **중복 필터 로직**
**AI_SIGNAL 매도 시 필터**:
1. `ai_sell_min_hold_sec` 체크 (120초)
2. SCALP이면 `net_pnl_after_fee > 0` 체크
3. ALL_IN이면 `expected_net_profit_krw >= min_net_profit_krw` 체크

**execute_sell() 진입 후 필터**:
1. ALL_IN이면 다시 `expected_net_profit_krw >= min_net_profit_krw` 체크

→ **중복 체크로 인한 혼란**

### 6. **동적 전략 전환 문제**
**코드**:
```python
vol = self.vol_calc.update(symbol, prices)
strategy = self.vol_calc.suggest_strategy(vol)
if strategy != self.current_strategy:
    self.current_strategy = strategy  # AGGRESSIVE/MODERATE/CONSERVATIVE 전환
```

**문제**:
- 프로필은 ALL_IN인데, `current_strategy`는 변동성에 따라 AGGRESSIVE 등으로 변함
- Position 생성 시 이 `current_strategy`를 사용 → 손익절 기준이 잘못 설정됨

## 📊 거래 패턴 분석 (최근 20건)

| 시간 | 종목 | 동작 | 손익 | 사유 |
|------|------|------|------|------|
| 16:03:56 | XRP | SELL | -7.9원 | AI_SIGNAL |
| 16:03:51 | BTC | SELL | -9.8원 | AI_SIGNAL |
| 16:02:00 | ETH | SELL | +0.0원 | AI_SIGNAL |
| 16:01:52 | XRP | SELL | -7.9원 | AI_SIGNAL |
| 16:01:49 | BTC | SELL | -0.3원 | AI_SIGNAL |
| 15:59:33 | XRP | SELL | -15.9원 | AI_SIGNAL |

**패턴**: 
- 모든 매도가 AI_SIGNAL
- 대부분 손실 (-0.3원 ~ -15.9원)
- 수수료(편도 ~8원)를 고려하면 당연한 결과

## 🎯 핵심 문제 요약

1. **ALL_IN 모드에서 Position 기반 손익절이 여전히 작동**
   - 수수료 미고려로 손실 청산 발생
   
2. **최소 보유시간이 일부 경로에서만 적용**
   - monitor_positions()는 즉시 청산

3. **AI 신호 신뢰도가 너무 낮음 (60%)**
   - 빈번한 매도 신호 → 수수료 누적

4. **중복/충돌하는 필터 로직**
   - 코드 가독성 저하, 유지보수 어려움

5. **동적 전략 전환이 프로필과 섞임**
   - ALL_IN 설정이 AGGRESSIVE 전략으로 오버라이드

## 🛠️ 제안 솔루션

### 즉시 조치 (손실 방지)
1. **ALL_IN 모드에서 monitor_positions() 비활성화**
   - Position 기반 손익절 무시
   - 오직 최소 순이익 필터만 사용

2. **AI 신뢰도 상향**
   - 60% → 80% 이상으로 조정
   - 잦은 매도 방지

3. **최소 보유시간 강화**
   - ALL_IN: 120초 → 300초 (5분)
   - 수수료 회수 가능한 최소 시간 확보

### 근본 해결 (리팩토링)
1. **프로필별 명확한 로직 분리**
   ```python
   if self.profile_name == 'ALL_IN':
       # ALL_IN 전용 로직 (수수료 중심)
   elif self.profile_name == 'SCALP':
       # SCALP 전용 로직 (초단타)
   else:
       # 일반 프로필 로직
   ```

2. **단일 매도 결정 함수**
   ```python
   def should_sell(self, symbol, price, reason) -> bool:
       """모든 매도 조건을 여기서 통합 체크"""
       # 1. 최소 보유시간
       # 2. 프로필별 수익 조건
       # 3. 비상 상황 (EMERGENCY)
   ```

3. **동적 전략 vs 프로필 분리**
   - `current_strategy`: 변동성 기반 (리스크 관리용)
   - `profile_name`: 사용자 선택 (매매 방식)
   - 두 개를 명확히 분리하고 우선순위 정립

## 📌 임시 긴급 조치 제안

**즉시 실행 가능한 최소 변경**:
```python
# monitor_positions() 수정
def monitor_positions(self, current_prices: dict):
    # ALL_IN은 Position 기반 손익절 스킵
    if self.profile_name == 'ALL_IN':
        return
    
    for symbol, pos in list(self.positions.items()):
        # ... 기존 로직
```

**AI 신뢰도 조정**:
```python
'ALL_IN': {
    'min_conf': 0.80,  # 60% → 80%
    'ai_sell_min_hold_sec': 300,  # 120초 → 300초
}
```

## 🔍 검증 방법

수정 후 다음을 확인:
1. ✅ 2분 이내 매도 발생하지 않는지
2. ✅ 손실 매도가 발생하지 않는지
3. ✅ 로그에서 "보류" 메시지 정상 출력
4. ✅ 최소 30분 운영 후 수익률 체크

---

**결론**: 현재 시스템은 여러 로직이 충돌하여 의도하지 않은 손실 청산이 반복되고 있습니다. 
긴급 조치로 ALL_IN 모드의 Position 기반 손익절을 비활성화하고, AI 신뢰도를 높이는 것을 권장합니다.
