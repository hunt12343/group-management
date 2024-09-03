import asyncio
import json
import os
import secrets
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
from token_1 import token

# Global variables
OWNER_ID = 5667016949
lottery_entries = {}
BOT_DATA_FILE = 'bot_data.json'
ALLOWED_IDS_FILE = 'allowed_ids.json'
SUDO_IDS_FILE = 'sudo_ids.json'
USERS_FILE = 'users.json'

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

# Bot data functions
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

# ID management functions
def load_allowed_ids():
    return set(load_json_data(ALLOWED_IDS_FILE, [OWNER_ID]))

def save_allowed_ids(allowed_ids):
    save_json_data(ALLOWED_IDS_FILE, {"user_ids": list(allowed_ids)})

def load_sudo_ids():
    return set(load_json_data(SUDO_IDS_FILE, [OWNER_ID]))

def save_sudo_ids(sudo_ids):
    save_json_data(SUDO_IDS_FILE, {"user_ids": list(sudo_ids)})

# User data functions
def load_users():
    return load_json_data(USERS_FILE, {})

def save_users(users):
    save_json_data(USERS_FILE, {"users": users})

def update_user_credits(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["credits"] += amount
        save_users(users)

def update_user_win_loss(user_id, win=True):
    users = load_users()
    if str(user_id) in users:
        if win:
            users[str(user_id)]["win"] += 1
        else:
            users[str(user_id)]["loss"] += 1
        save_users(users)

# Markdown escaping for Telegram messages
def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)
    
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)  # Convert to string to match JSON storage

    users = load_users()

    if user_id not in users:
        # Initialize user data
        users[user_id] = {
            "user_id": user_id,
            "join_date": datetime.now().strftime('%m/%d/%y'),
            "credits": 50000,  # Starting credits
            "daily": None,
            "win": 0,
            "loss": 0,
            "achievement": [],
            "faction": "None",
            "ban": None,
            "title": "None"
        }
        save_users(users)
        logger.info(f"User {user_id} started the bot.")

    await update.message.reply_text(
        "Welcome! You've received 50,000 credits to start betting. Use /profile to check your details."
    )

async def profile(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)  # Ensure consistency with stored ID
    users = load_users()

    if user_id in users:
        user_data = users[user_id]
        profile_message = (
            f"👤 Name: {user.first_name} 【{user_data['faction']}】\n"
            f"🆔 ID: {user_data['user_id']}\n"
            f"Credits: {user_data['credits']} 👾\n\n"
            f"Win: {user_data['win']}\n"
            f"Loss: {user_data['loss']}\n\n"
            f"{user_data['title']}\n"
        )
        logger.info(f"User {user_id} checked their profile.")
    else:
        profile_message = "You have not started using the bot yet. Use /start to begin."
        logger.warning(f"User {user_id} tried to check profile without starting the bot.")

    await update.message.reply_text(profile_message)


async def flip(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        choice, bet_amount = context.args[0].upper(), int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /flip H 500 (H for Heads, T for Tails)")
        return

    if choice not in ["H", "T"]:
        await update.message.reply_text("Invalid choice. Choose either 'H' for heads or 'T' for tails.")
        return

    if bet_amount <= 0:
        await update.message.reply_text("Bet amount must be a positive number.")
        return

    if bet_amount > users[user_id]["credits"]:
        await update.message.reply_text("You don't have enough credits for this bet.")
        return

    result = secrets.choice(["H", "T"])
    if result == choice:
        users[user_id]["credits"] += bet_amount
        users[user_id]["win"] += 1
        message = f"🎉 You won! {bet_amount} credits have been added to your profile."
    else:
        users[user_id]["credits"] -= bet_amount
        users[user_id]["loss"] += 1
        message = f"😞 You lost! {bet_amount} credits have been deducted from your profile."

    save_users(users)
    await update.message.reply_text(message)


async def bet(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        bet_amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /bet 500")
        return

    if bet_amount <= 0 or bet_amount > users[user_id]["credits"]:
        await update.message.reply_text("Invalid bet amount or insufficient credits.")
        return

    result = secrets.choice(["win", "lose"])
    if result == "win":
        users[user_id]["credits"] += bet_amount
        users[user_id]["win"] += 1
        message = f"You won! {bet_amount} credits have been added to your profile."
    else:
        users[user_id]["credits"] -= bet_amount
        users[user_id]["loss"] += 1
        message = f"You lost! {bet_amount} credits have been deducted from your profile."

    save_users(users)
    await update.message.reply_text(message)


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

async def backup(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    files_to_send = [BOT_DATA_FILE, ALLOWED_IDS_FILE, SUDO_IDS_FILE, USERS_FILE]

    for file_path in files_to_send:
        try:
            with open(file_path, 'rb') as file:
                await context.bot.send_document(chat_id=OWNER_ID, document=file, filename=os.path.basename(file_path))
        except FileNotFoundError:
            await update.message.reply_text(f"File {file_path} not found.")
        except Exception as e:
            logger.error(f"Error sending file {file_path}: {e}")
            await update.message.reply_text(f"Error sending file {file_path}: {str(e)}")

    await update.message.reply_text("Backup completed successfully.")

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

    if remove_id in allowed_ids:
        allowed_ids.remove(remove_id)
        save_allowed_ids(allowed_ids)
        await update.message.reply_text(f"User ID {remove_id} has been removed from allowed IDs.")
    else:
        await update.message.reply_text(f"User ID {remove_id} was not found in allowed IDs.")

async def add_sudo_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        new_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    sudo_ids.add(new_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {new_id} has been added to sudo IDs.")

async def remove_sudo_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        remove_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if remove_id in sudo_ids:
        sudo_ids.remove(remove_id)
        save_sudo_ids(sudo_ids)
        await update.message.reply_text(f"User ID {remove_id} has been removed from sudo IDs.")
    else:
        await update.message.reply_text(f"User ID {remove_id} was not found in sudo IDs.")

# Initialize application and handlers
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
application.add_handler(CommandHandler("inline_start", inline_start))
application.add_handler(CommandHandler("add_allowed_id", add_allowed_id))
application.add_handler(CommandHandler("remove_allowed_id", remove_allowed_id))
application.add_handler(CommandHandler("add_sudo_id", add_sudo_id))
application.add_handler(CommandHandler("remove_sudo_id", remove_sudo_id))

if __name__ == '__main__':
    start_date, user_ids = load_bot_data()
    allowed_ids = load_allowed_ids()
    sudo_ids = load_sudo_ids()
    application.run_polling()
