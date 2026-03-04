#!/usr/bin/env python3
"""
Telegram 알림 전송 모듈
"""

import requests
import json
import os
from pathlib import Path

# .env 자동 로드 (python-dotenv 미설치 환경도 수동 파싱으로 대응)
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / '.env'

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_FILE)
except Exception:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)

# Telegram 봇 설정
# 보안: 토큰 기본값은 비워두고 환경변수로만 주입
# - TELEGRAM_BOT_TOKEN: 권장 키
# - TelegramBotToken: 레거시/사용자 요청 호환 키
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TelegramBotToken", "")
CHAT_ID_FILE = BASE_DIR / '.telegram_chat_id'

def get_chat_id():
    """저장된 chat_id 또는 환경변수에서 chat_id 로드"""
    env_chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TelegramChatId")
    if env_chat_id:
        return str(env_chat_id).strip()
    try:
        if CHAT_ID_FILE.exists():
            return CHAT_ID_FILE.read_text().strip()
    except Exception:
        pass
    return None

def save_chat_id(chat_id: str):
    """chat_id 저장"""
    try:
        CHAT_ID_FILE.write_text(str(chat_id))
        return True
    except Exception as e:
        print(f"chat_id 저장 실패: {e}")
        return False

def get_updates():
    """최근 메시지 조회하여 chat_id 찾기"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('result'):
                # 가장 최근 메시지에서 chat_id 추출
                for update in reversed(data['result']):
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        print(f"✅ Chat ID 발견: {chat_id}")
                        save_chat_id(chat_id)
                        return str(chat_id)
                print("⚠️ 메시지가 없습니다. 봇에게 먼저 메시지를 보내주세요.")
                return None
        else:
            print(f"❌ API 오류: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ chat_id 조회 실패: {e}")
        return None

def send_message(text: str, parse_mode: str = "Markdown", silent: bool = False):
    """Telegram 메시지 전송"""
    if not BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN 미설정: Telegram 알림 전송 불가")
        return False

    chat_id = get_chat_id()

    # chat_id가 없으면 자동으로 가져오기 시도
    if not chat_id:
        chat_id = get_updates()
        if not chat_id:
            print("⚠️ chat_id를 찾을 수 없습니다. 봇에게 먼저 /start 메시지를 보내주세요.")
            return False

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_notification': silent
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            error = response.json()
            print(f"❌ 전송 실패: {error}")
            return False
    except Exception as e:
        print(f"❌ 전송 오류: {e}")
        return False

def send_alert(message: str, priority: str = "normal"):
    """우선순위에 따른 알림 전송"""
    # 우선순위에 따라 이모지 추가
    if priority == "critical":
        prefix = "🔴 *[긴급]*"
        silent = False
    elif priority == "warning":
        prefix = "🟡 *[경고]*"
        silent = False
    else:
        prefix = "ℹ️ *[정보]*"
        silent = True
    
    full_msg = f"{prefix}\n{message}"
    return send_message(full_msg, silent=silent)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 명령줄에서 직접 메시지 전송
        msg = ' '.join(sys.argv[1:])
        if send_message(msg):
            print("✅ 메시지 전송 성공")
        else:
            print("❌ 메시지 전송 실패")
    else:
        # chat_id 설정 모드
        print("=== Telegram Bot 설정 ===")
        print(f"Bot Token: {BOT_TOKEN}")
        print("\n1. Telegram에서 봇을 찾으세요:")
        print("   @트레이더마크봇 (또는 봇 링크)")
        print("\n2. 봇에게 /start 메시지를 보내세요")
        print("\n3. 아무 키나 눌러 chat_id를 가져옵니다...")
        input()
        
        chat_id = get_updates()
        if chat_id:
            print(f"\n✅ Chat ID 설정 완료: {chat_id}")
            print("\n테스트 메시지 전송 중...")
            if send_message("🤖 트레이더 마크 봇이 연결되었습니다!"):
                print("✅ 설정 완료!")
            else:
                print("❌ 테스트 전송 실패")
        else:
            print("\n❌ 설정 실패. 봇에게 먼저 메시지를 보내주세요.")
