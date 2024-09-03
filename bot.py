import asyncio
import json
import os
import secrets
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler
from telegram import ChatMemberAdministrator, ChatMemberOwner
from telegram.error import Unauthorized
from token_1 import token

# Import game and admin command modules
from game_commands import flip, dice, football, basketball, dart, expire
from admin_commands import broadcast, backup, add_allowed_id, remove_allowed_id, add_sudo_id, remove_sudo_id, tagquiz_enable, tagquiz_disable

# Global variables
OWNER_ID = 5667016949
BOT_DATA_FILE = 'bot_data.json'
USERS_FILE = 'users.json'
MESSAGE_COUNT = 0
ADMIN_TAG_INTERVAL = 90
SKIP_MESSAGES = 10
LAST_POLLED_BOT_ID = 5732300001

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def debug_globals():
    logger.info(f"Global Variables:")
    logger.info(f"OWNER_ID: {OWNER_ID}")
    logger.info(f"MESSAGE_COUNT: {MESSAGE_COUNT}")
    logger.info(f"ADMIN_TAG_INTERVAL: {ADMIN_TAG_INTERVAL}")
    logger.info(f"SKIP_MESSAGES: {SKIP_MESSAGES}")
    logger.info(f"LAST_POLLED_BOT_ID: {LAST_POLLED_BOT_ID}")

def load_json_data(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return default

def save_json_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def load_bot_data():
    data = load_json_data(BOT_DATA_FILE, {})
    if data:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        user_ids = set(data['user_ids'])
    else:
        start_date = datetime.now()
        user_ids = set()
        save_bot_data(start_date, user_ids)
    return start_date, user_ids

def save_bot_data(start_date, user_ids):
    data = {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "user_ids": list(user_ids)
    }
    save_json_data(BOT_DATA_FILE, data)

def load_users():
    return load_json_data(USERS_FILE, {})

def save_users(users):
    save_json_data(USERS_FILE, users)

def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def start(update: Update, context: CallbackContext) -> None:
    global start_date, user_ids
    user = update.effective_user
    user_id = user.id
    user_ids.add(user_id)
    users = load_users()

    if str(user_id) not in users:
        users[str(user_id)] = {
            "first_name": user.first_name,
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "wins": 0,
            "losses": 0
        }
        save_users(users)

    save_bot_data(start_date, user_ids)
    
    await update.message.reply_text(
        "Welcome! Use /coin to flip a coin, /dice to roll a dice, /football to play football, /basketball to play basketball, /dart to play darts, and /exp to expire your bets."
    )

async def profile(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    users = load_users()

    if str(user_id) not in users:
        await update.message.reply_text("Profile not found. Start a game to create a profile.")
        return

    user_profile = users[str(user_id)]
    profile_msg = f"Profile for {update.effective_user.first_name}:\n\nWins: {user_profile['wins']}\nLosses: {user_profile['losses']}\nStart Date: {user_profile['start_date']}"
    await update.message.reply_text(profile_msg)

async def message_handler(update: Update, context: CallbackContext) -> None:
    global LAST_POLLED_BOT_ID, MESSAGE_COUNT

    bot_id = context.bot.id
    MESSAGE_COUNT += 1

    if MESSAGE_COUNT % ADMIN_TAG_INTERVAL == 0:
        await tag_admins(context)

    if bot_id != LAST_POLLED_BOT_ID:
        LAST_POLLED_BOT_ID = bot_id
        await skip_message(update, context)

    if SKIP_COUNT > 0:
        SKIP_COUNT = 0

def main():
    global start_date, user_ids

    debug_globals()
    
    start_date, user_ids = load_bot_data()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))

    application.add_handler(MessageHandler(filters.TEXT, message_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
