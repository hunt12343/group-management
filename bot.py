from pymongo import MongoClient
import asyncio
import os
import logging
from datetime import datetime
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
from token_1 import token

from genshin_game import pull, bag, reward_primos, add_primos, leaderboard, handle_message, send_reward, button, reset_bag_data, drop_primos
# Global variables
OWNER_ID = 5667016949

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
            "primos": 3200,  # Adjust initial primogems as needed
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
                photo = photos.photos[0][0].file_id
                await update.message.reply_photo(photo=photo, caption=profile_message)
            else:
                await update.message.reply_text(profile_message)
        except Exception as e:
            logger.error(f"Error fetching user photo: {e}")
            await update.message.reply_text(profile_message)
    else:
        await update.message.reply_text("You need to start the bot first by using /start.")


async def roulette(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        bet_amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /roulette <amount>")
        return

    if bet_amount <= 0 or bet_amount > user_data["credits"]:
        await update.message.reply_text("Invalid bet amount or insufficient credits.")
        return

    result = secrets.choice(["win", "lose"])
    if result == "win":
        update_user_credits(user_id, bet_amount * 2)
        message = f"🎉 You won! Your bet doubled to {bet_amount * 2} units."
    else:
        update_user_credits(user_id, -bet_amount)
        message = f"😞 You lost! {bet_amount} units have been deducted from your profile."

    await update.message.reply_text(message)

async def flip(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        choice = context.args[0].upper()
        bet_amount = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /flip [H/T] [amount]")
        return

    if choice not in ["H", "T"]:
        await update.message.reply_text("Invalid choice. Use 'H' for heads or 'T' for tails.")
        return

    if bet_amount <= 0 or bet_amount > user_data["credits"]:
        await update.message.reply_text("Invalid bet amount.")
        return

    result = random.choice(["H", "T"])
    if result == choice:
        update_user_credits(user_id, bet_amount)
        message = f"🎉 You won! {bet_amount} credits added."
    else:
        update_user_credits(user_id, -bet_amount)
        message = f"😞 You lost! {bet_amount} credits deducted."

    await update.message.reply_text(message)

async def bet(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        bet_amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /bet <amount>")
        return

    if bet_amount <= 0 or bet_amount > user_data["credits"]:
        await update.message.reply_text("Invalid bet amount.")
        return

    result = secrets.choice(["win", "lose"])
    if result == "win":
        update_user_credits(user_id, bet_amount)
        message = f"You won! {bet_amount} credits have been added to your profile."
    else:
        update_user_credits(user_id, -bet_amount)
        message = f"You lost! {bet_amount} credits have been deducted from your profile."

    await update.message.reply_text(message)

async def dart(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["bullseye", "miss"])
    if result == "bullseye":
        update_user_credits(user_id, 100)
        await update.message.reply_text("🎯")  # Send emoji first
        await update.message.reply_text("Bullseye! You earned 100 credits! 😎")  # Send text message
    else:
        update_user_credits(user_id, -100)
        await update.message.reply_text("🎯")  # Send emoji first
        await update.message.reply_text("Miss! You lost 100 credits. 😢")  # Send text message

async def basketball(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["score", "miss"])
    if result == "score":
        update_user_credits(user_id, 75)
        await update.message.reply_text("🏀")  # Send emoji first
        await update.message.reply_text("Score! You earned 75 credits! 🏆")  # Send text message
    else:
        update_user_credits(user_id, -75)
        await update.message.reply_text("🏀")  # Send emoji first
        await update.message.reply_text("Miss! You lost 75 credits. 😞")  # Send text message


def main() -> None:
    # Create the Application and pass the bot token
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("roulette", roulette))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("bet", bet))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("pull", pull))
    application.add_handler(CommandHandler("bag", bag))
    application.add_handler(CommandHandler('add_primos', add_primos))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler('drop_primos', drop_primos))
    application.add_handler(CommandHandler("reset_bag_data", reset_bag_data))

    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reward_primos))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
