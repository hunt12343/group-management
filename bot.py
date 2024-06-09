import json
import os
import secrets
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from token_1 import token

DATA_FILE = 'bot_data.json'
ALLOWED_IDS_FILE = 'allowed_ids.json'
SUDO_IDS_FILE = 'sudo_ids.json'
OWNER_ID = 5667016949
lottery_entries = {}
lottery_active = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_bot_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
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
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file)

def load_allowed_ids():
    if os.path.exists(ALLOWED_IDS_FILE):
        with open(ALLOWED_IDS_FILE, 'r') as file:
            return set(json.load(file))
    return {OWNER_ID}

def save_allowed_ids(allowed_ids):
    with open(ALLOWED_IDS_FILE, 'w') as file:
        json.dump(list(allowed_ids), file)

def load_sudo_ids():
    if os.path.exists(SUDO_IDS_FILE):
        with open(SUDO_IDS_FILE, 'r') as file:
            return set(json.load(file))
    return {OWNER_ID}

def save_sudo_ids(sudo_ids):
    with open(SUDO_IDS_FILE, 'w') as file:
        json.dump(list(sudo_ids), file)

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
    global lottery_active
    user_id = update.effective_user.id
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
    
    lottery_entries[user_id] = number
    await update.message.reply_text(f"You have joined the lottery with number {number}.")

async def start_lottery(update: Update, context: CallbackContext) -> None:
    global lottery_active
    user_id = update.effective_user.id
    if user_id not in allowed_ids:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    
    if not lottery_active:
        await update.message.reply_text("There is no active lottery to start.")
        return
    
    if not lottery_entries:
        await update.message.reply_text("No one has joined the lottery yet.")
        return

    dice_values = []
    for _ in range(3):
        dice_msg = await context.bot.send_dice(chat_id=update.effective_chat.id)
        dice_values.append(dice_msg.dice.value)
    
    total = sum(dice_values)
    closest_user = None
    closest_diff = float('inf')
    
    for uid, number in lottery_entries.items():
        diff = abs(total - number)
        if diff < closest_diff:
            closest_diff = diff
            closest_user = uid
    
    winner_msg = f"The lottery has ended! The rolled numbers are {dice_values} with a total of {total}. The winner is <a href='tg://user?id={closest_user}'>this user</a> with the closest guess of {lottery_entries[closest_user]}!"
    await update.message.reply_text(winner_msg, parse_mode='HTML')
    
    lottery_active = False
    lottery_entries = {}

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
    await update.message.reply_text(f"User ID {sudo_id} has been granted sudo permissions.")

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
    await update.message.reply_text(f"User ID {sudo_id} has been removed from sudo permissions.")

async def mute(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in sudo_ids and user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(chat_id, user_to_mute.id, permissions)
        await update.message.reply_text(f"{user_to_mute.first_name} has been muted.")
    except Exception as e:
        logger.error(f"Failed to mute user: {e}")
        await update.message.reply_text("Failed to mute the user.")

async def unmute(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in sudo_ids and user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    permissions = ChatPermissions(can_send_messages=True)
    try:
        await context.bot.restrict_chat_member(chat_id, user_to_unmute.id, permissions)
        await update.message.reply_text(f"{user_to_unmute.first_name} has been unmuted.")
    except Exception as e:
        logger.error(f"Failed to unmute user: {e}")
        await update.message.reply_text("Failed to unmute the user.")

def main():
    global start_date, user_ids, allowed_ids, sudo_ids
    start_date, user_ids = load_bot_data()
    allowed_ids = load_allowed_ids()
    sudo_ids = load_sudo_ids()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("football", football))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("exp", expire))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("lottery", lottery))
    application.add_handler(CommandHandler("joinlottery", join_lottery))
    application.add_handler(CommandHandler("fstart", start_lottery))
    application.add_handler(CommandHandler("add", add_allowed_id))
    application.add_handler(CommandHandler("remove", remove_allowed_id))
    application.add_handler(CommandHandler("addsudo", add_sudo))
    application.add_handler(CommandHandler("removesudo", remove_sudo))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CallbackQueryHandler(inline_start, pattern="start"))

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
