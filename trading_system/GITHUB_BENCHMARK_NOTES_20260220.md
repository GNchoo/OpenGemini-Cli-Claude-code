# GitHub 레퍼런스 조사 메모 (2026-02-20)

## 확인한 상위 프로젝트(스타 기준)
- freqtrade/freqtrade (⭐ 46k+)
- microsoft/qlib (⭐ 37k+)
- mementum/backtrader (⭐ 20k+)
- nautechsystems/nautilus_trader (⭐ 20k+)
- QuantConnect/Lean (⭐ 16k+)
- polakowo/vectorbt (⭐ 6k+)

## 참고한 리스크 관리 패턴
(Freqtrade 문서 중심)
1. **StoplossGuard**: 일정 시간 내 손절 횟수 초과 시 신규 진입 잠금
2. **CooldownPeriod**: 청산 직후 재진입 금지(과매매 방지)
3. **MaxDrawdown Guard**: 손실 구간에서 강제 휴식
4. **Trailing/동적 스탑**: 수익 구간에서 리스크 축소

## 우리 시스템 반영
- `realtime_trader_v2.py`
  - 쿨다운 5분
  - 최근 1시간 손절 3회 시 30분 전역 잠금
  - 피크 대비 DD 12% 도달 시 30분 전역 잠금
  - 최소 보유 10분은 유지하되, 손절/익절은 즉시 실행(잠금 예외)
- 실전 기본 전략은 `ACTIVE_STRATEGY="B"` 유지

## 추가 반영 (수익 중심 투자방식 튜닝)
- **레짐 필터**: 하락 추세(DOWNTREND)에서는 신규 매수 차단
- **레인지장 필터**: RANGE에서는 고신뢰(>=70%) 신호만 진입
- **동적 진입 강도**: 신뢰도 낮거나 XRP 고변동 구간은 AGGRESSIVE 진입 제한
- **트레일링 스탑**: +1.5% 수익 구간부터 고점기준 1.0% 추적으로 수익 보호

## 다음 개선 제안
- 변동성(ATR) 기반 동적 포지션 사이징 고도화
- 거래 시간대 필터(유동성 낮은 구간 회피)
- B전략 성과 기반 자동 A/B 전환 로직
