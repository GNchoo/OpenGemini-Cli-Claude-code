import os
import pexpect
import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TELEGRAM_TOKEN = "REDACTED_TELEGRAM_TOKEN"
ALLOWED_USER_ID = REDACTED_USER_ID

# Global state for the gemini process
gemini_process: Optional[pexpect.spawn] = None
is_reading = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text('Hello! I am your Gemini CLI Telegram Agent. I am ready to accept prompts.')
    _ensure_gemini_running()

def _ensure_gemini_running():
    """Ensure the gemini process is running"""
    global gemini_process
    if gemini_process is None or not gemini_process.isalive():
        print("Starting new gemini process...")
        # Prepare environment with API key to bypass key prompt if supported
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = 'REDACTED_GEMINI_KEY'
        
        # Start gemini chat mode. 
        gemini_process = pexpect.spawn('/home/linuxbrew/.linuxbrew/bin/gemini chat', env=env, encoding='utf-8', timeout=0.1)
        # Handle initial prompts
        try:
            # Look for typical prompts or anything waiting for input
            while True:
                idx = gemini_process.expect([
                    r'Do you trust this folder\?',
                    r'Attempting to automatically update now',
                    r'Update successful',
                    r'Enter Gemini API Key',
                    pexpect.EOF,
                    pexpect.TIMEOUT
                ], timeout=2)
                
                if idx == 0:
                    # Trust folder prompt -> select option 1 and press Enter
                    print("Auto-trusting folder...")
                    gemini_process.sendline("1") # sendline sends \r\n
                elif idx == 1 or idx == 2:
                    # Update prompt -> wait a bit more
                    print("Handling update prompt...")
                    continue
                elif idx == 3:
                    print("Auto-providing API key...")
                    gemini_process.sendline("REDACTED_GEMINI_KEY")
                else:
                    # Timeout or EOF -> initial setup is likely done
                    break
                    
        except Exception as e:
            print(f"Error during initial prompt handling: {e}")
            pass
            
        # Drain any remaining initial output
        try:
            gemini_process.read_nonblocking(size=10000, timeout=1)
        except (pexpect.TIMEOUT, pexpect.EOF):
            pass

async def _read_and_send_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Wait for response from gemini_process and stream it back."""
    global is_reading
    is_reading = True
    full_response = ""
    idle_count = 0
    max_idle = 20  # 2 seconds without output -> assume generation finished
    
    try:
        while is_reading:
            try:
                # Read a chunk of output
                chunk = gemini_process.read_nonblocking(size=1024, timeout=0.1)
                full_response += chunk
                idle_count = 0
            except pexpect.TIMEOUT:
                # No new output in this 0.1s window. Check if we should stop.
                idle_count += 1
                if idle_count >= max_idle:
                    break
            except pexpect.EOF:
                # Process died
                full_response += "\n[System: Gemini process terminated]"
                break
                
            await asyncio.sleep(0.01)
            
    finally:
        is_reading = False
        
    # Clean up the response (remove the prompt echoes and CLI artifacts if any)
    response_text = full_response.strip()
    
    # Send the response back to Telegram in chunks if it's too long
    if response_text:
        # Telegram max message length is 4096
        chunk_size = 4000
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            if chunk.strip():
                try:
                    await update.message.reply_text(chunk)
                except Exception as e:
                    print(f"Error sending message: {e}")
    else:
        await update.message.reply_text("[No output received from Gemini]")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages from the allowed user and forward them to gemini."""
    global gemini_process
    
    if update.effective_user.id != ALLOWED_USER_ID:
        print(f"Blocked message from unauthorized user: {update.effective_user.id}")
        return

    text = update.message.text
    if not text:
        return

    _ensure_gemini_running()
    
    # Send the user's text to the gemini process
    gemini_process.sendline(text)
    
    # Send an initial typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    await _read_and_send_response(update, context)

async def restart_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to forcibly restart the backend gemini process."""
    global gemini_process
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    if gemini_process and gemini_process.isalive():
        gemini_process.terminate(force=True)
    
    _ensure_gemini_running()
    await update.message.reply_text("Backend Gemini process restarted.")

async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pass /model command to the backend gemini process."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    _ensure_gemini_running()
    
    # Extract the command and args (e.g. /model pro)
    text = update.message.text
    gemini_process.sendline(text)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    await _read_and_send_response(update, context)

async def update_cli(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run npm install -g gemini to update the underlying CLI."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    await update.message.reply_text("Updating Gemini CLI... This may take a minute.")
    
    # We run this in the shell, not through the pexpect chat process
    process = await asyncio.create_subprocess_shell(
        'npm install -g gemini',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    # Send the result back
    result = "[Update Result]\n"
    if stdout:
        result += stdout.decode()
    if stderr:
        result += f"\nErrors:\n{stderr.decode()}"
        
    # Chunk and send
    chunk_size = 4000
    for i in range(0, len(result), chunk_size):
        chunk = result[i:i+chunk_size]
        if chunk.strip():
            await update.message.reply_text(chunk)
            
    # Restart the backend process so it picks up the new version
    await restart_process(update, context)

async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help text with available commands."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    help_text = (
        "🤖 **Telegram Gemini CLI Agent**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/restart - Restart the backend Gemini process\n"
        "/model [name] - Switch the Gemini model (e.g., /model pro)\n"
        "/update - Update the Gemini CLI to the latest version via npm\n"
        "/help - Show this help message\n\n"
        "Any other text will be sent directly to the Gemini CLI chat interface."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart_process))
    application.add_handler(CommandHandler("model", set_model))
    application.add_handler(CommandHandler("update", update_cli))
    application.add_handler(CommandHandler("help", send_help))

    # General messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Gemini process before polling
    _ensure_gemini_running()

    print("Bot is polling...")
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
