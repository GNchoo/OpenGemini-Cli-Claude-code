#!/usr/bin/env python3
"""
트레이더 마크 📊 - 종합 테스트 스위트
모든 시스템 모듈의 안정성과 성능 테스트
"""

import subprocess
import sys
import time
from datetime import datetime

class ComprehensiveTestSuite:
    """종합 테스트 스위트"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
        print("=" * 70)
        print("트레이더 마크 📊 - 종합 시스템 테스트 스위트")
        print("=" * 70)
        print(f"테스트 시작: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def run_test(self, test_name, command, timeout=30):
        """개별 테스트 실행"""
        print(f"🧪 테스트: {test_name}")
        print(f"   명령어: {command}")
        
        try:
            start = time.time()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start
            
            if result.returncode == 0:
                status = "✅ PASS"
                # 중요한 출력만 표시
                output_lines = result.stdout.strip().split('\n')
                if len(output_lines) > 10:
                    output = '\n'.join(output_lines[:5] + ['...'] + output_lines[-5:])
                else:
                    output = result.stdout.strip()[:200] + "..." if len(result.stdout) > 200 else result.stdout.strip()
            else:
                status = "❌ FAIL"
                output = f"종료 코드: {result.returncode}\n에러: {result.stderr[:200]}"
            
            print(f"   결과: {status} ({elapsed:.1f}초)")
            
            if output:
                print(f"   출력: {output[:100]}..." if len(output) > 100 else f"   출력: {output}")
            
            self.test_results.append({
                'test': test_name,
                'status': 'PASS' if result.returncode == 0 else 'FAIL',
                'time': elapsed,
                'output': output[:500] if output else ''
            })
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"   결과: ⏰ TIMEOUT ({timeout}초 초과)")
            self.test_results.append({
                'test': test_name,
                'status': 'TIMEOUT',
                'time': timeout,
                'output': f'{timeout}초 시간 초과'
            })
            return False
        except Exception as e:
            print(f"   결과: ❌ ERROR ({str(e)})")
            self.test_results.append({
                'test': test_name,
                'status': 'ERROR',
                'time': 0,
                'output': str(e)
            })
            return False
        
        print()
    
    def test_module_1_basic_system(self):
        """기본 시스템 테스트"""
        print("\n📋 모듈 1: 기본 시스템 테스트")
        print("-" * 40)
        
        tests = [
            ("Python 환경", "python --version"),
            ("가상환경 활성화", "source trader_env/bin/activate && python -c 'import pandas; print(f\"pandas: {pandas.__version__}\")'"),
            ("필수 패키지", "python -c 'import numpy, pandas, requests, jwt; print(\"필수 패키지 로드 완료\")'"),
        ]
        
        all_pass = True
        for name, cmd in tests:
            if not self.run_test(name, cmd):
                all_pass = False
        
        return all_pass
    
    def test_module_2_trading_strategies(self):
        """트레이딩 전략 테스트"""
        print("\n📋 모듈 2: 트레이딩 전략 테스트")
        print("-" * 40)
        
        tests = [
            ("단타 기본 전략", "python scalping_simple.py --test 2>&1 | head -20"),
            ("AI 합의 시스템", "python ai_consensus_simple.py --test 2>&1 | head -20"),
            ("백테스팅 모듈", "python backtest_simple.py --test 2>&1 | head -20"),
        ]
        
        all_pass = True
        for name, cmd in tests:
            if not self.run_test(name, cmd, timeout=60):
                all_pass = False
        
        return all_pass
    
    def test_module_3_crash_defense(self):
        """폭락 대비 시스템 테스트"""
        print("\n📋 모듈 3: 폭락 대비 시스템 테스트")
        print("-" * 40)
        
        tests = [
            ("폭락 시나리오", "python crash_simple.py 2>&1 | head -30"),
            ("종합 폭락 시스템", "python complete_crash_system.py 2>&1 | head -50"),
            ("한 달 시뮬레이션", "python monthly_scalping_quick.py 2>&1 | head -40"),
        ]
        
        all_pass = True
        for name, cmd in tests:
            if not self.run_test(name, cmd, timeout=120):
                all_pass = False
        
        return all_pass
    
    def test_module_4_api_integration(self):
        """API 통합 테스트"""
        print("\n📋 모듈 4: API 통합 테스트")
        print("-" * 40)
        
        tests = [
            ("업비트 기본 테스트", "python upbit_ubuntu_simple.py 2>&1 | head -20"),
            ("API 키 테스트", "python test_upbit_simple.py 2>&1 | head -20"),
            ("시스템 통합 테스트", "python test_system.py 2>&1 | head -20"),
        ]
        
        all_pass = True
        for name, cmd in tests:
            if not self.run_test(name, cmd, timeout=60):
                all_pass = False
        
        return all_pass
    
    def test_module_5_performance(self):
        """성능 테스트"""
        print("\n📋 모듈 5: 성능 테스트")
        print("-" * 40)
        
        tests = [
            ("데이터 수집 속도", "python -c 'import time; start=time.time(); import pandas as pd; import numpy as np; print(f\"로딩 시간: {time.time()-start:.3f}초\")'"),
            ("메모리 사용량", "python -c 'import psutil; import os; process = psutil.Process(os.getpid()); print(f\"메모리: {process.memory_info().rss / 1024 / 1024:.1f} MB\")' 2>/dev/null || echo 'psutil 없음'"),
            ("동시성 테스트", "python -c 'import threading; def test(): pass; threads = [threading.Thread(target=test) for _ in range(10)]; [t.start() for t in threads]; [t.join() for t in threads]; print(\"10스레드 테스트 완료\")'"),
        ]
        
        all_pass = True
        for name, cmd in tests:
            if not self.run_test(name, cmd):
                all_pass = False
        
        return all_pass
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 종합 테스트 시작")
        print("=" * 70)
        
        modules = [
            ("기본 시스템", self.test_module_1_basic_system),
            ("트레이딩 전략", self.test_module_2_trading_strategies),
            ("폭락 대비", self.test_module_3_crash_defense),
            ("API 통합", self.test_module_4_api_integration),
            ("성능", self.test_module_5_performance),
        ]
        
        module_results = []
        
        for module_name, module_func in modules:
            print(f"\n▶️ {module_name} 테스트 시작")
            result = module_func()
            module_results.append((module_name, result))
            print(f"   {'✅ 통과' if result else '❌ 실패'}")
        
        # 결과 분석
        self.generate_test_report(module_results)
    
    def generate_test_report(self, module_results):
        """테스트 리포트 생성"""
        print("\n" + "=" * 70)
        print("종합 테스트 리포트")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        print(f"\n📊 테스트 통계:")
        print(f"  총 테스트: {total_tests}개")
        print(f"  통과: {passed_tests}개")
        print(f"  실패: {failed_tests}개")
        print(f"  통과율: {(passed_tests/total_tests*100):.1f}%")
        print(f"  총 소요 시간: {total_time:.1f}초")
        
        print(f"\n📋 모듈별 결과:")
        for module_name, result in module_results:
            status = "✅ 통과" if result else "❌ 실패"
            print(f"  {module_name}: {status}")
        
        print(f"\n🔍 실패한 테스트:")
        failed = [r for r in self.test_results if r['status'] != 'PASS']
        if failed:
            for test in failed:
                print(f"  • {test['test']}: {test['status']}")
                if test['output']:
                    print(f"    출력: {test['output'][:100]}")
        else:
            print("  없음 ✅")
        
        print(f"\n🎯 시스템 안정성 평가:")
        stability_score = (passed_tests / total_tests) * 100
        
        if stability_score >= 90:
            print(f"  ✅ 우수 ({stability_score:.1f}%) - 개발 진행 가능")
            recommendation = "모든 개발 단계 진행 가능"
        elif stability_score >= 80:
            print(f"  ⚠️ 양호 ({stability_score:.1f}%) - 주요 문제 수정 후 진행")
            recommendation = "주요 문제 수정 후 개발 진행"
        elif stability_score >= 60:
            print(f"  ⚠️ 보통 ({stability_score:.1f}%) - 상당한 개선 필요")
            recommendation = "상당한 개선 후 개발 진행"
        else:
            print(f"  ❌ 불안정 ({stability_score:.1f}%) - 재구축 필요")
            recommendation = "시스템 재구축 필요"
        
        print(f"\n💡 권장사항: {recommendation}")
        
        print(f"\n🚀 다음 단계:")
        if stability_score >= 80:
            print("1. 변동성 모니터링 모듈 개발")
            print("2. 긴급 정지 메커니즘 구현")
            print("3. AI 감지 에이전트 통합")
            print("4. 업비트 API 연동")
        else:
            print("1. 실패한 테스트 분석 및 수정")
            print("2. 시스템 안정성 개선")
            print("3. 재테스트 진행")
            print("4. 안정화 후 개발 진행")
        
        print("\n" + "=" * 70)
        print(f"✅ 종합 테스트 완료 ({end_time.strftime('%H:%M:%S')})")
        print("=" * 70)
        
        # 결과 저장
        self.save_results(stability_score)
        
        return stability_score >= 80
    
    def save_results(self, stability_score):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("트레이더 마크 📊 - 종합 테스트 리포트\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"테스트 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"안정성 점수: {stability_score:.1f}%\n\n")
            
            f.write("테스트 결과:\n")
            for result in self.test_results:
                f.write(f"- {result['test']}: {result['status']} ({result['time']:.1f}초)\n")
            
            f.write(f"\n총 테스트: {len(self.test_results)}개\n")
            f.write(f"통과: {sum(1 for r in self.test_results if r['status'] == 'PASS')}개\n")
            f.write(f"실패: {len(self.test_results) - sum(1 for r in self.test_results if r['status'] == 'PASS')}개\n")
        
        print(f"\n📁 테스트 리포트 저장: {filename}")
        return filename

def main():
    """메인 실행"""
    print("트레이더 마크 📊 - 시스템 종합 테스트 시작")
    
    # 테스트 스위트 실행
    test_suite = ComprehensiveTestSuite()
    
    try:
        # 모든 테스트 실행
        ready_for_development = test_suite.run_all_tests()
        
        print("\n💡 최종 결정:")
        if ready_for_development:
            print("✅ 시스템 안정성 확인 - 개발 진행 가능")
            print("   다음: 변동성 모니터링 모듈 개발 시작")
        else:
            print("❌ 시스템 안정성 부족 - 문제 수정 필요")
            print("   다음: 실패한 테스트 분석 및 수정")
        
    except KeyboardInterrupt:
        print("\n⏹️ 테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")

if __name__ == "__main__":
    main()