#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   OpenGemini & Claude Telegram Bot 자동 설치 스크립트   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""

# 1. 시스템 요구사항 확인 (OS 체크)
OS="$(uname -s)"
echo -e "${YELLOW}[1/5] 운영체제 확인 중... (${OS})${NC}"
sleep 1

# 필수 패키지 확인 함수
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}오류: '$1' 명령어를 찾을 수 없습니다.${NC}"
        if [ "$OS" = "Linux" ]; then
            echo "Ubuntu/Debian: sudo apt install $1"
        elif [ "$OS" = "Darwin" ]; then
            echo "macOS: brew install $1"
        fi
        exit 1
    fi
}

check_command "python3"
check_command "git"
check_command "npm"

# 2. 전역 CLI 패키지 설치
echo -e "
${YELLOW}[2/5] AI 코딩 에이전트 CLI 설치 중 (권한이 필요할 수 있습니다)...${NC}"
echo "=> Google Gemini CLI 설치 중..."
npm install -g @google/gemini-cli
echo "=> Anthropic Claude Code 설치 중..."
npm install -g @anthropic-ai/claude-code

# CLI 경로 찾기
GEMINI_PATH=$(which gemini)
CLAUDE_PATH=$(which claude)

if [ -z "$GEMINI_PATH" ]; then
    echo -e "${RED}Gemini CLI 설치 경로를 찾을 수 없습니다. 수동 설정이 필요할 수 있습니다.${NC}"
    GEMINI_PATH="gemini"
fi

# 3. 프로젝트 클론 및 파이썬 환경 설정
echo -e "
${YELLOW}[3/5] Python 가상환경 설정 중...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}오류: 파이썬 가상환경(venv) 생성에 실패했습니다. (python3-venv 패키지가 필요할 수 있음)${NC}"
        exit 1
    fi
fi

source venv/bin/activate
echo "=> 필요한 파이썬 라이브러리 설치 중..."
pip install --upgrade pip > /dev/null 2>&1
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
else
    pip install python-telegram-bot pexpect python-dotenv
fi

# 4. 환경 변수(.env) 설정
echo -e "
${YELLOW}[4/5] 텔레그램 봇 설정 (환경 변수)${NC}"
echo "텔레그램 봇 토큰과 사용자 ID가 필요합니다."
echo "※ BotFather(@BotFather)에서 발급받은 토큰을 입력하세요."
read -p "텔레그램 Bot Token: " TG_TOKEN

echo "※ 본인의 텔레그램 숫자 ID를 입력하세요. (@userinfobot 에서 확인 가능)"
read -p "텔레그램 User ID: " TG_USER_ID

# .env 파일 생성
cat > .env << EOL
# 텔레그램 설정
TELEGRAM_TOKEN=${TG_TOKEN}
ALLOWED_USER_ID=${TG_USER_ID}

# CLI 바이너리 경로
GEMINI_BIN=${GEMINI_PATH}
CLAUDE_BIN=${CLAUDE_PATH}

# 기본 설정
DEFAULT_ENGINE=gemini
GEMINI_MODEL=gemini-2.5-pro
GEMINI_APPROVAL_MODE=yolo
GEMINI_WORKDIR=$(pwd)/workspace
EOL

mkdir -p workspace

echo -e "
${GREEN}설정이 .env 파일에 저장되었습니다!${NC}"

# 5. 첫 실행 안내
echo -e "
${YELLOW}[5/5] 인증 및 실행 안내${NC}"
echo "봇을 사용하기 전에, CLI 최초 로그인이 필요합니다."
echo -e "1. 터미널에 ${GREEN}gemini auth${NC} 를 입력하여 구글 계정으로 로그인하세요."
echo -e "2. (선택) ${GREEN}claude login${NC} 을 입력하여 클로드에 로그인하세요."
echo -e "3. 로그인이 끝나면 ${GREEN}bash start_bot.sh${NC} 또는 ${GREEN}python bot.py${NC} 로 봇을 실행하세요!"
echo ""
echo -e "${GREEN}설치가 모두 완료되었습니다. 즐거운 코딩 되세요! 🚀${NC}"
