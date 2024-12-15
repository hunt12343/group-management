from pymongo import MongoClient
import asyncio
import os
import secrets
import logging
from telegram import Update, ChatPermissions
from telegram.ext import filters, ContextTypes
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
from token_1 import token

from genshin_game import pull, bag, reward_primos, add_primos, leaderboard, handle_message, button, reset_bag_data, drop_primos
from minigame import dart, basketball, flip, dice, credits_leaderboard,football
# Global variables
OWNER_ID = 5667016949
muted_users = set()

# List of owner IDs
OWNER_IDS = [5667016949, 1474610394]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = MongoClient('mongodb+srv://Joybot:Joybot123@joybot.toar6.mongodb.net/?retryWrites=true&w=majority&appName=Joybot') 
db = client['telegram_bot']
users_collection = db['users']
genshin_collection = db['genshin_users']

# MongoDB management functions
def get_user_by_id(user_id):
    return users_collection.find_one({"user_id": user_id})

def save_user(user_data):
    users_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

def get_genshin_user_by_id(user_id):
    return genshin_collection.find_one({"user_id": user_id})

def save_genshin_user(user_data):
    genshin_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    first_name = user.first_name  # Get user's first name

    # Save in general users collection
    existing_user = get_user_by_id(user_id)

    if existing_user is None:
        new_user = {
            "user_id": user_id,
            "first_name": first_name,  # Save the first name
            "join_date": datetime.now().strftime('%m/%d/%y'),
            "credits": 5000,
            "daily": None,
            "win": 0,
            "loss": 0,
            "achievement": [],
            "faction": "None",
            "ban": None,
            "title": "None",
            "primos": 0,
            "bag": {}
        }
        save_user(new_user)
        logger.info(f"User {user_id} started the bot with first name: {first_name}.")

        await update.message.reply_text(
            f"Welcome {first_name}! You've received 5000 credits to start betting. Use /profile to check your details."
        )
    else:
        logger.info(f"User {user_id} ({first_name}) already exists.")
        await update.message.reply_text(
            f"Welcome back, {first_name}! Use /profile to view your details."
        )

    # Save in genshin_users collection
    existing_genshin_user = get_genshin_user_by_id(user_id)

    if existing_genshin_user is None:
        new_genshin_user = {
            "user_id": user_id,
            "first_name": first_name,  # Save the first name in Genshin users
            "primos": 16000,  # Adjust initial primogems as needed
            "bag": {}
        }
        save_genshin_user(new_genshin_user)
        logger.info(f"Genshin user {user_id} initialized with first name: {first_name}.")
    else:
        logger.info(f"Genshin user {user_id} ({first_name}) already exists.")


async def profile(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    user_data = get_user_by_id(user_id)

    if user_data:
        profile_message = (
            f"👤 *{user.first_name}* 【{user_data['faction']}】\n"
            f"🆔 *ID*: {user_data['user_id']}\n"
            f"💰 *Units*: {user_data['credits']} 💎\n\n"
            f"🏆 *Wins*: {user_data['win']}\n"
            f"💔 *Losses*: {user_data['loss']}\n\n"
            f"🎖️ *Title*: {user_data['title']}\n"
        )

        try:
            photos = await context.bot.get_user_profile_photos(user_id)
            if photos.photos:
                # Use the smallest size available (last element in the list)
                smallest_photo = photos.photos[0][-1].file_id
                await update.message.reply_photo(photo=smallest_photo, caption=profile_message)
            else:
                await update.message.reply_text(profile_message)
        except Exception as e:
            logger.error(f"Error fetching user photo: {e}")
            await update.message.reply_text(profile_message)
    else:
        await update.message.reply_text("You need to start the bot first by using /start.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your bot. Use /amute and /aunmute to control users.")

async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    try:
        # Add user to the muted list
        muted_users.add(user_to_mute)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_mute,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted.")
    except Exception as e:
        await update.message.reply_text(f"Failed to mute user: {e}")

async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    try:
        # Remove user from the muted list
        muted_users.discard(user_to_unmute)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_unmute,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")
    except Exception as e:
        await update.message.reply_text(f"Failed to unmute user: {e}")

async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message from muted user: {e}")




def main() -> None:
    # Create the Application and pass the bot token
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("football", football))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("pull", pull))
    application.add_handler(CommandHandler("bag", bag))
    application.add_handler(CommandHandler("amute", amute))
    application.add_handler(CommandHandler("aunmute", aunmute))
    application.add_handler(CommandHandler('add_primos', add_primos))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler('drop_primos', drop_primos))
    application.add_handler(CommandHandler("reset_bag_data", reset_bag_data))
    application.add_handler(CommandHandler("credits_leaderboard", credits_leaderboard))

    

    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reward_primos))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.ALL, delete_muted_messages))

    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
