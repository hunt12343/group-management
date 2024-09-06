from telegram import Update
from telegram.ext import CallbackContext
import random
from pymongo import MongoClient
import logging
from datetime import datetime

OWNER_ID = 5667016949
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient('mongodb+srv://Joybot:Joybot123@joybot.toar6.mongodb.net/?retryWrites=true&w=majority&appName=Joybot') 
db = client['telegram_bot']
user_collection = db["users"]
genshin_collection = db["genshin_users"]

# Define the primogem cost
COST_PER_PULL = 160
COST_PER_10_PULLS = 1600

# Comprehensive list of characters with their star ratings
CHARACTERS = {
    "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5,
    "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5,
    "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4,
    "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4,
    "Amber": 4, "Kaeya": 4, "Noelle": 4, "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5,
    "Keqing": 5, "Albedo": 5, "Kazuha": 5, "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5,
    "Ayaka": 5, "Childe": 5, "Eula": 5, "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4,
    "Chongyun": 4, "Lisa": 4, "Barbara": 4, "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4,
    "Xinyan": 4, "Ningguang": 4, "Beidou": 4, "Amber": 4, "Kaeya": 4, "Noelle": 4, "Rosaria": 4,
    "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4, "Bennett": 4, "Fischl": 4, "Sucrose": 4,
    "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4, "Amber": 4, "Kaeya": 4, "Noelle": 4,
    "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5,
    "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5,
    "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4,
    "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4,
    "Amber": 4, "Kaeya": 4, "Noelle": 4, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4,
    "Barbara": 4, "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4,
    "Beidou": 4, "Amber": 4, "Kaeya": 4, "Noelle": 4, "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5,
    "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5, "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5,
    "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5, "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4,
    "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4, "Bennett": 4, "Fischl": 4, "Sucrose": 4,
    "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4, "Amber": 4, "Kaeya": 4, "Noelle": 4,
    "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5,
    "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5,
    "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4,
    "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4,
    "Amber": 4, "Kaeya": 4, "Noelle": 4, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4,
    "Barbara": 4, "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4,
    "Beidou": 4, "Amber": 4, "Kaeya": 4, "Noelle": 4, "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5,
    "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5, "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5,
    "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5, "Yae Miko": 5, "Tartaglia": 5
}


# Comprehensive list of weapons with their star ratings
WEAPONS = {
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4, "The Black Sword": 5,
    "Summit Shaper": 5, "Memory of Dust": 5, "The Alley Flash": 4, "Iron Sting": 4, "The Rainslasher": 4,
    "The Catch": 4, "Kagotsurube Isshin": 5, "Freedom-Sworn": 5, "Flowing Purity": 4, "Cursed Blade": 4,
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4, "The Black Sword": 5,
    "Summit Shaper": 5, "Memory of Dust": 5, "The Alley Flash": 4, "Iron Sting": 4, "The Rainslasher": 4,
    "The Catch": 4, "Kagotsurube Isshin": 5, "Freedom-Sworn": 5, "Flowing Purity": 4, "Cursed Blade": 4,
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4, "The Black Sword": 5,
    "Summit Shaper": 5, "Memory of Dust": 5, "The Alley Flash": 4, "Iron Sting": 4, "The Rainslasher": 4,
    "The Catch": 4, "Kagotsurube Isshin": 5, "Freedom-Sworn": 5, "Flowing Purity": 4, "Cursed Blade": 4,
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4, "The Black Sword": 5,
    "Summit Shaper": 5, "Memory of Dust": 5, "The Alley Flash": 4, "Iron Sting": 4, "The Rainslasher": 4,
    "The Catch": 4, "Kagotsurube Isshin": 5, "Freedom-Sworn": 5, "Flowing Purity": 4, "Cursed Blade": 4
}


# Function to get user data from the genshin_users collection
def get_genshin_user_by_id(user_id):
    return genshin_collection.find_one({"user_id": user_id})

# Function to save user data to the genshin_users collection
def save_genshin_user(user_data):
    genshin_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

# Function to get user data from the general users collection
def get_user_by_id(user_id):
    return user_collection.find_one({"user_id": user_id})

# Function to save user data to the general users collection
def save_user(user_data):
    user_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    # Save in general users collection
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

    # Save in genshin_users collection
    existing_genshin_user = get_genshin_user_by_id(user_id)

    if existing_genshin_user is None:
        new_genshin_user = {
            "user_id": user_id,
            "credits": 3200,  # Initial primogems
            "bag": {}
        }
        save_genshin_user(new_genshin_user)
        logger.info(f"Genshin user {user_id} initialized.")


async def reward_primos(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_genshin_user_by_id(user_id)
    
    if not user_data:
        # Create user data if not present
        user_data = {
            "user_id": user_id,
            "credits": 3200,  # Initial primogems
            "bag": {}
        }
        save_genshin_user(user_data)

    # Increment primos by 5
    user_data["credits"] += 5
    save_genshin_user(user_data)


async def add_primos(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🔒 You don't have permission to use this command.")
        return

    # Ensure proper command format
    if len(context.args) < 2:
        await update.message.reply_text("❗ Usage: /add primo <user_id> <amount>")
        return

    user_id = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❗ The amount must be a valid number.")
        return

    if amount <= 0:
        await update.message.reply_text("❗ The amount must be a positive number.")
        return

    user_data = get_genshin_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text(f"❗ User with ID {user_id} does not exist.")
        return

    user_data["credits"] = user_data.get("credits", 0) + amount
    save_genshin_user(user_data)
    await update.message.reply_text(f"✅ {amount} primogems have been added to user {user_id}'s account.")

async def pull(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_genshin_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    # Determine number of pulls
    number_of_pulls = 1
    if len(context.args) > 0 and context.args[0] == "10":
        number_of_pulls = 10

    # Calculate total cost
    total_cost = COST_PER_PULL * number_of_pulls
    if total_cost > user_data["credits"]:
        await update.message.reply_text("🔺 Insufficient primogems.")
        return

    user_data["credits"] -= total_cost

    # Pull items
    all_items = {**CHARACTERS, **WEAPONS}
    results = [draw_item(all_items) for _ in range(number_of_pulls)]
    
    # Create result message
    result_message = "🎉 **You pulled the following items:**\n\n"
    for item in results:
        item_type = "characters" if item in CHARACTERS else "weapons"
        update_item(user_data, item, item_type)
        result_message += f"🔹 {item} - {CHARACTERS.get(item, WEAPONS.get(item))}⭐\n"

    result_message += f"\n💎 You spent {total_cost} Primogems!\n"
    
    save_genshin_user(user_data)
    await update.message.reply_text(result_message, parse_mode="Markdown")


async def bag(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_genshin_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    bag_message = "🎒 **Your Bag**:\n"

    # Show primos separately
    bag_message += f"💎 **Primos**: {user_data['credits']} ⭐\n\n"

    # Show other items in the bag
    if 'bag' in user_data and user_data['bag']:
        for item_type, items in user_data['bag'].items():
            bag_message += f"\n🗃️ **{item_type.capitalize()}**:\n"
            for item, count in items.items():
                bag_message += f"🔹 {item}: {count}\n"
    else:
        bag_message += "🎒 Your bag is empty."

    await update.message.reply_text(bag_message, parse_mode="Markdown")
    logger.info(f"User {user_id} viewed their bag")

