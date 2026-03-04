# 트레이더 마크 📊 - 완전 설정 가이드

## 🚀 빠른 시작 (순서대로 진행)

### 1단계: 시스템 상태 확인 ✅

```bash
cd /home/fallman/.openclaw/workspace/trading_system

# 트레이더 상태 확인
systemctl --user status trader-autotrader.service

# 실시간 로그 확인
journalctl --user -u trader-autotrader.service -f
```

**현재 상태:** ✅ 정상 동작 중

---

### 2단계: Telegram 알림 설정 📱

**중요:** 먼저 Telegram 앱에서 봇에게 메시지를 보내야 합니다!

#### 2-1. 봇과 대화 시작

1. Telegram 앱을 엽니다
2. 다음 링크를 클릭하거나 검색:
   
   **https://t.me/Coin_Trading_Alert_Me_bot**
   
   또는 검색: `@Coin_Trading_Alert_Me_bot`

3. **봇과 대화 시작** 버튼 클릭
4. `/start` 메시지 전송

#### 2-2. Chat ID 설정

봇에게 메시지를 보낸 후:

```bash
./setup_telegram.sh
```

성공하면 테스트 메시지가 Telegram으로 전송됩니다!

#### 2-3. 트레이더 재시작 (알림 활성화)

```bash
systemctl --user restart trader-autotrader.service
```

이제 다음 상황에서 Telegram 알림을 받습니다:
- 🔴 일일 손실 한도 도달 (5%)
- 🟡 연속 3패 이상
- 🟡 미체결 주문 취소
- ℹ️ 큰 손익 발생 (±2% 이상)

---

### 3단계: 일일 리포트 자동화 📊

```bash
./setup_daily_report_cron.sh
```

**설정 내용:**
- 매일 오전 9시 자동 리포트 생성
- Telegram으로 요약 전송
- 파일 저장: `reports/report_YYYY-MM-DD.json`

**수동 리포트 생성:**
```bash
python3 daily_report.py
```

---

### 4단계: 1주일 모니터링 도구 📈

#### 주간 성과 분석
```bash
./weekly_analysis.sh
```

출력 예시:
```
일별 요약:
날짜          거래    손익        승률   
==================================================
2026-02-15   12     +1.23%     66.7%
2026-02-16   8      -0.45%     50.0%
...

주간 종합:
총 거래: 45회
총 손익: +3.21%
주간 승률: 62.2% (28승 17패)
평균 Profit Factor: 1.45
```

#### 슬리피지 분석
```bash
python3 analyze_slippage.py

# 또는 로그에서 직접 확인
journalctl --user -u trader-autotrader.service | grep '슬리피지'
```

#### 연속 손실 대응 확인
```bash
# BUY 차단 로그 확인
journalctl --user -u trader-autotrader.service -f | grep "BUY 차단"

# 포지션 축소 로그 확인
journalctl --user -u trader-autotrader.service -f | grep "연속.*패.*포지션 축소"
```

---

### 5단계: 백테스팅 (선택사항) 🔬

**현재 상태:** 스켈레톤 생성됨

파일: `backtest_engine.py`, `advanced_indicators.py`

**추후 완성 예정:**
- 업비트 candle API 연동
- 과거 3개월 데이터 검증
- 파라미터 최적화

---

## 📋 주요 기능 요약

### ✅ 구현 완료

1. **안전장치**
   - 일일 손실 한도 (5%)
   - 매도 후 재진입 방지 (3분 + 2% 할인)
   - 연속 손실 시 포지션 축소 (3패 → 50%)
   - 미체결 주문 자동 취소 (3분)
   - 점검시간 거래 차단

2. **알림 시스템**
   - Telegram 실시간 알림
   - 우선순위별 분류 (긴급/경고/정보)

3. **성과 분석**
   - 일일 자동 리포트 (매일 09:00)
   - 주간 성과 분석
   - 슬리피지 추적
   - Profit Factor, 승률 계산

4. **거래 최적화**
   - 시세 freshness 검증 (15초)
   - 슬리피지 완충 (95%)
   - API 백오프 (429/400 에러)

---

## 🎯 모니터링 체크리스트

### 매일 확인

- [ ] Telegram 알림 정상 수신
- [ ] 일일 리포트 수신 (09:00)
- [ ] 주요 거래 정상 실행
- [ ] 손실 한도 이내 유지

### 주간 확인

- [ ] 주간 성과 분석 (`./weekly_analysis.sh`)
- [ ] 슬리피지 패턴 확인
- [ ] 연속 손실 대응 효과
- [ ] 승률 및 Profit Factor 검토

### 필요 시 조정

**쿨다운 시간 조정:**
```python
# auto_trader.py 수정
if time_since_sell < 180:  # 3분 → 원하는 시간(초)
```

**할인율 조정:**
```python
# auto_trader.py 수정
if price >= last_sell * 0.98:  # 2% → 원하는 비율
```

**포지션 축소 조정:**
```python
# auto_trader.py 수정
if self.consecutive_losses >= 3:  # 3패 → 원하는 횟수
    reduction = 0.5  # 50% → 원하는 비율
```

---

## 🔧 문제 해결

### Telegram 알림이 안 와요

1. 봇에게 메시지를 보냈는지 확인:
   ```bash
   ls -la .telegram_chat_id
   ```

2. Chat ID 재설정:
   ```bash
   ./setup_telegram.sh
   ```

3. 수동 테스트:
   ```bash
   python3 telegram_notifier.py "테스트 메시지"
   ```

### 일일 리포트가 안 와요

1. Cron 확인:
   ```bash
   crontab -l | grep daily_report
   ```

2. 수동 실행:
   ```bash
   python3 daily_report.py
   ```

3. 로그 확인:
   ```bash
   cat logs/daily_report.log
   ```

### 거래가 안 돼요

1. 로그 확인:
   ```bash
   journalctl --user -u trader-autotrader.service -n 100
   ```

2. 차단 사유 확인:
   ```bash
   journalctl --user -u trader-autotrader.service | grep "차단\|보류"
   ```

3. 일일 손실 확인:
   ```bash
   journalctl --user -u trader-autotrader.service | grep "일일 PnL"
   ```

---

## 📞 지원

**로그 위치:**
- 트레이더: `journalctl --user -u trader-autotrader.service`
- 리포트: `logs/daily_report.log`
- 거래 기록: `live_trade_log.json`

**설정 파일:**
- Telegram Chat ID: `.telegram_chat_id`
- 거래 프로필: `trading_profile.json`
- 베이스라인: `live_baseline.json`

**문서:**
- 개선 사항: `IMPROVEMENTS.md`
- 실행 가이드: `RUN_GUIDE.md`

---

생성일: 2026-02-22
버전: 2.0
