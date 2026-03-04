#!/usr/bin/env python3
"""
슬리피지 분석 도구
auto_trader.py의 slippage_records를 분석
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_slippage():
    """슬리피지 패턴 분석 (로그 파일에서 추출 또는 직접 기록)"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📈 슬리피지 분석")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    
    # TODO: 실제 슬리피지 데이터는 auto_trader.py에서 파일로 저장하도록 개선 필요
    # 현재는 메모리에만 저장되므로 재시작 시 소실됨
    
    print("ℹ️ 슬리피지 데이터 수집 중...")
    print("")
    print("📝 참고:")
    print("  - 슬리피지는 주문가 vs 체결가 차이입니다")
    print("  - 0.5% 이상 차이 시 로그에 경고가 기록됩니다")
    print("  - journalctl로 '슬리피지 발생' 검색하여 확인하세요")
    print("")
    print("예시 명령:")
    print("  journalctl --user -u trader-autotrader.service | grep '슬리피지'")
    
if __name__ == "__main__":
    analyze_slippage()
