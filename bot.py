import asyncio
import json
import os
import secrets
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, filters
from token_1 import token
from telegram import ChatMemberAdministrator, ChatMemberOwner
from telegram.error import Unauthorized

# Global variables
OWNER_ID = 5667016949
lottery_entries = {}
lottery_active = False
BOT_DATA_FILE = 'bot_data.json'
ALLOWED_IDS_FILE = 'allowed_ids.json'
SUDO_IDS_FILE = 'sudo_ids.json'
TAG_QUIZ_USERS_FILE = 'tag_quiz_users.json'
tag_quiz_users = set()
USERS_FILE = 'users.json'
MESSAGE_COUNT = 0
SKIP_COUNT = 0
ADMIN_TAG_INTERVAL = 90
SKIP_MESSAGES = 10
LAST_POLLED_BOT_ID = 5732300001

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def load_allowed_ids():
    data = load_json_data(ALLOWED_IDS_FILE, {"user_ids": [OWNER_ID]})
    return set(data["user_ids"])

def save_allowed_ids(allowed_ids):
    save_json_data(ALLOWED_IDS_FILE, {"user_ids": list(allowed_ids)})

def load_sudo_ids():
    data = load_json_data(SUDO_IDS_FILE, {"user_ids": [OWNER_ID]})
    return set(data["user_ids"])

def load_tag_quiz_users():
    global tag_quiz_users
    tag_quiz_users = set(load_json_data(TAG_QUIZ_USERS_FILE, []))

def save_tag_quiz_users():
    save_json_data(TAG_QUIZ_USERS_FILE, list(tag_quiz_users))

def save_sudo_ids(sudo_ids):
    save_json_data(SUDO_IDS_FILE, {"user_ids": list(sudo_ids)})

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

    # Check if user is already in the database
    if str(user_id) not in users:
        # Add user to the database with initial values
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

async def flip(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    result = secrets.choice(["heads", "tails"])
    user_link = f"<a href='tg://user?id={user.id}'>{escape_markdown_v2(user.first_name)}</a>"
    message = f"『 {user_link} 』flipped a coin!\n\nIt's {result}! Timestamp: {datetime.now()}"
    if update.message.reply_to_message:
        original_msg_id = update.message.reply_to_message.message_id
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML', reply_to_message_id=original_msg_id)
    else:
        await update.message.reply_text(message, parse_mode='HTML')

async def dice(update: Update, context: CallbackContext) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        if update.message.reply_to_message:
            user_dice_msg_id = update.message.reply_to_message.message_id
            await context.bot.send_dice(chat_id=update.effective_chat.id, reply_to_message_id=user_dice_msg_id)
        else:
            await update.message.reply_text("Please reply to a user's message to roll a dice for them.")
    else:
        await context.bot.send_dice(chat_id=update.effective_chat.id)

async def football(update: Update, context: CallbackContext) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        if update.message.reply_to_message:
            user_msg_id = update.message.reply_to_message.message_id
            await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='⚽', reply_to_message_id=user_msg_id)
        else:
            await update.message.reply_text("Please reply to a user's message to play football for them.")
    else:
        await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='⚽')

async def basketball(update: Update, context: CallbackContext) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        if update.message.reply_to_message:
            user_msg_id = update.message.reply_to_message.message_id
            await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🏀', reply_to_message_id=user_msg_id)
        else:
            await update.message.reply_text("Please reply to a user's message to play basketball for them.")
    else:
        await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🏀')

async def dart(update: Update, context: CallbackContext) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        if update.message.reply_to_message:
            user_msg_id = update.message.reply_to_message.message_id
            await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎯', reply_to_message_id=user_msg_id)
        else:
            await update.message.reply_text("Please reply to a user's message to play darts for them.")
    else:
        await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎯')

async def expire(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"User {user.first_name} requested to expire their bets."
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

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_ids = list(user_ids)  # Convert set to list for iteration
    message_text = update.message.text.split(None, 1)[1]
    failed_users = []

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text)
        except Unauthorized:
            logger.warning(f"User {user_id} has blocked the bot.")
            failed_users.append(user_id)

    for user_id in failed_users:
        user_ids.remove(user_id)
    save_bot_data(start_date, user_ids)

async def tag_admins(context: CallbackContext) -> None:
    bot = context.bot
    message = f"Admin, this is a periodic check-in.\nTotal messages processed: {MESSAGE_COUNT}"

    for admin_id in context.job.context['admin_ids']:
        try:
            await bot.send_message(admin_id, message)
        except Unauthorized:
            logger.warning(f"Admin {admin_id} has blocked the bot.")

async def tagquiz_enable(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    tag_quiz_users.add(user_id)
    save_tag_quiz_users()
    await update.message.reply_text("You have been added to the tag quiz users list.")

async def tagquiz_disable(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in tag_quiz_users:
        tag_quiz_users.remove(user_id)
        save_tag_quiz_users()
        await update.message.reply_text("You have been removed from the tag quiz users list.")
    else:
        await update.message.reply_text("You are not in the tag quiz users list.")

async def skip_message(update: Update, context: CallbackContext) -> None:
    global MESSAGE_COUNT, SKIP_COUNT
    MESSAGE_COUNT += 1

    if MESSAGE_COUNT >= SKIP_MESSAGES:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"The bot has processed {MESSAGE_COUNT} messages since the last check."
        )
        SKIP_COUNT += 1
        MESSAGE_COUNT = 0

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

async def backup(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    with open(BOT_DATA_FILE, 'rb') as file:
        await context.bot.send_document(chat_id=OWNER_ID, document=file)

async def add_allowed_id(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    new_id = int(context.args[0])
    allowed_ids.add(new_id)
    save_allowed_ids(allowed_ids)
    await update.message.reply_text(f"User ID {new_id} added to allowed IDs.")

async def remove_allowed_id(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    remove_id = int(context.args[0])
    allowed_ids.discard(remove_id)
    save_allowed_ids(allowed_ids)
    await update.message.reply_text(f"User ID {remove_id} removed from allowed IDs.")

async def add_sudo_id(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    new_id = int(context.args[0])
    sudo_ids.add(new_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {new_id} added to sudo IDs.")

async def remove_sudo_id(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    remove_id = int(context.args[0])
    sudo_ids.discard(remove_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {remove_id} removed from sudo IDs.")

def main():
    global start_date, user_ids, allowed_ids, sudo_ids, tag_quiz_users
    start_date, user_ids = load_bot_data()
    allowed_ids = load_allowed_ids()
    sudo_ids = load_sudo_ids()
    load_tag_quiz_users()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("football", football))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("expire", expire))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("add_allowed_id", add_allowed_id))
    application.add_handler(CommandHandler("remove_allowed_id", remove_allowed_id))
    application.add_handler(CommandHandler("add_sudo_id", add_sudo_id))
    application.add_handler(CommandHandler("remove_sudo_id", remove_sudo_id))
    application.add_handler(CommandHandler("tagquiz_enable", tagquiz_enable))
    application.add_handler(CommandHandler("tagquiz_disable", tagquiz_disable))

    application.add_handler(filters.MessageHandler(filters.TEXT, message_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
