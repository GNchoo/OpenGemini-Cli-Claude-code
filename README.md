# OpenGemini Agent Platform

OpenGemini is a powerful AI agent platform that brings advanced agentic capabilities to Telegram. It integrates `gemini-cli` and `claude-code` to provide a seamless interactive coding and automation experience.

## ✨ Key Features

- 🤖 **Multi-Engine support**: Switch between Google Gemini and Claude Code (`/engine`).
- 🛠️ **Interactive Tool Approval**: Approve or reject shell commands and file edits via Telegram buttons.
- 💻 **Coding Agent Mode**: Specialized system prompts for software development (`/coding`).
- 📁 **Workspace Isolation**: Manage files within dedicated, configurable directories (`/workspace`).
- 🔄 **Persistent Sessions**: Independent conversation history per chat and per engine.

## 🚀 Getting Started

### Prerequisites

- Node.js (for `gemini-cli` and `claude-code`)
- Python 3.10+
- Telegram Bot Token

### Installation

1. Install dependencies:
   ```bash
   pip install python-telegram-bot pexpect python-dotenv
   npm install -g @google/gemini-cli
   # Install claude-code if available
   ```

2. Configure `.env`:
   ```env
   TELEGRAM_TOKEN=your_bot_token
   ALLOWED_USER_ID=your_id
   GEMINI_API_KEY=your_api_key
   GEMINI_WORKDIR=/home/fallman/projects
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## ⌨️ Bot Commands

- `/start` - Initialize the agent platform.
- `/engine [gemini|claude]` - Switch AI engines.
- `/coding` - Activate specialized coding-agent mode.
- `/mode [default|plan|yolo]` - Set tool approval strictness.
- `/workspace [path]` - Change active working directory.
- `/status` - Check engine and session state.
- `/new` - Reset current session.

## 🛡️ Security

OpenGemini supports a **Sandbox Mode** for Gemini CLI to ensure safe execution of generated scripts. Use `/mode yolo` only if you trust the model completely.
