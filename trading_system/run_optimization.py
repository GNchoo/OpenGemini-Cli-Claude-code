#!/usr/bin/env python3
"""
트레이더 마크 📊 - 최적화 실행 스크립트
"""

import subprocess
import sys
import os

def run_optimization_steps():
    """최적화 단계별 실행"""
    
    print("=" * 70)
    print("트레이더 마크 📊 - 최적화 프로세스 시작")
    print("=" * 70)
    
    # 가상환경 확인
    if not os.path.exists('trader_env'):
        print("가상환경이 없습니다. 생성 중...")
        result = subprocess.run(['python3', '-m', 'venv', 'trader_env'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("가상환경 생성 실패")
            return False
    
    # 가상환경 활성화 (소스 명령은 스크립트에서 직접 할 수 없으므로 경로만 설정)
    python_path = 'trader_env/bin/python'
    
    if not os.path.exists(python_path):
        print(f"Python 경로 없음: {python_path}")
        return False
    
    # 1. 시스템 테스트
    print("\n1. 시스템 테스트 실행...")
    result = subprocess.run([python_path, 'test_system.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 시스템 테스트 성공")
    else:
        print("❌ 시스템 테스트 실패")
        print(result.stderr)
        return False
    
    # 2. 다중 종목 테스트
    print("\n2. 다중 종목 테스트 실행...")
    result = subprocess.run([python_path, 'multi_stock_test.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 다중 종목 테스트 성공")
        
        # 결과에서 알파 양수 종목 추출
        output = result.stdout
        alpha_lines = [line for line in output.split('\n') if '알파 양수 종목:' in line]
        if alpha_lines:
            print(alpha_lines[0])
    else:
        print("❌ 다중 종목 테스트 실패")
        print(result.stderr)
    
    # 3. 파라미터 최적화 (간단한 버전)
    print("\n3. 파라미터 최적화 실행...")
    
    # 직접 파이썬 코드 실행
    optimization_code = '''
import pandas as pd
import numpy as np
from datetime import datetime
from data_collector import DataCollector
from trading_strategy import MovingAverageCrossover

print("간단한 파라미터 최적화 시작...")

# 데이터 수집
collector = DataCollector()
ticker = "005930.KS"  # 삼성전자로 테스트
data = collector.get_stock_data(ticker, period="3mo")

if data.empty:
    print("데이터 수집 실패")
    exit(1)

# 이동평균선 조합 테스트
ma_combinations = [(5,20), (10,30), (20,50), (5,50)]

results = []
for short, long in ma_combinations:
    strategy = MovingAverageCrossover(short, long)
    
    # 간단한 백테스팅
    capital = 10000000
    position = 0
    entry_price = 0
    
    for i in range(20, len(data)):
        historical_data = data.iloc[:i+1]
        current_price = historical_data["Close"].iloc[-1]
        
        signal = strategy.analyze(historical_data, ticker)
        
        if signal.action.value == "BUY" and position <= 0:
            if position == -1:
                pnl = (entry_price - current_price) * 100
                capital += pnl
            position = 1
            entry_price = current_price
        elif signal.action.value == "SELL" and position >= 0:
            if position == 1:
                pnl = (current_price - entry_price) * 100
                capital += pnl
            position = -1
            entry_price = current_price
    
    # 최종 청산
    if position == 1:
        final_price = data["Close"].iloc[-1]
        pnl = (final_price - entry_price) * 100
        capital += pnl
    elif position == -1:
        final_price = data["Close"].iloc[-1]
        pnl = (entry_price - final_price) * 100
        capital += pnl
    
    return_rate = ((capital - 10000000) / 10000000) * 100
    results.append((short, long, return_rate))
    print(f"MA({short},{long}): {return_rate:+.2f}%")

# 결과 분석
if results:
    best_result = max(results, key=lambda x: x[2])
    print(f"\\n✅ 최적 이동평균선: MA({best_result[0]},{best_result[1]}) ({best_result[2]:+.2f}%)")
    
    # 결과 저장
    import json
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "ticker": ticker,
        "results": [{"short": s, "long": l, "return": r} for s, l, r in results],
        "best_params": {"short": best_result[0], "long": best_result[1], "return": best_result[2]}
    }
    
    with open("optimization_results/simple_ma_optimization.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    print("💾 결과 저장: optimization_results/simple_ma_optimization.json")
'''

    # 임시 파일에 코드 작성 후 실행
    with open('temp_optimization.py', 'w') as f:
        f.write(optimization_code)
    
    result = subprocess.run([python_path, 'temp_optimization.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 파라미터 최적화 성공")
        print(result.stdout)
    else:
        print("❌ 파라미터 최적화 실패")
        print(result.stderr)
    
    # 임시 파일 삭제
    if os.path.exists('temp_optimization.py'):
        os.remove('temp_optimization.py')
    
    # 4. 혼합 전략 테스트
    print("\n4. 혼합 전략 테스트 실행...")
    
    hybrid_code = '''
from trading_strategy import MovingAverageCrossover, RSIMeanReversion, BollingerBandStrategy, StrategyManager
from data_collector import DataCollector
import json
from datetime import datetime

print("혼합 전략 테스트 시작...")

# 데이터 수집
collector = DataCollector()
ticker = "005380.KS"  # 현대차 (알파 양수 종목)
data = collector.get_stock_data(ticker, period="3mo")

if data.empty:
    print("데이터 수집 실패")
    exit(1)

# 테스트할 혼합 전략
hybrid_combos = [
    {"name": "MA 단일", "ma_weight": 1.0},
    {"name": "MA+RSI", "ma_weight": 0.7, "rsi_weight": 0.3},
    {"name": "MA+BB", "ma_weight": 0.7, "bb_weight": 0.3},
    {"name": "MA+RSI+BB", "ma_weight": 0.5, "rsi_weight": 0.3, "bb_weight": 0.2}
]

results = []

for combo in hybrid_combos:
    manager = StrategyManager()
    
    # 이동평균선 전략
    ma_strategy = MovingAverageCrossover(5, 20)
    manager.add_strategy(ma_strategy, combo.get("ma_weight", 0.5))
    
    # RSI 전략
    if combo.get("rsi_weight", 0) > 0:
        rsi_strategy = RSIMeanReversion(30, 70)
        manager.add_strategy(rsi_strategy, combo["rsi_weight"])
    
    # 볼린저밴드 전략
    if combo.get("bb_weight", 0) > 0:
        bb_strategy = BollingerBandStrategy()
        manager.add_strategy(bb_strategy, combo["bb_weight"])
    
    # 백테스팅
    capital = 10000000
    position = 0
    entry_price = 0
    
    for i in range(20, len(data)):
        historical_data = data.iloc[:i+1]
        current_price = historical_data["Close"].iloc[-1]
        
        # 개별 전략 분석
        signals = manager.analyze_all(historical_data, ticker)
        
        # 합의 신호
        consensus = manager.get_consensus_signal(signals)
        
        if consensus.action.value == "BUY" and position <= 0:
            if position == -1:
                pnl = (entry_price - current_price) * 100
                capital += pnl
            position = 1
            entry_price = current_price
        elif consensus.action.value == "SELL" and position >= 0:
            if position == 1:
                pnl = (current_price - entry_price) * 100
                capital += pnl
            position = -1
            entry_price = current_price
    
    # 최종 청산
    if position == 1:
        final_price = data["Close"].iloc[-1]
        pnl = (final_price - entry_price) * 100
        capital += pnl
    elif position == -1:
        final_price = data["Close"].iloc[-1]
        pnl = (entry_price - final_price) * 100
        capital += pnl
    
    return_rate = ((capital - 10000000) / 10000000) * 100
    results.append({
        "name": combo["name"],
        "return": return_rate,
        "weights": {k: v for k, v in combo.items() if "weight" in k}
    })
    
    print(f"{combo['name']}: {return_rate:+.2f}%")

# 결과 분석
if results:
    best_result = max(results, key=lambda x: x["return"])
    print(f"\\n✅ 최적 혼합 전략: {best_result['name']} ({best_result['return']:+.2f}%)")
    
    # 결과 저장
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "ticker": ticker,
        "results": results,
        "best_strategy": best_result
    }
    
    with open("optimization_results/hybrid_strategy_test.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    print("💾 결과 저장: optimization_results/hybrid_strategy_test.json")
'''

    with open('temp_hybrid.py', 'w') as f:
        f.write(hybrid_code)
    
    result = subprocess.run([python_path, 'temp_hybrid.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 혼합 전략 테스트 성공")
        print(result.stdout)
    else:
        print("❌ 혼합 전략 테스트 실패")
        print(result.stderr)
    
    # 임시 파일 삭제
    if os.path.exists('temp_hybrid.py'):
        os.remove('temp_hybrid.py')
    
    # 5. 최종 리포트
    print("\n5. 최종 리포트 생성...")
    
    report_code = '''
from datetime import datetime
import json
import os

print("최종 리포트 생성 중...")

# 디렉토리 생성
os.makedirs("reports", exist_ok=True)

# 결과 파일 읽기
results = {}

ma_file = "optimization_results/simple_ma_optimization.json"
hybrid_file = "optimization_results/hybrid_strategy_test.json"

if os.path.exists(ma_file):
    with open(ma_file, "r") as f:
        ma_results = json.load(f)
    results["ma_optimization"] = ma_results

if os.path.exists(hybrid_file):
    with open(hybrid_file, "r") as f:
        hybrid_results = json.load(f)
    results["hybrid_strategy"] = hybrid_results

# 리포트 생성
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = f"reports/final_optimization_report_{timestamp}.txt"

with open(report_file, "w") as f:
    f.write("=" * 80 + "\\n")
    f.write("트레이더 마크 📊 - 최적화 최종 리포트\\n")
    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
    f.write("=" * 80 + "\\n\\n")
    
    f.write("1. 테스트 개요\\n")
    f.write("-" * 40 + "\\n")
    f.write("• 테스트 종목: 삼성전자(005930.KS), 현대차(005380.KS)\\n")
    f.write("• 테스트 기간: 3개월\\n")
    f.write("• 초기 자본: 10,000,000원\\n\\n")
    
    if "ma_optimization" in results:
        f.write("2. 이동평균선 파라미터 최적화\\n")
        f.write("-" * 40 + "\\n")
        
        ma_data = results["ma_optimization"]
        f.write(f"테스트 종목: {ma_data['ticker']}\\n\\n")
        
        f.write("파라미터별 성과:\\n")
        for r in ma_data["results"]:
            f.write(f"  • MA({r['short']},{r['long']}): {r['return']:+.2f}%\\n")
        
        best = ma_data["best_params"]
        f.write(f"\\n✅ 최적 이동평균선: MA({best['short']},{best['long']}) ({best['return']:+.2f}%)\\n\\n")
    
    if "hybrid_strategy" in results:
        f.write("3. 혼합 전략 테스트\\n")
        f.write("-" * 40 + "\\n")
        
        hybrid_data = results["hybrid_strategy"]
        f.write(f"테스트 종목: {hybrid_data['ticker']}\\n\\n")
        
        f.write("전략별 성과:\\n")
        for r in hybrid_data["results"]:
            f.write(f"  • {r['name']}: {r['return']:+.2f}%\\n")
        
        best = hybrid_data["best_strategy"]
        f.write(f"\\n✅ 최적 혼합 전략: {best['name']} ({best['return']:+.2f}%)\\n\\n")
    
    f.write("4. 투자 권장사항\\n")
    f.write("-" * 40 + "\\n")
    
    if "ma_optimization" in results and "hybrid_strategy" in results:
        ma_best = results["ma_optimization"]["best_params"]
        hybrid_best = results["hybrid_strategy"]["best_strategy"]
        
        f.write("🎯 추천 설정:\\n")
        f.write(f"  • 이동평균선: MA({ma_best['short']},{ma_best['long']})\\n")
        f.write(f"  • 혼합 전략: {hybrid_best['name']}\\n")
        f.write(f"  • 리스크 관리: 자본의 2% 제한\\n")
        f.write(f"  • 손절매: 5% 설정\\n")
        f.write(f"  • 익절매: 10% 설정\\n")
    else:
        f.write("테스트 결과가 부족하여 구체적인 권장사항을 제시할 수 없습니다.\\n")
    
    f.write("\\n" + "=" * 80 + "\\n")
    f.write("트레이더 마크 📊 분석 완료\\n")
    f.write("=" * 80 + "\\n")

print(f"📄 리포트 생성 완료: {report_file}")
'''

    with open('temp_report.py', 'w') as f:
        f.write(report_code)
    
    result = subprocess.run([python_path, 'temp_report.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 리포트 생성 성공")
        print(result.stdout)
    else:
        print("❌ 리포트 생성 실패")
        print(result.stderr)
    
    # 임시 파일 삭제
    if os.path.exists('temp_report.py'):
        os.remove('temp_report.py')
    
    print("\n" + "=" * 70)
    print("🎉 모든 최적화 단계 완료!")
    print("=" * 70)
    
    # 생성된 파일 목록
    print("\n📁 생성된 파일:")
    for dir_name in ['optimization_results', 'reports']:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            if files:
                print(f"\n{dir_name}/")
                for file in files:
                    print(f"  • {file}")
    
    return True

if __name__ == "__main__":
    success = run_optimization_steps()
    
    if success:
        print("\n✅ 최적화 프로세스 완료!")
        print("\n다음 단계: 실제 API 연동 준비를 시작할 수 있습니다.")
        print("\n실행 가능한 명령어:")
        print("1. 시스템 상태 확인: python test_system.py")
        print("2. 다중 종목 분석: python multi_stock_test.py")
        print("3. 일일 분석: python main_fixed.py --mode test")