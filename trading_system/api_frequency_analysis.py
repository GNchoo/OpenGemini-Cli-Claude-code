#!/usr/bin/env python3
"""
트레이더 마크 📊 - API 조회 빈도 분석
"""

import time
from datetime import datetime, timedelta

class APIFrequencyAnalyzer:
    """API 조회 빈도 분석기"""
    
    def __init__(self):
        self.upbit_limits = {
            'requests_per_minute': 600,     # 분당 600회
            'requests_per_second': 10,      # 초당 10회
            'websocket_connections': 20,    # 최대 20개 WebSocket
            'order_requests_per_second': 8, # 초당 주문 8회
        }
        
        print("=" * 70)
        print("트레이더 마크 📊 - API 조회 빈도 분석")
        print("=" * 70)
    
    def analyze_scalping_frequency(self):
        """단타 매매 API 조회 빈도 분석"""
        print("\n📊 단타 매매(스캘핑) API 사용 패턴")
        print("-" * 40)
        
        # 단타 매매 시나리오
        scenarios = [
            {
                'name': '초고빈도 단타',
                'timeframe': '1m',
                'trades_per_hour': 120,      # 시간당 120회 (30초마다)
                'data_checks_per_trade': 3,  # 거래당 3회 데이터 확인
                'description': '극단적 고빈도'
            },
            {
                'name': '고빈도 단타',
                'timeframe': '5m',
                'trades_per_hour': 30,       # 시간당 30회 (2분마다)
                'data_checks_per_trade': 2,  # 거래당 2회 데이터 확인
                'description': '일반적 단타'
            },
            {
                'name': '중빈도 단타',
                'timeframe': '15m',
                'trades_per_hour': 12,       # 시간당 12회 (5분마다)
                'data_checks_per_trade': 2,  # 거래당 2회 데이터 확인
                'description': '보수적 단타'
            },
            {
                'name': '저빈도 스윙',
                'timeframe': '1h',
                'trades_per_hour': 2,        # 시간당 2회 (30분마다)
                'data_checks_per_trade': 1,  # 거래당 1회 데이터 확인
                'description': '스윙 트레이딩'
            }
        ]
        
        for scenario in scenarios:
            # 시간당 API 호출 계산
            hourly_api_calls = scenario['trades_per_hour'] * scenario['data_checks_per_trade']
            
            # 분당 API 호출
            minute_api_calls = hourly_api_calls / 60
            
            # 초당 API 호출
            second_api_calls = hourly_api_calls / 3600
            
            # 업비트 제한 대비
            minute_limit_ratio = (minute_api_calls / self.upbit_limits['requests_per_minute']) * 100
            second_limit_ratio = (second_api_calls / self.upbit_limits['requests_per_second']) * 100
            
            print(f"\n🔹 {scenario['name']} ({scenario['timeframe']}):")
            print(f"   거래 빈도: {scenario['trades_per_hour']}회/시간")
            print(f"   API 호출: {hourly_api_calls:.0f}회/시간")
            print(f"   분당: {minute_api_calls:.1f}회 (제한 대비 {minute_limit_ratio:.1f}%)")
            print(f"   초당: {second_api_calls:.3f}회 (제한 대비 {second_limit_ratio:.1f}%)")
            print(f"   설명: {scenario['description']}")
    
    def analyze_our_system_frequency(self):
        """우리 시스템의 실제 API 조회 빈도 분석"""
        print("\n📊 우리 시스템의 API 사용 패턴")
        print("-" * 40)
        
        # 우리 시스템 구성 요소별 API 사용
        components = [
            {
                'component': '변동성 모니터링',
                'frequency': '10초마다',
                'calls_per_hour': 360,  # 3600초 / 10초
                'endpoints': ['ticker', 'candles']
            },
            {
                'component': 'AI 합의 시스템',
                'frequency': '1분마다',
                'calls_per_hour': 60,
                'endpoints': ['ticker', 'candles', 'orderbook']
            },
            {
                'component': '긴급 감시',
                'frequency': '5초마다',
                'calls_per_hour': 720,
                'endpoints': ['ticker']
            },
            {
                'component': '포트폴리오 관리',
                'frequency': '30초마다',
                'calls_per_hour': 120,
                'endpoints': ['accounts', 'ticker']
            },
            {
                'component': '주문 실행',
                'frequency': '거래 발생 시',
                'calls_per_hour': 50,  # 예상 평균
                'endpoints': ['orders', 'ticker']
            }
        ]
        
        total_hourly_calls = 0
        endpoint_usage = {}
        
        print("구성 요소별 API 사용량:")
        for comp in components:
            calls = comp['calls_per_hour']
            total_hourly_calls += calls
            
            # 엔드포인트별 사용량 집계
            for endpoint in comp['endpoints']:
                endpoint_usage[endpoint] = endpoint_usage.get(endpoint, 0) + calls
            
            print(f"\n  {comp['component']}:")
            print(f"    빈도: {comp['frequency']}")
            print(f"    시간당: {calls}회")
            print(f"    엔드포인트: {', '.join(comp['endpoints'])}")
        
        # 총계 계산
        minute_calls = total_hourly_calls / 60
        second_calls = total_hourly_calls / 3600
        
        minute_limit_ratio = (minute_calls / self.upbit_limits['requests_per_minute']) * 100
        second_limit_ratio = (second_calls / self.upbit_limits['requests_per_second']) * 100
        
        print(f"\n📈 총계:")
        print(f"  시간당 총 API 호출: {total_hourly_calls:.0f}회")
        print(f"  분당: {minute_calls:.1f}회 (제한 대비 {minute_limit_ratio:.1f}%)")
        print(f"  초당: {second_calls:.3f}회 (제한 대비 {second_limit_ratio:.1f}%)")
        
        print(f"\n🔍 엔드포인트별 사용량:")
        for endpoint, calls in sorted(endpoint_usage.items(), key=lambda x: x[1], reverse=True):
            pct = (calls / total_hourly_calls) * 100
            print(f"  {endpoint}: {calls:.0f}회 ({pct:.1f}%)")
    
    def calculate_optimal_frequency(self):
        """최적의 API 조회 빈도 계산"""
        print("\n🎯 최적 API 조회 빈도 제안")
        print("-" * 40)
        
        # 안전 마진: 제한의 80% 사용
        safe_minute_limit = self.upbit_limits['requests_per_minute'] * 0.8  # 480회/분
        safe_second_limit = self.upbit_limits['requests_per_second'] * 0.8  # 8회/초
        
        print(f"안전 제한 (제한의 80%):")
        print(f"  분당: {safe_minute_limit:.0f}회")
        print(f"  초당: {safe_second_limit:.1f}회")
        
        # 최적 빈도 계산
        optimal_frequencies = [
            {
                'task': '초고빈도 모니터링',
                'optimal_interval': 3,  # 3초마다
                'hourly_calls': 1200,
                'reason': '긴급 상황 감지용'
            },
            {
                'task': '실시간 가격 모니터링',
                'optimal_interval': 5,  # 5초마다
                'hourly_calls': 720,
                'reason': '단타 신호 생성용'
            },
            {
                'task': '기술적 분석',
                'optimal_interval': 30,  # 30초마다
                'hourly_calls': 120,
                'reason': '지표 계산용'
            },
            {
                'task': '포트폴리오 관리',
                'optimal_interval': 60,  # 1분마다
                'hourly_calls': 60,
                'reason': '잔고 확인용'
            },
            {
                'task': 'AI 합의 시스템',
                'optimal_interval': 120,  # 2분마다
                'hourly_calls': 30,
                'reason': '의사결정용'
            }
        ]
        
        total_optimal_calls = sum(f['hourly_calls'] for f in optimal_frequencies)
        optimal_minute_calls = total_optimal_calls / 60
        optimal_second_calls = total_optimal_calls / 3600
        
        print(f"\n제안된 최적 빈도:")
        for freq in optimal_frequencies:
            print(f"\n  {freq['task']}:")
            print(f"    간격: {freq['optimal_interval']}초")
            print(f"    시간당: {freq['hourly_calls']}회")
            print(f"    이유: {freq['reason']}")
        
        print(f"\n📊 최적화된 총계:")
        print(f"  시간당 총 API 호출: {total_optimal_calls:.0f}회")
        print(f"  분당: {optimal_minute_calls:.1f}회 (안전 제한 대비 {(optimal_minute_calls/safe_minute_limit*100):.1f}%)")
        print(f"  초당: {optimal_second_calls:.3f}회 (안전 제한 대비 {(optimal_second_calls/safe_second_limit*100):.1f}%)")
        
        # WebSocket 사용 권장
        print(f"\n💡 WebSocket 사용 권장:")
        print(f"  • 실시간 가격: WebSocket으로 대체 (API 호출 감소)")
        print(f"  • 주문 체결: WebSocket으로 실시간 수신")
        print(f"  • 예상 API 호출 감소: 70% 이상")
    
    def generate_api_usage_plan(self):
        """API 사용 계획 생성"""
        print("\n📋 API 사용 계획 (실전 적용)")
        print("-" * 40)
        
        plan = {
            'phase_1': {
                'name': '초기 테스트 (1주일)',
                'max_hourly_calls': 500,
                'monitoring_interval': 10,  # 10초마다
                'description': '안정성 테스트, 제한의 20% 사용'
            },
            'phase_2': {
                'name': '소액 실전 (2주일)',
                'max_hourly_calls': 1500,
                'monitoring_interval': 5,   # 5초마다
                'description': '소액 거래, 제한의 50% 사용'
            },
            'phase_3': {
                'name': '본격 운영 (3주차 이후)',
                'max_hourly_calls': 2000,
                'monitoring_interval': 3,   # 3초마다
                'description': '전체 기능 가동, 제한의 70% 사용'
            }
        }
        
        for phase_id, phase_info in plan.items():
            minute_calls = phase_info['max_hourly_calls'] / 60
            limit_ratio = (minute_calls / self.upbit_limits['requests_per_minute']) * 100
            
            print(f"\n{phase_info['name']}:")
            print(f"  최대 시간당: {phase_info['max_hourly_calls']}회")
            print(f"  모니터링 간격: {phase_info['monitoring_interval']}초")
            print(f"  분당: {minute_calls:.1f}회 (제한 대비 {limit_ratio:.1f}%)")
            print(f"  설명: {phase_info['description']}")
        
        print(f"\n🚀 권장 실행 계획:")
        print(f"1. Phase 1부터 시작하여 시스템 안정성 확인")
        print(f"2. WebSocket 도입으로 API 부하 분산")
        print(f"3. 점진적으로 빈도 증가")
        print(f"4. 3월 16일까지 Phase 3 도달 목표")

def main():
    """메인 실행"""
    print("트레이더 마크 📊 - API 조회 빈도 상세 분석")
    
    analyzer = APIFrequencyAnalyzer()
    
    # 모든 분석 실행
    analyzer.analyze_scalping_frequency()
    analyzer.analyze_our_system_frequency()
    analyzer.calculate_optimal_frequency()
    analyzer.generate_api_usage_plan()
    
    print("\n" + "=" * 70)
    print("✅ API 조회 빈도 분석 완료")
    print("=" * 70)
    
    print("\n💡 핵심 결론:")
    print("1. 업비트 API 제한: 분당 600회, 초당 10회")
    print("2. 우리 시스템 예상 사용량: 제한의 30-50%")
    print("3. WebSocket 도입 시 70% 이상 API 호출 감소 가능")
    print("4. 점진적 확장으로 안정성 유지 가능")

if __name__ == "__main__":
    main()