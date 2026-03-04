# 트레이더 마크 📊 - 자동 매매 시스템 빠른 시작 가이드

## 시스템 개요
알고리즘 기반 자동 주식 트레이딩 시스템으로, 냉철한 데이터 분석과 효율적인 의사결정을 통해 수익을 극대화합니다.

## 1. 필수 패키지 설치

```bash
# 필수 패키지 설치
cd trading_system
pip install -r requirements.txt

# 또는 개별 설치
pip install yfinance pandas numpy ta matplotlib schedule scikit-learn
```

## 2. 시스템 테스트

```bash
# 전체 시스템 테스트
python test_system.py

# 개별 모듈 테스트
python data_collector.py          # 데이터 수집 테스트
python trading_strategy.py        # 트레이딩 전략 테스트
python backtest.py               # 백테스팅 테스트
```

## 3. 백테스팅 실행 (권장)

백테스팅을 통해 전략의 성능을 검증합니다:

```bash
# 종합 백테스팅 실행
python backtest.py

# 또는 메인 시스템을 통해 백테스팅
python main.py --mode backtest --backtest-period 6mo
```

## 4. 설정 파일 수정

`config.json` 파일을 수정하여 시스템 설정을 변경합니다:

```json
{
  "initial_capital": 10000000,      // 초기 자본
  "risk_per_trade": 0.02,           // 거래당 최대 손실 2%
  "watchlist": [                    // 모니터링 종목
    "005930.KS",    // 삼성전자
    "000660.KS",    // SK하이닉스
    "035420.KS",    // 네이버
    "035720.KS"     // 카카오
  ],
  "stop_loss_percent": 0.05,        // 손절 5%
  "take_profit_percent": 0.08       // 익절 8%
}
```

## 5. 실행 모드

### 테스트 모드 (시뮬레이션)
```bash
python main.py --mode test
```
- 실제 거래 없이 시뮬레이션만 실행
- 백테스팅 결과 확인
- 시스템 동작 테스트

### 실전 모드 (⚠️ 주의)
```bash
python main.py --mode live
```
- 실제 거래 실행
- 반드시 백테스팅 후 사용 권장
- 초기에는 소액으로 테스트

## 6. 시스템 구성 요소

### 데이터 수집 모듈 (`data_collector.py`)
- 실시간 주가 데이터 수집
- 기술적 지표 계산
- 데이터 저장 및 관리

### 트레이딩 전략 모듈 (`trading_strategy.py`)
- 이동평균선 크로스오버 전략
- RSI 평균회귀 전략
- 볼린저밴드 전략
- 다중 전략 통합 관리

### 백테스팅 모듈 (`backtest.py`)
- 역사적 데이터 기반 전략 검증
- 성과 지표 계산 (승률, 샤프비율 등)
- 결과 시각화

### 메인 시스템 (`main.py`)
- 시스템 통합 관리
- 실시간 모니터링
- 자동 트레이딩 실행

## 7. 모니터링 및 리포트

### 로그 파일
- `trading_system.log`: 시스템 실행 로그
- `data/`: 수집된 데이터 파일
- `reports/`: 일일 리포트

### 리포트 확인
```bash
# 최근 리포트 확인
ls -la reports/

# 리포트 내용 보기
cat reports/daily_report_20250415.json | python -m json.tool
```

## 8. 고급 설정

### 전략 가중치 조정
`config.json`의 `strategies` 섹션에서 전략별 가중치를 조정할 수 있습니다:

```json
"strategies": {
  "ma_crossover": {
    "enabled": true,
    "weight": 1.0    // 가중치 높일수록 영향력 증가
  }
}
```

### 거래 시간 설정
```json
"trading_hours": {
  "start": "09:00",  // 장 시작 시간
  "end": "15:30"     // 장 마감 시간
}
```

## 9. 문제 해결

### 일반적인 문제
1. **패키지 설치 오류**: Python 3.8 이상 사용 확인
2. **데이터 수집 실패**: 인터넷 연결 확인, Yahoo Finance 접근성 확인
3. **메모리 부족**: 데이터 기간 줄이기 (`period` 파라미터 조정)

### 로그 확인
```bash
# 실시간 로그 모니터링
tail -f trading_system.log

# 에러 로그 필터링
grep -i error trading_system.log
```

## 10. 다음 단계

1. **백테스팅 최적화**: 다양한 기간과 파라미터로 테스트
2. **전략 개발**: 맞춤형 트레이딩 전략 추가
3. **API 연동**: 실제 거래소 API 연결 (업비트, 빗썸 등)
4. **대시보드 개발**: 실시간 모니터링 웹 인터페이스
5. **알림 시스템**: Telegram/Discord 알림 연동

## 주의사항
- 처음에는 **테스트 모드**로 충분히 검증 후 실전 사용
- **소액**으로 시작하여 시스템 신뢰성 확인
- 정기적인 **백테스팅**으로 전략 성능 모니터링
- **리스크 관리** 설정을 엄격히 준수

---

**트레이더 마크 📊** 가 항상 냉철한 분석과 효율적인 의사결정으로 도와드리겠습니다!