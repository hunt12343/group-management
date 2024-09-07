from telegram import Update
from telegram.ext import CallbackContext
import random
from pymongo import MongoClient
import logging
from datetime import datetime

OWNER_ID = 5667016949
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = MongoClient('mongodb+srv://Joybot:Joybot123@joybot.toar6.mongodb.net/?retryWrites=true&w=majority&appName=Joybot') 
db = client['telegram_bot']
user_collection = db["users"]
genshin_collection = db["genshin_users"]

HARD_PITY_THRESHOLD = 90
SOFT_PITY_THRESHOLD = 75
COST_PER_PULL = 160
COST_PER_10_PULLS = 1600
BASE_5_STAR_RATE = 0.06

# Comprehensive list of characters with their star ratings
CHARACTERS = {
    "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5,
    "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5,
    "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4,
    "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4,
    "Amber": 4, "Kaeya": 4, "Noelle": 4
}

# Comprehensive list of weapons with their star ratings
WEAPONS = {
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4, "The Black Sword": 5,
    "Summit Shaper": 5, "Memory of Dust": 5, "The Alley Flash": 4, "Iron Sting": 4, "The Catch": 4,
    "Kagotsurube Isshin": 5, "Freedom-Sworn": 5, "Flowing Purity": 4, "Cursed Blade": 4
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
            "credits": 5000,  # Assuming credits should be used here
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
            "primos": 3200,  # Initial primogems
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
            "primos": 3200,  # Initial primogems
            "bag": {}
        }
        save_genshin_user(user_data)

    # Increment primos by 5
    user_data["primos"] += 5
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

    user_data["primos"] = user_data.get("primos", 0) + amount
    save_genshin_user(user_data)
    await update.message.reply_text(f"✅ {amount} primogems have been added to user {user_id}'s account.")

def draw_item(items):
    weights = [1 / (item_star**2) for item_star in items.values()]
    return random.choices(list(items.keys()), weights=weights, k=1)[0]

def update_item(user_data, item, item_type):
    if item_type not in user_data["bag"]:
        user_data["bag"][item_type] = {}

    if item not in user_data["bag"][item_type]:
        user_data["bag"][item_type][item] = 1
    else:
        user_data["bag"][item_type][item] += 1

    # Update refinement/constellation level
    if user_data["bag"][item_type][item] > 1:
        if item_type == "characters":
            user_data["bag"][item_type][item] = f"✨ C{user_data['bag'][item_type][item]}"
        elif item_type == "weapons":
            user_data["bag"][item_type][item] = f"⚔️ R{user_data['bag'][item_type][item]}"

async def pull(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_genshin_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    try:
        number_of_pulls = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Usage: /pull <number> (1-10)")
        return

    if number_of_pulls < 1 or number_of_pulls > 10:
        await update.message.reply_text("❗ Please specify a number between 1 and 10.")
        return

    total_cost = number_of_pulls * COST_PER_PULL
    if user_data["primos"] < total_cost:
        await update.message.reply_text(f"❗ You do not have enough primogems. Needed: {total_cost}")
        return

    user_data["primos"] -= total_cost

    items_pulled = {"characters": [], "weapons": []}
    for _ in range(number_of_pulls):
        if random.random() < BASE_5_STAR_RATE:
            item = draw_item({k: v for k, v in CHARACTERS.items() if v == 5})
            item_type = "characters"
        else:
            item = draw_item(WEAPONS)
            item_type = "weapons"

        items_pulled[item_type].append(item)
        update_item(user_data, item, item_type)

    save_genshin_user(user_data)

    # Format the response message
    characters_str = "\n".join([f"✨ {char}" for char in items_pulled["characters"]]) if items_pulled["characters"] else "No characters pulled."
    weapons_str = "\n".join([f"⚔️ {weapon}" for weapon in items_pulled["weapons"]]) if items_pulled["weapons"] else "No weapons pulled."

    response = (
        "🔹 **Pull Results:**\n\n"
        f"{characters_str}\n"
        f"{weapons_str}\n\n"
        f"💎 **Remaining Primogems:** {user_data['primos']}"
    )

    await update.message.reply_text(response, parse_mode='Markdown')


async def bag(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_genshin_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    primos = user_data.get("primos", 0)
    characters = user_data["bag"].get("characters", {})
    weapons = user_data["bag"].get("weapons", {})

    characters_list = [f"✨ {char}: {info}" for char, info in characters.items()]
    weapons_list = [f"⚔️ {weapon}: {info}" for weapon, info in weapons.items()]

    characters_str = "\n".join(characters_list) if characters_list else "No characters in bag."
    weapons_str = "\n".join(weapons_list) if weapons_list else "No weapons in bag."

    response = (
        "🔹 **Your Bag:**\n\n"
        f"💎 **Primogems:** {primos}\n\n"
        "👤 **Characters:**\n"
        f"{characters_str}\n\n"
        "⚔️ **Weapons:**\n"
        f"{weapons_str}"
    )

    await update.message.reply_text(response, parse_mode='Markdown')
