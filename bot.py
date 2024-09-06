from pymongo import MongoClient
import asyncio
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
from token_1 import token
import random
import secrets

from genshin_game import pull, bag

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

# MongoDB management functions
def get_user_by_id(user_id):
    return users_collection.find_one({"user_id": user_id})

def save_user(user_data):
    users_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

def update_user_credits(user_id, amount):
    users_collection.update_one({"user_id": user_id}, {"$inc": {"credits": amount}})

def update_user_win_loss(user_id, win=True):
    if win:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"win": 1}})
    else:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"loss": 1}})

# Telegram message formatting function
def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    existing_user = get_user_by_id(user_id)

    if existing_user is None:
        new_user = {
            "user_id": user_id,
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
        logger.info(f"User {user_id} started the bot.")

        await update.message.reply_text(
            "Welcome! You've received 5000 credits to start betting. Use /profile to check your details."
        )
    else:
        logger.info(f"User {user_id} already exists.")
        await update.message.reply_text(
            "You have already started the bot. Use /profile to view your details."
        )

# Profile command
async def profile(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    user_data = get_user_by_id(user_id)

    if user_data:
        profile_message = (
            f"👤 *{user.first_name}* 【{user_data['faction']}】\n"
            f"🆔 *ID*: {user_data['user_id']}\n"
            f"💰 *Units*: {user_data['credits']} 💎\n"
            f"🎯 *Primos*: {user_data['primos']} ⭐\n\n"
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

# Roulette game
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

# Flip coin game
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

# Basketball game function
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

# Add credits manually
async def add(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You don't have permission to use this command.")
        return

    try:
        user_id = context.args[0]
        amount = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /add <user_id> <amount>")
        return

    if amount <= 0:
        await update.message.reply_text("Invalid amount. Please enter a positive number.")
        return

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text(f"User with ID {user_id} does not exist.")
        return

    update_user_credits(user_id, amount)
    await update.message.reply_text(f"{amount} credits have been added to user {user_id}'s profile.")

# Main function to run the bot
def main() -> None:
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("roulette", roulette))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("bet", bet))
    application.add_handler(CommandHandler("dart", dart))
    application.add_handler(CommandHandler("basketball", basketball))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("pull", pull))
    application.add_handler(CommandHandler("bag", bag))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
