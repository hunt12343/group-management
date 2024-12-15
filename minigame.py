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

class Emoji:
    DICE = "🎲"
    DART = "🎯"
    BASKETBALL = "🏀"
    COIN_FLIP = "🪙"

# Function to get the tagged user or default to the sender
async def get_tagged_user(update: Update):
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == MessageEntity.MENTION:
                user = update.message.entities[0].user
                return f"[{user.first_name}](tg://user?id={user.id})"
    return f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"

# Mini-game: Dart  
async def dart(update: Update, context: CallbackContext) -> None:
    user_tag = await get_tagged_user(update)
    await update.message.reply_text(f"{user_tag} {Emoji.DART}")

# Mini-game: Basketball  
async def basketball(update: Update, context: CallbackContext) -> None:
    user_tag = await get_tagged_user(update)
    await update.message.reply_text(f"{user_tag} {Emoji.BASKETBALL}")

# Mini-game: Coin Flip  
async def flip(update: Update, context: CallbackContext) -> None:
    user_tag = await get_tagged_user(update)
    await update.message.reply_text(f"{user_tag} {Emoji.COIN_FLIP}")

# Mini-game: Dice Roll  
async def dice(update: Update, context: CallbackContext) -> None:
    user_tag = await get_tagged_user(update)
    await update.message.reply_text(f"{user_tag} {Emoji.DICE}")


        
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

