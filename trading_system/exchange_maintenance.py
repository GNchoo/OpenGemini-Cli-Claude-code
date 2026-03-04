#!/usr/bin/env python3
"""
거래소 점검시간 대응
업비트 API 상태 체크 및 점검 시간 관리
"""

import requests
from datetime import datetime

UPBIT_SERVER_STATUS_URL = "https://api.upbit.com/v1/status/wallet"

def check_upbit_status():
    """업비트 서버 상태 체크"""
    try:
        response = requests.get(UPBIT_SERVER_STATUS_URL, timeout=5)
        if response.status_code == 200:
            return True, "정상"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def is_maintenance_time():
    """점검 시간 여부 확인 (주로 새벽 시간대)"""
    now = datetime.now()
    # 업비트는 보통 새벽 1-3시에 점검하는 경우가 많음
    if 1 <= now.hour < 3:
        return True, "일반 점검 시간대"
    return False, "거래 가능 시간"

if __name__ == "__main__":
    status, msg = check_upbit_status()
    print(f"업비트 상태: {msg}")
    
    maintenance, reason = is_maintenance_time()
    if maintenance:
        print(f"점검 시간: {reason}")
    else:
        print("거래 가능")
