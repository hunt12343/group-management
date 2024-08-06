import asyncio
import json
import os
import secrets
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from token_1 import token
from telegram.constants import ParseMode
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb+srv://zh666602:PDtM7vYlai7JY2iS@betbot.lgwmmus.mongodb.net/?retryWrites=true&w=majority")
db = client.betbot
bot_data_collection = db.bot_data
allowed_ids_collection = db.allowed_ids
sudo_ids_collection = db.sudo_ids

# Global variables
OWNER_ID = 5667016949
lottery_entries = {}
lottery_active = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_bot_data():
    data = bot_data_collection.find_one({"_id": "bot_data"})
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
    bot_data_collection.update_one({"_id": "bot_data"}, {"$set": data}, upsert=True)

def load_allowed_ids():
    data = allowed_ids_collection.find_one({"_id": "allowed_ids"})
    if data:
        return set(data['user_ids'])
    return {OWNER_ID}

def save_allowed_ids(allowed_ids):
    data = {"_id": "allowed_ids", "user_ids": list(allowed_ids)}
    allowed_ids_collection.update_one({"_id": "allowed_ids"}, {"$set": data}, upsert=True)

def load_sudo_ids():
    data = sudo_ids_collection.find_one({"_id": "sudo_ids"})
    if data:
        return set(data['user_ids'])
    return {OWNER_ID}

def save_sudo_ids(sudo_ids):
    data = {"_id": "sudo_ids", "user_ids": list(sudo_ids)}
    sudo_ids_collection.update_one({"_id": "sudo_ids"}, {"$set": data}, upsert=True)

def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_ids.add(user_id)
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
    user_id = update.effective_user.id
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
    user_id = update.effective_user.id
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
    user_id = update.effective_user.id
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
    user_id = update.effective_user.id
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
    user_id = update.effective_user.id
    await update.message.reply_text("Your all bets are expired")

async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in allowed_ids:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
        except Exception as e:
            logger.error(f"Failed to send message to {uid}: {e}")

async def inline_start(update: Update, context: CallbackContext) -> None:
    button = InlineKeyboardButton("Start Bot", url=f"https://t.me/{context.bot.username}?start=start")
    reply_markup = InlineKeyboardMarkup([[button]])
    await update.message.reply_text("Please start the bot by clicking the button below:", reply_markup=reply_markup)

async def add_allowed_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        new_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    allowed_ids.add(new_id)
    save_allowed_ids(allowed_ids)
    await update.message.reply_text(f"User ID {new_id} has been added to allowed IDs.")

async def remove_allowed_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        remove_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    allowed_ids.discard(remove_id)
    save_allowed_ids(allowed_ids)
    await update.message.reply_text(f"User ID {remove_id} has been removed from allowed IDs.")

async def add_sudo(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        sudo_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    sudo_ids.add(sudo_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {sudo_id} has been added to sudo IDs.")

async def remove_sudo(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        sudo_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    sudo_ids.discard(sudo_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {sudo_id} has been removed from sudo IDs.")

async def main() -> None:
    application = Application.builder().token(token).build()

    start_handler = CommandHandler("start", start)
    flip_handler = CommandHandler("flip", flip)
    dice_handler = CommandHandler("dice", dice)
    football_handler = CommandHandler("football", football)
    basketball_handler = CommandHandler("basketball", basketball)
    dart_handler = CommandHandler("dart", dart)
    expire_handler = CommandHandler("expire", expire)
    broadcast_handler = CommandHandler("broadcast", broadcast)
    inline_start_handler = CommandHandler("inline_start", inline_start)
    add_allowed_id_handler = CommandHandler("add_allowed_id", add_allowed_id)
    remove_allowed_id_handler = CommandHandler("remove_allowed_id", remove_allowed_id)
    add_sudo_handler = CommandHandler("add_sudo", add_sudo)
    remove_sudo_handler = CommandHandler("remove_sudo", remove_sudo)

    application.add_handler(start_handler)
    application.add_handler(flip_handler)
    application.add_handler(dice_handler)
    application.add_handler(football_handler)
    application.add_handler(basketball_handler)
    application.add_handler(dart_handler)
    application.add_handler(expire_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(inline_start_handler)
    application.add_handler(add_allowed_id_handler)
    application.add_handler(remove_allowed_id_handler)
    application.add_handler(add_sudo_handler)
    application.add_handler(remove_sudo_handler)

    # Load bot data
    global start_date, user_ids, allowed_ids, sudo_ids
    start_date, user_ids = load_bot_data()
    allowed_ids = load_allowed_ids()
    sudo_ids = load_sudo_ids()

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
