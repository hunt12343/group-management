from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
import logging

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to keep track of muted users
muted_users = set()

# List of owner IDs
MUTE_IDS = [5667016949, 1474610394, 1322464076]

async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Mute_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    try:
        # Add user to the muted list
        muted_users.add(user_to_mute)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_mute,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted.")
    except Exception as e:
        await update.message.reply_text(f"Muted Admin haha!!")

async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Mute_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    try:
        # Remove user from the muted list
        muted_users.discard(user_to_unmute)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_unmute,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")
    except Exception as e:
        await update.message.reply_text(f"Unmuted!!!")

async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message from muted user: {e}")
