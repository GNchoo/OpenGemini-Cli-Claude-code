# 트레이더 마크 📊 - 실행 가이드 (수정판)

## 시스템 상태
✅ **모든 오류 수정 완료** (2025-04-15)
- 들여쓰기 오류 해결
- 라이브러리 호환성 문제 해결
- 클래스 초기화 문제 해결

## 빠른 시작

### 1. 가상환경 활성화
```bash
cd trading_system
source trader_env/bin/activate
```

### 2. 시스템 테스트
```bash
# 전체 시스템 테스트
python test_system.py

# 개별 모듈 테스트
python data_collector.py          # 데이터 수집 테스트
python trading_strategy.py        # 트레이딩 전략 테스트
python backtest_fixed.py          # 백테스팅 테스트
python main_fixed.py --mode test  # 메인 시스템 테스트
```

### 3. 다중 종목 분석
```bash
# 6개 종목 분석
python multi_stock_test.py
```

## 주요 모듈 설명

### 📊 데이터 수집 모듈 (`data_collector.py`)
- Yahoo Finance API를 통한 실시간 데이터 수집
- 기술적 지표 계산 (이동평균, RSI, MACD, 볼린저밴드)
- 데이터 자동 저장 (CSV 형식)

### 🎯 트레이딩 전략 모듈 (`trading_strategy.py`)
- **이동평균선 크로스오버 전략** (MA_Crossover)
- **RSI 평균회귀 전략** (RSI_MeanReversion)  
- **볼린저밴드 전략** (BollingerBandStrategy)
- 전략 매니저를 통한 다중 전략 통합

### 📈 백테스팅 모듈 (`backtest_fixed.py`)
- 역사적 데이터 기반 전략 성능 검증
- 수익률, 승률, 샤프비율 등 성과 지표 계산
- 간단한 시뮬레이션 백테스팅

### 🚀 메인 시스템 (`main_fixed.py`)
- 일일 시장 분석 자동화
- 트레이딩 신호 생성 및 리포트 작성
- 포지션 사이즈 자동 계산 (리스크 기반)

### 🔍 다중 종목 분석 (`multi_stock_test.py`)
- 6개 주요 종목 동시 분석
- 알파(초과수익) 계산
- 포트폴리오 시뮬레이션

## 설정 파일 (`config.json`)

### 주요 설정 항목:
```json
{
  "initial_capital": 10000000,      // 초기 자본 (1천만원)
  "risk_per_trade": 0.02,           // 거래당 최대 손실 2%
  "watchlist": [                    // 모니터링 종목
    "005930.KS",    // 삼성전자
    "000660.KS",    // SK하이닉스
    "035420.KS",    // 네이버
    "035720.KS",    // 카카오
    "005380.KS",    // 현대차
    "373220.KS"     // LG에너지솔루션
  ],
  "stop_loss_percent": 0.05,        // 손절 5%
  "take_profit_percent": 0.10       // 익절 10%
}
```

## 실행 모드

### 테스트 모드 (권장)
```bash
python main_fixed.py --mode test
```
- 실제 거래 없이 시뮬레이션만 실행
- 일일 리포트 생성
- 시스템 동작 확인

### 분석 모드
```bash
python main_fixed.py --mode analysis
```
- 시장 분석 및 신호 생성
- 상세 리포트 작성
- 투자 권장사항 제시

## 결과물

### 생성되는 파일:
1. **데이터 파일**: `data/*.csv` (수집된 주가 데이터)
2. **리포트 파일**: `reports/daily_report_YYYYMMDD.json` (일일 분석 리포트)
3. **테스트 리포트**: `multi_stock_test_report_*.txt` (다중 종목 테스트 리포트)
4. **시스템 로그**: `trading_system.log` (실행 로그)

### 리포트 예시:
```json
{
  "date": "2025-04-15",
  "analysis_time": "14:30:00",
  "total_signals": 2,
  "buy_signals": 1,
  "sell_signals": 1,
  "signals": [
    {
      "ticker": "005930.KS",
      "action": "BUY",
      "price": 181200,
      "confidence": 0.75,
      "reason": "골든크로스 발생",
      "position_size": 55,
      "investment": 9966000
    }
  ]
}
```

## 문제 해결

### 일반적인 문제:

1. **가상환경 활성화 실패**
   ```bash
   # 가상환경 재생성
   python3 -m venv trader_env
   source trader_env/bin/activate
   pip install -r requirements.txt
   ```

2. **패키지 설치 오류**
   ```bash
   # 개별 설치
   pip install yfinance pandas numpy ta matplotlib
   ```

3. **데이터 수집 실패**
   - 인터넷 연결 확인
   - Yahoo Finance 접근성 확인
   - `period` 파라미터 조정 (예: "1mo" → "5d")

4. **메모리 부족**
   - 데이터 기간 줄이기
   - 동시 분석 종목 수 줄이기

### 로그 확인:
```bash
# 실시간 로그 모니터링
tail -f trading_system.log

# 에러 로그 필터링
grep -i error trading_system.log
```

## 다음 단계

### 단기 (권장):
1. **파라미터 최적화 테스트**
   ```python
   # 이동평균선 조합 테스트
   combinations = [(5,20), (10,30), (20,50), (5,50)]
   ```

2. **알파 양수 종목 집중 분석**
   - 현대차, LG에너지솔루션 심층 분석
   - 섹터별 특성 연구

3. **혼합 전략 개발**
   - 이동평균선 + RSI 필터
   - 다중 타임프레임 분석

### 중장기:
4. **실제 API 연동**
   - 업비트/빗썸 모의투자
   - 실시간 데이터 스트리밍

5. **고급 기능 개발**
   - 머신러닝 예측 모델
   - 실시간 리스크 관리
   - 웹 대시보드

## 주의사항

⚠️ **중요**: 
- 처음에는 **테스트 모드**로 충분히 검증
- **소액**으로 시작하여 시스템 신뢰성 확인
- 정기적인 **백테스팅**으로 전략 성능 모니터링
- **리스크 관리** 설정을 엄격히 준수

---

**트레이더 마크** 📊 가 항상 냉철한 분석으로 도와드리겠습니다!

## 연락처
- 시스템 이슈: `test_system.py` 실행 후 로그 확인
- 기능 요청: 설정 파일(`config.json`) 수정
- 긴급 문제: 시스템 로그(`trading_system.log`) 확인