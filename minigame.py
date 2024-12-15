import random
from telegram import Update, MessageEntity
from telegram.ext import CallbackContext
from datetime import datetime
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

async def dart(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🎯")  # Send the dart emoji first
    await update.message.reply_text("Bullseye!")  # Send text message

async def basketball(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🏀")  # Send the basketball emoji first
    await update.message.reply_text("Score!")  # Send text message

async def flip(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🪙")  # Send the coin flip emoji first
    await update.message.reply_text("Heads or Tails?")  # Send text message

async def dice(update: Update, context: CallbackContext) -> None:
    # Check if there's a user mentioned in the message
    if update.message.entities and update.message.entities[0].type == MessageEntity.MENTION:
        mentioned_user_id = update.message.entities[0].user.id
        mentioned_user = f"[{update.message.entities[0].user.first_name}](tg://user?id={mentioned_user_id})"

        # Tag the mentioned user and send the emoji
        await update.message.reply_text(f"{mentioned_user} 🎲")
    else:
        # If no user is tagged, just send the emoji
        await update.message.reply_text("🎲")


        
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

