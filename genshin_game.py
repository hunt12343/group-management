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

BASE_5_STAR_RATE = 0.02  
HIGH_5_STAR_RATE = 0.60  
PULL_THRESHOLD = 10      
HIGH_PULL_THRESHOLD = 70  
COST_PER_PULL = 160 


CHARACTERS = {
    # 5-star characters
    "Albedo": 5, "Alhaitham": 5, "Aloy": 5, "Ayaka": 5, "Ayato": 5, "Baizhu": 5, "Cyno": 5, 
    "Dehya": 5, "Diluc": 5, "Eula": 5, "Ganyu": 5, "Hu Tao": 5, "Itto": 5, "Jean": 5, 
    "Kazuha": 5, "Keqing": 5, "Klee": 5, "Kokomi": 5, "Lyney": 5, "Mona": 5, "Nahida": 5, 
    "Nilou": 5, "Qiqi": 5, "Raiden": 5, "Shenhe": 5, "Tighnari": 5, "Venti": 5, "Wanderer": 5, 
    "Xiao": 5, "Yae Miko": 5, "Yelan": 5, "Yoimiya": 5, "Zhongli": 5,

    # 4-star characters
    "Amber": 4, "Barbara": 4, "Beidou": 4, "Bennett": 4, "Candace": 4, "Chongyun": 4, 
    "Collei": 4, "Diona": 4, "Dori": 4, "Fischl": 4, "Gorou": 4, "Heizou": 4, "Kaeya": 4, 
    "Kuki Shinobu": 4, "Layla": 4, "Lisa": 4, "Ningguang": 4, "Noelle": 4, "Razor": 4, 
    "Rosaria": 4, "Sara": 4, "Sayu": 4, "Sucrose": 4, "Thoma": 4, "Xiangling": 4, 
    "Xingqiu": 4, "Xinyan": 4, "Yanfei": 4, "Yaoyao": 4, "Yun Jin": 4
}


# Comprehensive list of weapons with their star ratings
WEAPONS = {
    # 5-star weapons
    "Aquila Favonia": 5, "Amos' Bow": 5, "Aqua Simulacra": 5, "Calamity Queller": 5, "Crimson Moon's Semblance": 5,
    "Elegy for the End": 5, "Engulfing Lightning": 5, "Everlasting Moonglow": 5, "Freedom-Sworn": 5,
    "Haran Geppaku Futsu": 5, "Hunter's Path": 5, "Jadefall's Splendor": 5, "Kagura's Verity": 5,
    "Key of Khaj-Nisut": 5, "Light of Foliar Incision": 5, "Lost Prayer to the Sacred Winds": 5,
    "Lumidouce Elegy": 5, "Memory of Dust": 5, "Mistsplitter Reforged": 5, "Polar Star": 5,
    "Primordial Jade Cutter": 5, "Primordial Jade Winged-Spear": 5, "Redhorn Stonethresher": 5,
    "Song of Broken Pines": 5, "Staff of Homa": 5, "Staff of the Scarlet Sands": 5, "Summit Shaper": 5,
    "The First Great Magic": 5, "The Unforged": 5, "Thundering Pulse": 5, "Tome of the Eternal Flow": 5,
    "Tulaytullah's Remembrance": 5, "Uraku Misugiri": 5, "Verdict": 5, "Vortex Vanquisher": 5, "Wolf's Gravestone": 5,

    # 4-star weapons
    "Akuoumaru": 4, "Alley Hunter": 4, "Amenoma Kageuchi": 4, "Ballad of the Boundless Blue": 4,
    "Ballad of the Fjords": 4, "Blackcliff Agate": 4, "Blackcliff Longsword": 4, "Blackcliff Pole": 4,
    "Blackcliff Slasher": 4, "Blackcliff Warbow": 4, "Cloudforged": 4, "Cinnabar Spindle": 4,
    "Compound Bow": 4, "Crescent Pike": 4, "Deathmatch": 4, "Dodoco Tales": 4, "Dragon's Bane": 4,
    "Dragonspine Spear": 4, "End of the Line": 4, "Eye of Perception": 4, "Fading Twilight": 4,
    "Favonius Codex": 4, "Favonius Greatsword": 4, "Favonius Lance": 4, "Favonius Sword": 4,
    "Favonius Warbow": 4, "Festering Desire": 4, "Finale of the Deep": 4, "Fleuve Cendre Ferryman": 4,
    "Flowing Purity": 4, "Forest Regalia": 4, "Frostbearer": 4, "Fruit of Fulfillment": 4, "Hakushin Ring": 4,
    "Hamayumi": 4, "Iron Sting": 4, "Kagotsurube Isshin": 4, "Kitain Cross Spear": 4, "Lion's Roar": 4,
    "Lithic Blade": 4, "Lithic Spear": 4, "Luxurious Sea-Lord": 4, "Mailed Flower": 4, "Makhaira Aquamarine": 4,
    "Mappa Mare": 4, "Missive Windspear": 4, "Mitternachts Waltz": 4, "Moonpiercer": 4, "Mouun's Moon": 4,
    "Oathsworn Eye": 4, "Portable Power Saw": 4, "Predator": 4, "Prospector's Drill": 4, "Prototype Amber": 4,
    "Prototype Archaic": 4, "Prototype Crescent": 4, "Prototype Rancour": 4, "Prototype Starglitter": 4,
    "Rainslasher": 4, "Range Gauge": 4, "Rightful Reward": 4, "Royal Bow": 4, "Royal Greatsword": 4,
    "Royal Grimoire": 4, "Royal Longsword": 4, "Royal Spear": 4, "Rust": 4, "Sacrificial Bow": 4,
    "Sacrificial Fragments": 4, "Sacrificial Greatsword": 4, "Sacrificial Jade": 4, "Sacrificial Sword": 4,
    "Sapwood Blade": 4, "Scion of the Blazing Sun": 4, "Serpent Spine": 4, "Snow-Tombed Starsilver": 4,
    "Solar Pearl": 4, "Song of Stillness": 4, "Sword of Descension": 4, "Sword of Narzissenkreuz": 4,
    "Talking Stick": 4, "The Alley Flash": 4, "The Bell": 4, "The Black Sword": 4, "The Catch": 4,
    "The Dockhand's Assistant": 4, "The Flute": 4, "The Stringless": 4, "The Viridescent Hunt": 4,
    "The Widsith": 4, "Tidal Shadow": 4, "Toukabou Shigure": 4, "Ultimate Overlord's Mega Magic Sword": 4,
    "Wandering Evenstar": 4, "Wavebreaker's Fin": 4, "Whiteblind": 4, "Windblume Ode": 4, "Wine and Song": 4,
    "Wolf-Fang": 4, "Xiphos' Moonlight": 4,

    # 3-star weapons
    "Black Tassel": 3, "Bloodtainted Greatsword": 3, "Cool Steel": 3, "Dark Iron Sword": 3,
    "Debate Club": 3, "Emerald Orb": 3, "Ferrous Shadow": 3, "Fillet Blade": 3, "Halberd": 3,
    "Harbinger of Dawn": 3, "Magic Guide": 3, "Messenger": 3, "Otherworldly Story": 3,
    "Raven Bow": 3, "Recurve Bow": 3, "Sharpshooter's Oath": 3, "Skyrider Greatsword": 3,
    "Skyrider Sword": 3, "Slingshot": 3, "Thrilling Tales of Dragon Slayers": 3, "Traveler's Handy Sword": 3,
    "Twin Nephrite": 3, "White Iron Greatsword": 3, "White Tassel": 3
}


