# 트레이딩 시스템 리팩토링 진행 상황
**시작 시간**: 2026-02-20 16:13
**담당 모델**: Claude Sonnet 4.5
**목표**: 충돌하는 로직 분리 및 명확화

## 리팩토링 목표

### 1. 프로필별 매도 로직 완전 분리
- [x] ALL_IN: 수수료 기반 순이익 중심
- [ ] SCALP: 초단타 익절/트레일/시간청산
- [ ] 일반 프로필: Position 기반 손익절

### 2. 단일 매도 결정 함수
- [ ] `should_sell()` 함수 구현
- [ ] 모든 매도 조건 통합

### 3. 동적 전략 vs 프로필 분리
- [ ] `current_strategy`: 변동성 기반 리스크 관리
- [ ] `profile_name`: 사용자 선택 매매 방식
- [ ] 우선순위 명확화

## 작업 단계

### Phase 1: 백업 및 준비 ✅
- [x] 현재 코드 백업
- [x] 진단 리포트 작성 (LOGIC_DIAGNOSIS.md)
- [x] 진행 상황 추적 파일 생성

### Phase 2: 매도 결정 로직 리팩토링
**현재 진행 중**

#### Step 2.1: should_sell() 통합 함수 생성 ✅
- [x] 모든 매도 조건을 하나의 함수로 통합
- [x] 프로필별 분기 명확화 (_should_sell_all_in, _should_sell_scalp, _should_sell_normal)
- [x] 반환값: (should_sell: bool, reason: str)

#### Step 2.2: execute_sell() 단순화 ✅
- [x] 중복 필터 제거
- [x] should_sell() 결과만 사용

#### Step 2.3: monitor_positions() 재설계 ✅
- [x] 프로필별 동작 명확화
- [x] ALL_IN/SCALP은 Position 기반 손익절 비활성화

#### Step 2.4: _on_ticker() 매도 로직 정리 ✅
- [x] 중복 필터 제거
- [x] should_sell()로 통합

### Phase 3: 진입 로직 정리
- [x] execute_buy() 프로필별 분기 (주문 크기는 기존 로직 유지)

### Phase 4: 전략 vs 프로필 분리 ✅
- [x] _get_position_strategy() 헬퍼 함수 추가
- [x] Position 생성 시 프로필 기반 전략 사용
- [x] ALL_IN/SCALP은 MODERATE 고정 (손익절 미사용)
- [x] 일반 프로필은 동적 전략 사용

### Phase 5: 테스트 및 배포 ✅
- [x] 컴파일 체크 ✅
- [x] 서비스 재시작 ✅
- [x] 초기 동작 확인 ✅

## 검증 결과

### 정상 작동 확인
1. ✅ 서비스 시작 성공
2. ✅ 포지션 복원 정상 (BTC 0.00016602)
3. ✅ 매도 보류 메시지 정상 출력
   - 예: "⏸️ 매도 보류 KRW-BTC: MIN_HOLD(24s < 300s)"
4. ✅ SELL 신호 90% 발생해도 실제 매도 안 됨 (80% 미만)

### 로직 변경 요약
- **통합 매도 함수**: should_sell() 구현
- **프로필별 분리**: _should_sell_all_in, _should_sell_scalp, _should_sell_normal
- **중복 제거**: execute_sell()과 _on_ticker()의 중복 필터 제거
- **전략 분리**: Position 생성 시 profile 기반으로 전환

## 백업 정보
**원본 파일**: auto_trader.py (커밋 0be06fc)
**백업 위치**: auto_trader.py.backup-20260220-1613

## 변경 로그

### 2026-02-20 16:13 - Phase 1 완료
- 백업 생성
- 진행 상황 추적 파일 생성

### 2026-02-20 16:14-16:21 - Phase 2-5 완료 ✅
**Phase 2: 매도 결정 로직 리팩토링**
- should_sell() 통합 함수 생성
- 프로필별 _should_sell_xxx() 함수 분리
- execute_sell() 단순화
- monitor_positions() 프로필별 분기
- _on_ticker() 중복 필터 제거

**Phase 4: 전략 vs 프로필 분리**
- _get_position_strategy() 헬퍼 추가
- Position 생성 시 프로필 기반 전략 사용
- ALL_IN/SCALP은 MODERATE 고정

**Phase 5: 배포 및 검증**
- 컴파일 성공
- 서비스 재시작 성공
- 매도 보류 로직 정상 작동 확인

## 리팩토링 완료 ✅

**소요 시간**: 약 7분
**변경 파일**: auto_trader.py
**백업 위치**: auto_trader.py.backup-20260220-1613

### 다음 권장 작업
1. 30분간 실전 모니터링
2. 거래 발생 시 수익률 확인
3. 필요 시 신뢰도 미세 조정 (80% → 75%)
