# 트레이더 마크 📊 - 3월 16일까지 개발 로드맵

## 목표: 실전 투자 완벽 준비

---

## Week 1 (2/19~2/23) — 모의투자 엔진 + 성과 추적
- [x] 실시간 모니터링 모듈 (volatility_monitor.py)
- [x] WebSocket 클라이언트 (websocket_client.py)
- [x] AI 신호 엔진 (ai_signal_engine.py)
- [x] 자동 트레이더 (auto_trader.py)
- [ ] 모의투자 엔진 — 일별 성과 추적 + 리포트
- [ ] 성과 대시보드 — 수익률 / 승률 / 최대낙폭

## Week 2 (2/24~3/2) — 전략 고도화 + 리스크 강화
- [ ] 멀티심볼 동시 매매 최적화
- [ ] 동적 손절/익절 (ATR 기반)
- [ ] 일일 손실 한도 시스템
- [ ] 연속 손실 자동 중지
- [ ] 시장 상황별 전략 백테스트

## Week 3 (3/3~3/9) — AI 고도화 + 실전 연동 준비
- [ ] AI 에이전트 성과 기반 가중치 조정
- [ ] 뉴스/공포지수 연동 (크립토 Fear & Greed)
- [ ] 실제 업비트 WebSocket 연결 테스트
- [ ] 주문 체결 확인 로직

## Week 4 (3/10~3/15) — 최종 점검 + 실전 준비
- [ ] 전체 시스템 스트레스 테스트
- [ ] 엣지 케이스 처리 (네트워크 오류 등)
- [ ] 모의투자 최종 성과 분석
- [ ] 실전 전환 체크리스트 완료

## 3월 16일 — 실전 시작
- K-Bank 계좌 → 업비트 입금
- 100,000원 소액 실전 테스트
- paper_mode=False, simulate=False 전환
- 24시간 모니터링 시작

---

## 일일 자동 실행 명령어
```bash
cd trading_system && source trader_env/bin/activate
python3 paper_engine.py --days 1   # 오늘 모의투자 실행
python3 paper_engine.py --report   # 누적 성과 리포트
```
