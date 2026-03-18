# OpenGemini 🤖 (2026 Edition)

Gemini CLI와 Claude Code를 텔레그램으로 제어하는 강력한 에이전트 봇입니다. 2026년 3월 기준 최신 모델(Gemini 3.1, 3, 2.5)과 클로드 코드(Claude Code)를 완벽하게 지원하며, 엔진 간 대화 맥락이 실시간으로 동기화됩니다.

## 주요 기능 (2026)

- **Gemini 3 시리즈 지원**: `gemini-3.1-pro-preview`, `gemini-3-flash-preview` 등 최신 모델 완벽 대응.
- **Claude Code 통합**: `claude` 엔진을 통해 고성능 코딩 에이전트 기능을 텔레그램에서 사용.
- **실시간 엔진 동기화 (Sync)**: Gemini와 Claude가 서로의 답변을 기억하며 대화를 이어갑니다.
- **OpenClaw 공유 세션 연동**: `CONTEXT.md`, `TODO.md` 등을 통해 다른 에이전트 시스템과 작업 맥락을 공유합니다.
- **무중단 비대화형 실행**: `--print` 및 `--output-format` 최적화로 프리징 없는 빠른 응답.

## 빠른 시작 (One-Click Setup)

명령어 한 줄로 모든 환경 세팅을 완료할 수 있습니다.

```bash
git clone https://github.com/GNchoo/OpenGemini-Cli-Claude-code.git
cd OpenGemini-Cli-Claude-code
bash setup.sh
```

### 1. 설정 (Config)
`.env` 파일을 열어 다음 정보를 입력하세요:
- `TELEGRAM_TOKEN`: 봇 파더로부터 받은 토큰
- `ALLOWED_USER_ID`: 봇을 사용할 사용자 ID

### 2. 실행 (Start)
```bash
bash start_bot.sh
```

## 주요 명령어

- `/engine`: Gemini와 Claude 엔진 간 즉시 전환.
- `/model`: 지원되는 최신 모델 목록 확인 및 선택.
- `/status`: 현재 엔진, 모델, 세션 상태 및 가동 시간 확인.
- `/clear`: 현재 대화 기록(Transcript) 초기화.

## 공유 세션 (Shared Session) 연동

이 봇은 `~/.openclaw/workspace/shared-session/` 경로의 파일들을 자동으로 감지하여 맥락에 주입합니다.
- `CONTEXT.md`: 장기 프로젝트 목표 및 규칙
- `TODO.md`: 실시간 할 일 목록 (JSON 포맷)
- `LAST_RESULT.md`: 마지막 작업 결과

## 라이선스
MIT License
