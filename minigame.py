import random
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from pymongo import MongoClient
import logging

# MongoDB setup
client = MongoClient('mongodb+srv://Joybot:Joybot123@joybot.toar6.mongodb.net/?retryWrites=true&w=majority&appName=Joybot')
db = client['telegram_bot']
users_collection = db['users']

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB utility functions
def get_user_by_id(user_id):
    return users_collection.find_one({"user_id": user_id})

def update_user_credits(user_id, amount):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": amount}}
    )

# Mini-games
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

async def flip(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["heads", "tails"])
    if result == "heads":
        update_user_credits(user_id, 50)
        await update.message.reply_text("🪙")  # Send emoji first
        await update.message.reply_text("Heads! You earned 50 credits! 🤑")  # Send text message
    else:
        update_user_credits(user_id, -50)
        await update.message.reply_text("🪙")  # Send emoji first
        await update.message.reply_text("Tails! You lost 50 credits. 😔")  # Send text message

async def dice(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    roll = random.randint(1, 6)
    if roll == 6:
        update_user_credits(user_id, 150)
        await update.message.reply_text("🎲")  # Send emoji first
        await update.message.reply_text("You rolled a 6! Jackpot! You earned 150 credits! 🎉")  # Send text message
    else:
        update_user_credits(user_id, -30)
        await update.message.reply_text("🎲")  # Send emoji first
        await update.message.reply_text(f"You rolled a {roll}. Better luck next time! You lost 30 credits. 🙃")
        
async def credits_leaderboard(update: Update, context: CallbackContext) -> None:
    try:
        # Fetch top 20 users sorted by credits in descending order
        top_users = list(users_collection.find().sort("credits", -1).limit(20))

        if not top_users:
            await update.message.reply_text("No data available for the leaderboard.")
            return

        # Build the leaderboard message
        leaderboard_message = "⚔️ *Top 20 Credits Leaderboard* ⚔️\n\n"
        for idx, user in enumerate(top_users, start=1):
            name = user.get("first_name", "Unknown User")
            credits = user.get("credits", 0)
            leaderboard_message += f"{idx}. {name} ► {credits} 👾\n"

        # Send the leaderboard message
        await update.message.reply_text(leaderboard_message)
    except Exception as e:
        logger.error(f"Error generating credits leaderboard: {e}")
        await update.message.reply_text("An error occurred while generating the leaderboard.")

