from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to keep track of muted users
muted_users = set()

# List of owner IDs
OWNER_IDS = [5667016949, 1474610394]

async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    if user_to_mute in muted_users:
        await update.message.reply_text("This user is already muted.")
        return

    # Add user to muted set
    muted_users.add(user_to_mute)
    logger.info(f"Muted user: {user_to_mute}")
    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted. All their messages will be deleted.")

# Command to unmute a user
async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    if user_to_unmute not in muted_users:
        await update.message.reply_text("This user is not muted.")
        return

    # Remove user from muted set
    muted_users.discard(user_to_unmute)
    logger.info(f"Unmuted user: {user_to_unmute}")
    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")

# Handler to delete messages from muted users
async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            logger.info(f"Deleted message from muted user: {update.message.from_user.id}")
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
