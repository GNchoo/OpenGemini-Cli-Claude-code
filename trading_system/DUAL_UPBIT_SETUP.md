# 듀얼 업비트(A/B) 실전 세팅

## 1) .env 키 입력
`trading_system/.env`에서 아래 값을 채우세요.

- `UPBIT_ACCESS_KEY_A`, `UPBIT_SECRET_KEY_A` (기존 계정)
- `UPBIT_ACCESS_KEY_B`, `UPBIT_SECRET_KEY_B` (추가 계정)

현재 B 계정은 AccessKey만 입력되어 있고 SecretKey가 비어 있습니다.

## 2) 연결 테스트
```bash
cd /home/fallman/.openclaw/workspace/trading_system
python3 test_dual_upbit_accounts.py
```

성공 기준:
- `✅ A 계정 인증 성공`
- `✅ B 계정 인증 성공`

## 3) 실전 트레이더 실행
```bash
cd /home/fallman/.openclaw/workspace/trading_system
python3 realtime_trader_v2.py
```

## 성능 개선 적용 내역 (어제 결과 반영)
- A 전략(손절 과다) → `ACTIVE_STRATEGY="B"`로 실전 기본 전환
- 진입 신뢰도 0.60 → 0.70
- 시간당 최대 거래 4회 → 2회
- 최소 보유 5분 → 10분
- 전략 엔진 `ma20_not_down` 버그 수정
