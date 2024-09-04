import asyncio
import json
import os
import secrets
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext
from token_1 import token

# Global variables
OWNER_ID = 5667016949
players = {}
BOT_DATA_FILE = 'bot_data.json'
ALLOWED_IDS_FILE = 'allowed_ids.json'
SUDO_IDS_FILE = 'sudo_ids.json'
USERS_FILE = 'users.json'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_json_data(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return default

def save_json_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Bot data functions
def load_bot_data():
    data = load_json_data(BOT_DATA_FILE, {})
    if data:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        user_ids = set(data['user_ids'])
    else:
        start_date = datetime.now()
        user_ids = set()
        save_bot_data(start_date, user_ids)
    return start_date, user_ids

def save_bot_data(start_date, user_ids):
    data = {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "user_ids": list(user_ids)
    }
    save_json_data(BOT_DATA_FILE, data)

# ID management functions
def load_allowed_ids():
    return set(load_json_data(ALLOWED_IDS_FILE, [OWNER_ID]))

def save_allowed_ids(allowed_ids):
    save_json_data(ALLOWED_IDS_FILE, {"user_ids": list(allowed_ids)})

def load_sudo_ids():
    return set(load_json_data(SUDO_IDS_FILE, [OWNER_ID]))

def save_sudo_ids(sudo_ids):
    save_json_data(SUDO_IDS_FILE, {"user_ids": list(sudo_ids)})

def load_users():
    """Loads the users data from USERS_FILE."""
    return load_json_data(USERS_FILE, {})

def save_users(users):
    """Saves the users data to USERS_FILE."""
    save_json_data(USERS_FILE, users)

def update_user_credits(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["credits"] += amount
        save_users(users)

def update_user_win_loss(user_id, win=True):
    users = load_users()
    if str(user_id) in users:
        if win:
            users[str(user_id)]["win"] += 1
        else:
            users[str(user_id)]["loss"] += 1
        save_users(users)

# Markdown escaping for Telegram messages
def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)  # Convert to string to match JSON storage

    users = load_users()

    if user_id not in users:
        # Initialize user data
        users[user_id] = {
            "user_id": user_id,
            "join_date": datetime.now().strftime('%m/%d/%y'),
            "credits": 50000,  # Starting credits
            "daily": None,
            "win": 0,
            "loss": 0,
            "achievement": [],
            "faction": "None",
            "ban": None,
            "title": "None"
        }
        save_users(users)
        logger.info(f"User {user_id} started the bot.")

    await update.message.reply_text(
        "Welcome! You've received 50,000 credits to start betting. Use /profile to check your details."
    )

async def profile(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()

    if user_id in users:
        user_data = users[user_id]
        profile_message = (
            f"👤 *{user.first_name}* 【{user_data['faction']}】\n"
            f"🆔 *ID*: {user_data['user_id']}\n"
            f"💰 *Units*: {user_data['credits']} 💎\n\n"
            f"🏆 *Wins*: {user_data['win']}\n"
            f"💔 *Losses*: {user_data['loss']}\n\n"
            f"🎖️ *Title*: {user_data['title']}\n"
        )

        # Send the profile picture
        try:
            photos = await context.bot.get_user_profile_photos(user_id=user.id)
            if photos.total_count > 0:
                await update.message.reply_photo(photos.photos[0][-1].file_id, caption=profile_message, parse_mode='Markdown')
            else:
                await update.message.reply_text(profile_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error fetching profile picture for user {user_id}: {e}")
            await update.message.reply_text(profile_message, parse_mode='Markdown')
    else:
        await update.message.reply_text("You have not started using the bot yet. Use /start to begin.")

async def roulette(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        bet_amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /roulette <amount>")
        return

    if bet_amount <= 0 or bet_amount > users[user_id]["credits"]:
        await update.message.reply_text("Invalid bet amount or insufficient credits.")
        return

    result = secrets.choice(["win", "lose"])
    if result == "win":
        users[user_id]["credits"] += bet_amount * 2
        message = f"🎉 You won! Your bet doubled to {bet_amount * 2} units."
    else:
        users[user_id]["credits"] -= bet_amount
        message = f"😞 You lost! {bet_amount} units have been deducted from your profile."

    save_users(users)
    await update.message.reply_text(message)

def slot_machine(player_id, bet_amount):
    if player_id not in players:
        return "You need to start the bot first."
    
    slots = ["🍒", "🍋", "🔔", "⭐", "🍀"]
    result = [random.choice(slots), random.choice(slots), random.choice(slots)]
    
    if result[0] == result[1] == result[2]:
        win_amount = bet_amount * 10
        players[player_id]['credits'] += win_amount
        return f"{result} Jackpot! You win {win_amount} credits!"
    else:
        players[player_id]['credits'] -= bet_amount
        return f"{result} You lose {bet_amount} credits."

async def flip(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in players:
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

    if bet_amount <= 0 or bet_amount > players[user_id]["credits"]:
        await update.message.reply_text("Invalid bet amount.")
        return

    result = random.choice(["H", "T"])
    if result == choice:
        players[user_id]["credits"] += bet_amount
        message = f"🎉 You won! {bet_amount} credits added."
    else:
        players[user_id]["credits"] -= bet_amount
        message = f"😞 You lost! {bet_amount} credits deducted."

    save_data()  # Save player data
    await update.message.reply_text(message)



async def bet(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    try:
        bet_amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /bet 500")
        return

    if bet_amount <= 0 or bet_amount > users[user_id]["credits"]:
        await update.message.reply_text("Invalid bet amount or insufficient credits.")
        return

    result = secrets.choice(["win", "lose"])
    if result == "win":
        users[user_id]["credits"] += bet_amount
        users[user_id]["win"] += 1
        message = f"You won! {bet_amount} credits have been added to your profile."
    else:
        users[user_id]["credits"] -= bet_amount
        users[user_id]["loss"] += 1
        message = f"You lost! {bet_amount} credits have been deducted from your profile."

    save_users(users)
    await update.message.reply_text(message)


async def dice(update: Update, context: CallbackContext) -> None:
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        if update.message.reply_to_message:
            user_dice_msg_id = update.message.reply_to_message.message_id
            await context.bot.send_dice(chat_id=update.effective_chat.id, reply_to_message_id=user_dice_msg_id)
        else:
            await update.message.reply_text("Please reply to a user's message to roll a dice for them.")
    else:
        await context.bot.send_dice(chat_id=update.effective_chat.id)

async def football(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in players:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["goal", "miss"])
    if result == "goal":
        players[user_id]["credits"] += 50
        message = "⚽ Goal! You earned 50 credits."
    else:
        players[user_id]["credits"] -= 50
        message = "🚫 Miss! You lost 50 credits."

    save_data()  # Save player data
    await update.message.reply_text(message)


async def basketball(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in players:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["score", "miss"])
    if result == "score":
        players[user_id]["credits"] += 75
        message = "🏀 Score! You earned 75 credits."
    else:
        players[user_id]["credits"] -= 75
        message = "🏀 Miss! You lost 75 credits."

    save_data()  # Save player data
    await update.message.reply_text(message)


async def dart(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in players:
        await update.message.reply_text("You need to start the bot first by using /start.")
        return

    result = random.choice(["bullseye", "miss"])
    if result == "bullseye":
        players[user_id]["credits"] += 100
        message = "🎯 Bullseye! You earned 100 credits."
    else:
        players[user_id]["credits"] -= 100
        message = "🎯 Miss! You lost 100 credits."

    save_data()  # Save player data
    await update.message.reply_text(message)

async def add_units(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        target_id = context.args[0]
        amount = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /add <user_id> <amount>")
        return

    users = load_users()
    if target_id in users:
        users[target_id]["credits"] += amount
        save_users(users)
        await update.message.reply_text(f"Successfully added {amount} units to user {target_id}.")
    else:
        await update.message.reply_text("User not found.")

# PvP battle functions
def save_players():
    save_json_data('players.json', players)

def load_players():
    global players
    players = load_json_data('players.json', {})

def challenge_player(challenger_id, opponent_id):
    load_players()
    if opponent_id not in players:
        return "Opponent has not started the bot yet."
    if challenger_id not in players:
        return "You have not started the bot yet."

    players[challenger_id]['hp'] = 100
    players[opponent_id]['hp'] = 100
    players[challenger_id]['opponent'] = opponent_id
    players[opponent_id]['opponent'] = challenger_id

    save_players()
    return f"Challenge accepted! {challenger_id} vs {opponent_id}. Let the battle begin!"

def attack_player(attacker_id):
    load_players()
    if attacker_id not in players or 'opponent' not in players[attacker_id]:
        return "You are not in a battle."

    opponent_id = players[attacker_id]['opponent']
    damage = random.randint(5, 15)
    players[opponent_id]['hp'] -= damage
    
    if players[opponent_id]['hp'] <= 0:
        winner_id = attacker_id
        loser_id = opponent_id
        players[winner_id]['credits'] += 100  # Winner gains credits
        players[loser_id]['credits'] -= 50    # Loser loses credits
        del players[winner_id]['opponent']
        del players[loser_id]['opponent']
        save_players()
        return f"{winner_id} wins the battle! {loser_id} is defeated."
    
    save_players()
    return f"{attacker_id} attacks {opponent_id} for {damage} damage. {opponent_id} has {players[opponent_id]['hp']} HP left."

def defend_player(defender_id):
    load_players()
    if defender_id not in players or 'opponent' not in players[defender_id]:
        return "You are not in a battle."

    defense = random.randint(5, 10)
    players[defender_id]['hp'] += defense
    save_players()
    return f"{defender_id} defends and restores {defense} HP. Current HP: {players[defender_id]['hp']}"

# Command for initiating a PvP challenge
async def challenge(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    try:
        opponent_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /challenge <opponent_id>")
        return

    result = challenge_player(user.id, opponent_id)
    await update.message.reply_text(result)

# Command for attacking in PvP battle
async def attack(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    result = attack_player(user.id)
    await update.message.reply_text(result)

# Command for defending in PvP battle
async def defend(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    result = defend_player(user.id)
    await update.message.reply_text(result)

async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in allowed_ids:
        await update.message.reply_text("You do not have permission to use this command.")
        return
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
        except Exception as e:
            logger.error(f"Failed to send message to {uid}: {e}")

async def backup(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    files_to_send = [BOT_DATA_FILE, ALLOWED_IDS_FILE, SUDO_IDS_FILE, USERS_FILE]

    for file_path in files_to_send:
        try:
            with open(file_path, 'rb') as file:
                await context.bot.send_document(chat_id=OWNER_ID, document=file, filename=os.path.basename(file_path))
        except FileNotFoundError:
            await update.message.reply_text(f"File {file_path} not found.")
        except Exception as e:
            logger.error(f"Error sending file {file_path}: {e}")
            await update.message.reply_text(f"Error sending file {file_path}: {str(e)}")

    await update.message.reply_text("Backup completed successfully.")

async def inline_start(update: Update, context: CallbackContext) -> None:
    button = InlineKeyboardButton("Start Bot", url=f"https://t.me/{context.bot.username}?start=start")
    reply_markup = InlineKeyboardMarkup([[button]])
    await update.message.reply_text("Please start the bot by clicking the button below:", reply_markup=reply_markup)

async def add_sudo_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        new_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    sudo_ids.add(new_id)
    save_sudo_ids(sudo_ids)
    await update.message.reply_text(f"User ID {new_id} has been added to sudo IDs.")

async def remove_sudo_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        remove_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if remove_id in sudo_ids:
        sudo_ids.remove(remove_id)
        save_sudo_ids(sudo_ids)
        await update.message.reply_text(f"User ID {remove_id} has been removed from sudo IDs.")
    else:
        await update.message.reply_text(f"User ID {remove_id} was not found in sudo IDs.")


def main():
    application = Application.builder().token(token).build()

    # Add command handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler("flip", flip))
application.add_handler(CommandHandler("dice", dice))
application.add_handler(CommandHandler("football", football))
application.add_handler(CommandHandler("basketball", basketball))
application.add_handler(CommandHandler("pvp", pvp))
application.add_handler(CommandHandler("lottery", lottery))
application.add_handler(CommandHandler("dart", dart))
application.add_handler(CommandHandler("bet", bet))
application.add_handler(CommandHandler("challenge", challenge))
application.add_handler(CommandHandler("attack", attack))
application.add_handler(CommandHandler("defend", defend))
application.add_handler(CommandHandler("add", add_units))
application.add_handler(CommandHandler("roulette", roulette))
application.add_handler(CommandHandler("profile", profile))
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(CommandHandler("backup", backup))
application.add_handler(CommandHandler("inline_start", inline_start))
application.add_handler(CommandHandler("add_sudo_id", add_sudo_id))
application.add_handler(CommandHandler("remove_sudo_id", remove_sudo_id))
application.add_handler(CommandHandler('challenge', challenge))
application.add_handler(CommandHandler('attack', attack))
application.add_handler(CommandHandler('defend', defend))

    application.run_polling()

if __name__ == '__main__':
    main()
