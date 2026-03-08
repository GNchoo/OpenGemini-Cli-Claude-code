#!/bin/bash
cd /home/fallman/tools/OpenGemini
pkill -9 -f bot.py
pkill -9 -f claude
rm -f .bot.lock
nohup venv/bin/python -u bot.py > bot_attempt15.log 2>&1 &
echo "Bot started with PID $!"
