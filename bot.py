import asyncio
import os
import secrets
import logging
from datetime import datetime
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from token_1 import token
from telegram.constants import ParseMode

MONGO_URI = 'mongodb+srv://zh666602:PDtM7vYlai7JY2iS@betbot.lgwmmus.mongodb.net/?retryWrites=true&w=majority&appName=Betbot'
client = MongoClient(MONGO_URI)
db = client['betbot']
bot_data_collection = db['bot_data']
allowed_ids_collection = db['allowed_ids']
sudo_ids_collection = db['sudo_ids']
OWNER_ID = 5667016949
lottery_entries = {}
lottery_active = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_bot_data():
    bot_data = bot_data_collection.find_one({'_id': 'bot_data'})
    if bot_data:
        start_date = datetime.strptime(bot_data['start_date'], '%Y-%m-%d')
        user_ids = set(bot_data['user_ids'])
    else:
        start_date = datetime.now()
        user_ids = set()
        save_bot_data(start_date, user_ids)
    return start_date, user_ids

def save_bot_data(start_date, user_ids):
    bot_data_collection.update_one(
        {'_id': 'bot_data'},
        {'$set': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'user_ids': list(user_ids)
        }},
        upsert=True
    )

def load_allowed_ids():
    allowed_ids_doc = allowed_ids_collection.find_one({'_id': 'allowed_ids'})
    if allowed_ids_doc:
        return set(allowed_ids_doc['allowed_ids'])
    return {OWNER_ID}

def save_allowed_ids(allowed_ids):
    allowed_ids_collection.update_one(
        {'_id': 'allowed_ids'},
        {'$set': {'allowed_ids': list(allowed_ids)}},
        upsert=True
    )

def load_sudo_ids():
    sudo_ids_doc = sudo_ids_collection.find_one({'_id': 'sudo_ids'})
    if sudo_ids_doc:
        return set(sudo_ids_doc['sudo_ids'])
    return {OWNER_ID}

def save_sudo_ids(sudo_ids):
    sudo_ids_collection.update_one(
        {'_id': 'sudo_ids'},
        {'$set': {'sudo_ids': list(sudo_ids)}},
        upsert=True
    )

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

async def lottery(update: Update, context: CallbackContext) -> None:
    global lottery_active, lottery_entries
    user_id = update.effective_user.id
    if user_id not in allowed_ids:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    lottery_active = True
    lottery_entries = {}
    await update.message.reply_text("The lottery has started! Use /joinlottery <number> to join.")

async def join_lottery(update: Update, context: CallbackContext) -> None:
    global lottery_active, lottery_entries
    user = update.effective_user
    user_id = user.id

    if not lottery_active:
        await update.message.reply_text("There is no active lottery. Please wait for the host to start one.")
        return
    
    if user_id in lottery_entries:
        await update.message.reply_text("You have already joined the lottery.")
        return
    
    try:
        number = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid number to join the lottery.")
        return
    
    if number in lottery_entries.values():
        await update.message.reply_text("This number is already taken. Please choose another number.")
        return

    lottery_entries[user_id] = number
    user_link = f"<a href='tg://user?id={user_id}'>{escape_markdown_v2(user.first_name)}</a>"
    await update.message.reply_text(f"{user_link} has joined the lottery with number {number}!", parse_mode='HTML')

async def end_lottery(update: Update, context: CallbackContext) -> None:
    global lottery_active, lottery_entries
    user_id = update.effective_user.id
    if user_id not in allowed_ids:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    if not lottery_active:
        await update.message.reply_text("There is no active lottery.")
        return
    
    if not lottery_entries:
        await update.message.reply_text("No one has joined the lottery yet.")
        return
    
    winning_number = secrets.choice(list(lottery_entries.values()))
    winners = [uid for uid, number in lottery_entries.items() if number == winning_number]
    if winners:
        for winner in winners:
            user_link = f"<a href='tg://user?id={winner}'>{escape_markdown_v2(context.bot.get_chat(winner).first_name)}</a>"
            await update.message.reply_text(f"The lottery has ended! The winning number is {winning_number}. Congratulations {user_link}!", parse_mode='HTML')
    else:
        await update.message.reply_text(f"The lottery has ended! The winning number is {winning_number}. No one won this time.")
    
    lottery_active = False
    lottery_entries = {}

async def grant(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    try:
        target_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return
    
    allowed_ids.add(target_id)
    save_allowed_ids(allowed_ids)
    await update.message.reply_text(f"User {target_id} has been granted permission to use the bot.")

async def revoke(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    try:
        target_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return
    
    if target_id in allowed_ids:
        allowed_ids.remove(target_id)
        save_allowed_ids(allowed_ids)
        await update.message.reply_text(f"User {target_id} has been revoked permission to use the bot.")
    else:
        await update.message.reply_text(f"User {target_id} does not have permission to be revoked.")

async def sudo(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    try:
        target_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return
    
    sudo_ids.add(target_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User {target_id} has been granted sudo access.")

async def unsudo(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    try:
        target_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return
    
    if target_id in sudo_ids:
        sudo_ids.remove(target_id)
        save_sudo_ids(sudo_ids)
        await update.message.reply_text(f"User {target_id} has been revoked sudo access.")
    else:
        await update.message.reply_text(f"User {target_id} does not have sudo access to be revoked.")

def main() -> None:
    global start_date, user_ids, allowed_ids, sudo_ids
    start_date, user_ids = load_bot_data()
    allowed_ids = load_allowed_ids()
    sudo_ids = load_sudo_ids()
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("coin", flip))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("football", football))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("exp", expire))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("inlinestart", inline_start))
    application.add_handler(CommandHandler("lottery", lottery))
    application.add_handler(CommandHandler("joinlottery", join_lottery))
    application.add_handler(CommandHandler("endlottery", end_lottery))
    application.add_handler(CommandHandler("grant", grant))
    application.add_handler(CommandHandler("revoke", revoke))
    application.add_handler(CommandHandler("sudo", sudo))
    application.add_handler(CommandHandler("unsudo", unsudo))
    
    application.run_polling()

if __name__ == '__main__':
    main()
