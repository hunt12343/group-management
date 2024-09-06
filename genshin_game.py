from telegram import Update
from telegram.ext import CallbackContext
import random
from pymongo import MongoClient

client = MongoClient('mongodb+srv://Joybot:Joybot123@joybot.toar6.mongodb.net/?retryWrites=true&w=majority&appName=Joybot') 
db = client['telegram_bot']
genshin_collection = db["genshin_users"]

# Define the primogem cost
COST_PER_PULL = 160
COST_PER_10_PULLS = 1600

# Comprehensive list of characters with their star ratings (replace with up-to-date list)
CHARACTERS = {
    "Diluc": 5, "Jean": 5, "Qiqi": 5, "Venti": 5, "Mona": 5, "Keqing": 5, "Albedo": 5, "Kazuha": 5,
    "Hu Tao": 5, "Ganyu": 5, "Zhongli": 5, "Raiden Shogun": 5, "Ayaka": 5, "Childe": 5, "Eula": 5,
    "Yae Miko": 5, "Tartaglia": 5, "Rosaria": 4, "Razor": 4, "Chongyun": 4, "Lisa": 4, "Barbara": 4,
    "Bennett": 4, "Fischl": 4, "Sucrose": 4, "Xingqiu": 4, "Xinyan": 4, "Ningguang": 4, "Beidou": 4,
    "Amber": 4, "Kaeya": 4, "Noelle": 4
}

# Comprehensive list of weapons with their star ratings (replace with up-to-date list)
WEAPONS = {
    "Aquila Favonia": 5, "The Stringless": 4, "Skyward Spine": 5, "The Flute": 4, "Deathmatch": 4,
    "Rust": 4, "Sacrificial Sword": 4, "Skyward Blade": 5, "Serpent Spine": 4, "Lost Prayer to the Sacred Winds": 5,
    "Primordial Jade Cutter": 5, "The Sacrificial Greatsword": 4, "Crescent Pike": 4, "Rainslasher": 4,
    "White Tassel": 3, "Dragon's Bane": 4, "Prototype Amber": 4, "The Widsith": 4, "Prototype Rancour": 4,
    "The Bell": 4, "Katsuragikiri Nagamasa": 4, "The Viridescent Hunt": 4
}

async def reward_primos(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user_by_id(user_id)
    
    if not user_data:
        user_data = {
            "user_id": user_id,
            "credits": 50000,
            "bag": {}
        }

    user_data["credits"] += 5
    save_user(user_data)

# Function to get user data
def get_user_by_id(user_id):
    return genshin_collection.find_one({"user_id": user_id})

# Function to save user data
def save_user(user_data):
    genshin_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)

def draw_item(items):
    weights = [1/(item_star**2) for item_star in items.values()]
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
    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    try:
        number_of_pulls = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Usage: /pull <number>")
        return

    total_cost = COST_PER_PULL * number_of_pulls
    if number_of_pulls == 10:
        total_cost = COST_PER_10_PULLS

    if total_cost > user_data["credits"]:
        await update.message.reply_text("🔺 Insufficient primogems.")
        return

    user_data["credits"] -= total_cost

    all_items = {**CHARACTERS, **WEAPONS}
    results = [draw_item(all_items) for _ in range(number_of_pulls)]
    
    result_message = "🎉 **You pulled the following items:**\n\n"
    for item in results:
        item_type = "characters" if item in CHARACTERS else "weapons"
        update_item(user_data, item, item_type)
        result_message += f"🔹 {item} - {CHARACTERS.get(item, WEAPONS.get(item))}⭐\n"

    result_message += f"\n💎 You spent {total_cost} Primogems!\n"
    
    save_user(user_data)
    await update.message.reply_text(result_message, parse_mode="Markdown")

async def bag(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("🔹 You need to start the bot first by using /start.")
        return

    if "bag" not in user_data or not user_data["bag"]:
        await update.message.reply_text("🎒 Your bag is empty.")
        return

    bag_message = "🎒 **Your Bag**:\n"
    for item_type, items in user_data["bag"].items():
        bag_message += f"\n🗃️ **{item_type.capitalize()}**:\n"
        for item, count in items.items():
            bag_message += f"🔹 {item}: {count}\n"

    await update.message.reply_text(bag_message, parse_mode="Markdown")
