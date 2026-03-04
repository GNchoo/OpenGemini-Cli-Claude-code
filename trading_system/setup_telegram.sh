#!/bin/bash
# Telegram 봇 초기 설정

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Telegram 알림 봇 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣ Telegram 앱을 열고 다음 봇을 찾으세요:"
echo "   https://t.me/Coin_Trading_Alert_Me_bot"
echo ""
echo "   또는 검색: @Coin_Trading_Alert_Me_bot"
echo ""
echo "2️⃣ 봇과 대화를 시작하고 /start 메시지를 보내세요"
echo ""
echo "3️⃣ 메시지를 보낸 후 Enter 키를 눌러 계속하세요..."
read -r

echo ""
echo "Chat ID 가져오는 중..."
python3 "$SCRIPT_DIR/telegram_notifier.py" <<< $'\n'

if [ -f "$SCRIPT_DIR/.telegram_chat_id" ]; then
    echo ""
    echo "✅ Telegram 설정 완료!"
    echo ""
    echo "테스트 알림 전송 중..."
    python3 "$SCRIPT_DIR/telegram_notifier.py" "🤖 트레이더 마크 봇 연결 성공! 이제 중요한 거래 알림을 받을 수 있습니다."
else
    echo ""
    echo "❌ 설정 실패. 다시 시도하세요:"
    echo "   1. 봇에게 /start 메시지를 보냈는지 확인"
    echo "   2. 이 스크립트를 다시 실행"
fi