def get_genshin_user_by_id(user_id):
    return genshin_collection.find_one({"user_id": user_id})


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



# Draw an item based on current pull count and 5-star/4-star logic
def draw_item(items, pull_counter, last_five_star_pull):
    # If the user has pulled 10 times without a 4-star, guarantee a 4-star item
    if pull_counter % PULL_THRESHOLD == 0:
        item = draw_4_star_item(items)
        return item, "characters" if "character" in item else "weapons"

    # Increase the 5-star rate after 70 pulls without a 5-star
    if pull_counter - last_five_star_pull >= HIGH_PULL_THRESHOLD:
        five_star_chance = HIGH_5_STAR_RATE
    else:
        five_star_chance = BASE_5_STAR_RATE

    # Check for a 5-star pull
    if random.random() < five_star_chance:
        item = draw_5_star_item(items)
        return item, "characters" if "character" in item else "weapons"

    # Otherwise, draw either a 4-star or 3-star item
    return draw_3_star_item(items), "weapons"

# Helper functions to draw items based on star rating
def draw_5_star_item(items):
    five_star_items = {k: v for k, v in items.items() if v == 5}
    return random.choice(list(five_star_items.keys()))

def draw_4_star_item(items):
    four_star_items = {k: v for k, v in items.items() if v == 4}
    return random.choice(list(four_star_items.keys()))

def draw_3_star_item(items):
    three_star_items = {k: v for k, v in items.items() if v == 3}
    return random.choice(list(three_star_items.keys()))
    

def update_item(user_data, item, item_type):
    if item_type not in user_data["bag"]:
        user_data["bag"][item_type] = {}

    if item not in user_data["bag"][item_type]:
        user_data["bag"][item_type][item] = 1
    else:
        # Get the current count of the item
        current_count = user_data["bag"][item_type][item]
        
        # Check if the item count is stored as an integer or a string
        if isinstance(current_count, int):
            user_data["bag"][item_type][item] += 1
        else:
            # Extract the current refinement level or constellation level
            if item_type == "characters":
                # Extract the numerical part of the level
                current_level = int(current_count.split('C')[1]) if 'C' in current_count else 0
                new_level = current_level + 1
                user_data["bag"][item_type][item] = f"✨ C{new_level}"
            elif item_type == "weapons":
                # Extract the numerical part of the level
                current_level = int(current_count.split('R')[1]) if 'R' in current_count else 0
                new_level = current_level + 1
                user_data["bag"][item_type][item] = f"⚔️ R{new_level}"



# Assuming you already have functions to get and save user data
# Example: get_genshin_user_by_id, save_genshin_user, update_item

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

    # Deduct primogems
    user_data["primos"] -= total_cost
    pull_counter = user_data.get('pull_counter', 0)
    last_five_star_pull = user_data.get('last_five_star_pull', 0)

    items_pulled = {"characters": [], "weapons": []}
    
    for _ in range(number_of_pulls):
        item, item_type = draw_item(WEAPONS, pull_counter, last_five_star_pull)  # Pass correct arguments
        items_pulled[item_type].append(item)
        update_item(user_data, item, item_type)
        
        # Increment counters
        pull_counter += 1

        # Reset last_five_star_pull if a 5-star is pulled
        if item_type == "characters" and item in CHARACTERS and CHARACTERS[item] == 5:
            last_five_star_pull = pull_counter

    # Save user data after pulls
    user_data['pull_counter'] = pull_counter
    user_data['last_five_star_pull'] = last_five_star_pull
    save_genshin_user(user_data)

    # Format the response message
    characters_str = "\n".join([f"✨ {char} ({CHARACTERS[char]}★)" for char in items_pulled["characters"]]) if items_pulled["characters"] else "No characters pulled."
    weapons_str = "\n".join([f"⚔️ {weapon} ({WEAPONS[weapon]}★)" for weapon in items_pulled["weapons"]]) if items_pulled["weapons"] else "No weapons pulled."

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
