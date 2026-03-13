# 🤖 OpenGemini & Claude Telegram Bot (Beginner's Guide)

[Korean Version (한국어 버전)](README.md)

This project is a personal automation bot that allows you to fully utilize powerful AI coding agents like **Google Gemini** and **Anthropic Claude** right from your smartphone (Telegram).
Even if you don't know how to code, just follow the steps below slowly, and anyone can create their own AI assistant!

---

## 📌 Table of Contents

1. [Prerequisites (Telegram Setup)](#1-prerequisites-telegram-setup)
2. [Super Simple 1-Minute Install (Mac, Linux, Windows WSL)](#2-super-simple-1-minute-install-automated-script)
3. [Detailed OS-Specific Installation Guide (Manual)](#3-detailed-os-specific-installation-guide)
   - [Windows Users](#windows-users)
   - [Mac (Apple) Users](#mac-users)
   - [Linux (Ubuntu) Users](#linux-ubuntu-users)
4. [Initial Authentication & Running the Bot](#4-initial-authentication--running-the-bot)
5. [Bot Commands & Usage](#5-bot-commands--usage)
6. [Frequently Asked Questions (FAQ)](#6-frequently-asked-questions-faq)

---

## 1. Prerequisites (Telegram Setup)

To use this bot safely by yourself, you need two pieces of information: a **'Bot Token'** and your **'User ID'**.

### 🔑 1) Getting a Bot Token
1. Open the Telegram app.
2. Search for **`@BotFather`** in the top search bar and enter the chat with the blue checkmark (official account).
3. Press the **[Start]** button at the bottom of the screen.
4. Type `/newbot` in the message box and send it.
5. Enter a **Name** for your bot (e.g., `My Coding Assistant`) and send.
6. Enter a **Username** for your bot (must end in `_bot`, e.g., `my_super_coding_bot`) and send.
7. You will receive a congratulatory message containing a long mix of English letters and numbers.
   *(e.g., `1234567890:ABCdefGhIjKlMnOpQrStUvWxYz`)*
   👉 **Copy this value and save it in a notepad! (This is your TELEGRAM_TOKEN)**

### 🆔 2) Finding Your Telegram User ID
This step ensures that only your ID is allowed to use the bot, preventing others from accessing it.
1. Search for **`@userinfobot`** in the Telegram search bar and enter the chat.
2. Press the **[Start]** button.
3. You will see a number like `Id: 123456789` on the screen.
   👉 **Copy this number and save it in your notepad as well! (This is your ALLOWED_USER_ID)**

---

## 2. Super Simple 1-Minute Install (Automated Script)

If you know how to open a Terminal or Command Prompt, simply copy the one line of command below, paste it, and press Enter. The entire installation will proceed automatically.
*(Windows users should first complete the WSL installation in `3. Detailed OS-Specific Installation Guide` below before doing this.)*

```bash
curl -fsSL https://raw.githubusercontent.com/GNchoo/OpenGemini-Cli-Claude-code/main/install.sh | bash
```

**If you are prompted during installation:**
1. `Telegram Bot Token:` Paste the **Bot Token** you saved earlier and press Enter.
2. `Telegram User ID:` Paste the **Number ID** you saved earlier and press Enter.

Once complete, you can skip directly to **[4. Initial Authentication & Running the Bot](#4-initial-authentication--running-the-bot)**!

---

## 3. Detailed OS-Specific Installation Guide

If the automatic installation above fails, or if you prefer to install things manually step-by-step, follow the guide below.

### Windows Users
On Windows, you cannot run it directly; you first need to create a 'Fake Linux (WSL)' inside your computer. It is not difficult at all!

**[Step 1] Install Linux (WSL)**
1. Click the **Start button** at the bottom left of your computer screen → search for `PowerShell`.
2. Right-click on `Windows PowerShell` → click **"Run as administrator"**.
3. When the black window appears, copy and paste the text below and press Enter.
   ```powershell
   wsl --install
   ```
4. Once it says installation is complete, **restart your computer**.

**[Step 2] Start Ubuntu (Linux)**
1. After the computer turns on, press the Start button again and search for `Ubuntu` to run it.
2. The first time you turn it on, it will ask you to wait a few minutes for installation.
3. When `Enter new UNIX username:` appears, type the **English name** you want to use (e.g., `kim`) and press Enter.
4. When `New password:` appears, set a **password**. (Nothing will show on the screen as you type, but it is being entered. Type with confidence.) Press Enter and re-enter to confirm.
5. Ta-da! The Linux window is ready. Now, type the commands below line by line and press Enter.
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git curl python3 python3-venv python3-pip
   ```
   (If it asks for a password, just type the password you set earlier.)

**[Step 3] Run Automatic Installation**
Now, copy and paste the command from **[2. Super Simple 1-Minute Install]** above!

---

### Mac Users
Mac users will use an app called `Terminal`.
1. Press `Command(⌘) + Space` on your keyboard to open Spotlight, search for `Terminal`, and run it.
2. Copy/paste the command below and press Enter.
   *(This installs a helper tool called Homebrew. It may ask for your Mac password.)*
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Once the installation is complete, install the required programs (Git, Python, Node) with the command below.
   ```bash
   brew install git python node
   ```
4. Now, copy and paste the command from **[2. Super Simple 1-Minute Install]** above!

---

### Linux (Ubuntu) Users
1. Open the Terminal and install the basic programs with the command below.
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git curl nodejs npm python3 python3-venv python3-pip
   ```
2. Now, copy and paste the command from **[2. Super Simple 1-Minute Install]** above!

---

## 4. Initial Authentication & Running the Bot

If the installation script finished successfully, the final step is to **give AI (Gemini, Claude) permission (login)** to use your account.

### 1) Gemini Login (Required)
Type the command below in the Terminal window.
```bash
gemini auth
```
An internet browser window will open. (If it doesn't, manually copy the address starting with `https://...` from the screen and paste it into your browser.)
Log in with your Google account and click "Allow" for everything, and you're done!

### 2) Claude Login (Optional - Only if you want to use Claude)
Type the command below in the Terminal window.
```bash
claude login
```
Similarly, a browser will open asking you to log in. Return to the Terminal window once completed.

### 3) Run the Bot!
It's finally time to turn on the bot. Type the command below in the project folder.
```bash
# Turn on the bot (If you close this window, the bot will turn off)
python bot.py
```
If you see the text `OpenGemini Agent bot polling...` on the screen, it's a success!
Now, open Telegram on your smartphone, enter the bot name you created earlier, and try talking to it.

> **💡 Tip: How do I keep the bot running even if I turn off the computer or close the Terminal?**
> Type `bash start_bot.sh` in the Terminal, and it will keep running quietly in the background.

---

## 5. Bot Commands & Usage

Enter the commands below in the Telegram bot chat room.
(You can also press the `/` button at the bottom left of the chat window to see the menu.)

| Command | When to use |
|---|---|
| `/start` | To check if the bot is alive. It will give a greeting. |
| `/help` | When you want to see the available features again. |
| `/engine` | Brings up a button to switch between Google (Gemini) and Claude. |
| `/model` | Choose whether the bot uses a smart version (Pro) or a fast/cheap version (Flash/Haiku). |
| `/workspace [Path]` | Specify which folder on your computer the bot should work in. (e.g., `/workspace /home/my/docs`) |
| `/coding` | Changes the bot to a perfect 'expert programmer' mode. Coding ability is maximized. |
| `/new` | Forgets previous conversation contexts and starts fresh. |

**Conversation Example:**
> **You:** "Hi! Create an index.html file in my workspace folder. Make the background black and write 'Hello World' in the center." <br>
> **Bot:** (After thinking for a moment) "Yes, I created the file!" (Simultaneously shoots the completed html file directly to your Telegram on your smartphone!)

---

## 6. Frequently Asked Questions (FAQ)

**Q. The bot is ignoring me and not answering!**
1. Check the Terminal window where you turned on the bot to see if any errors occurred.
2. You might have mixed up the `Telegram Bot Token` and `User ID`. Open the `.env` file in the folder to double-check if the numbers are correct.

**Q. How do I open and check the file? (How to edit the `.env` file)**
Type `nano .env` in the Terminal, and a notepad-like screen will open. Move with the arrow keys on your keyboard to fix the content, then press **`Ctrl + X`**, press **`Y`**, and hit **`Enter`** to save and exit.

**Q. Are Gemini and Claude free?**
The CLI tools themselves are provided for free, but depending on the API policies of each company (Google, Anthropic) or your account status, there may be limits. You can use them freely within the free limits.

**Q. I want to leave the bot on forever (Auto-start on server reboot)**
If you are using a Raspberry Pi or Cloud Server (Linux), registering with `systemd` is recommended.
Type `nano ~/.config/systemd/user/opengemini.service` in the Terminal, paste the content below, and modify the paths to fit your situation.
*(Refer to the previous manual setup or the source code for the exact systemd template.)*
