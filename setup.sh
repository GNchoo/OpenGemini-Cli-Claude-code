#!/bin/bash
# OpenGemini Unified Setup Script (2026 Edition)
set -e

echo "🚀 OpenGemini 통합 설치를 시작합니다..."

# 1. 가상환경 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경(venv) 생성 중..."
    python3 -m venv venv
fi

# 2. 의존성 설치
echo "📥 Python 패키지 설치 중..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# 3. 환경 변수 템플릿 준비
if [ ! -f ".env" ]; then
    echo "📋 .env 설정 파일 생성 중 (.env.template 기반)..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "⚠️  .env 파일이 생성되었습니다. TELEGRAM_TOKEN 등을 수동으로 설정해주세요."
    else
        cat <<EOF > .env
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ALLOWED_USER_ID=0
GEMINI_BIN=$(which gemini || echo "/home/fallman/.npm-global/bin/gemini")
CLAUDE_BIN=$(which claude || echo "/home/fallman/.npm-global/bin/claude")
GEMINI_MODEL=gemini-2.5-flash
GEMINI_WORKDIR=$(pwd)/workspace
EOF
    fi
fi

# 4. 필수 디렉토리 생성
echo "📁 디렉토리 구조 초기화 중..."
mkdir -p workspace
mkdir -p .sessions
mkdir -p ~/.opengemini/sessions
mkdir -p ~/.opengemini/memory
mkdir -p ~/.openclaw/workspace/shared-session

# 5. 실행 권한 부여
chmod +x start_bot.sh 2>/dev/null || true

# 6. systemd 서비스 등록 (자동 재시작 설정)
echo "🔄 시스템 재부팅 시 자동 실행 설정 중..."
SERVICE_FILE="$HOME/.config/systemd/user/opengemini.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=OpenGemini Agent Bot
After=network.target

[Service]
Type=simple
ExecStart=$(pwd)/venv/bin/python3 -u $(pwd)/bot.py
WorkingDirectory=$(pwd)
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable opengemini.service
loginctl enable-linger "$USER"

echo "✅ 모든 준비가 완료되었습니다!"
echo "1. .env 파일에서 TELEGRAM_TOKEN과 ALLOWED_USER_ID를 설정하세요."
echo "2. 'systemctl --user start opengemini.service' 명령어로 봇을 시작하거나,"
echo "3. 'bash start_bot.sh' 명령어로 수동 시작할 수 있습니다."
