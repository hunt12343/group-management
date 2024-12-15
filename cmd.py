from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set of muted users
muted_users = set()

# List of owner IDs
Mute_IDS = [5667016949, 1474610394, 1322464076]

async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Mute_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    # Add user to the muted set to delete their messages later
    muted_users.add(user_to_mute)

    try:
        # Attempt to restrict user (may fail if they are admin)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_mute,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        logger.error(f"Error muting user {user_to_mute}: {e}")

    # Respond as if the user was muted, regardless of success
    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted.")

async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Mute_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    # Remove user from the muted set
    muted_users.discard(user_to_unmute)

    try:
        # Attempt to lift restrictions (may fail if they were not muted)
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_unmute,
            permissions=ChatPermissions(can_send_messages=True)
        )
    except Exception as e:
        logger.error(f"Error unmuting user {user_to_unmute}: {e}")

    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")

async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            # Delete messages from muted users
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message from muted user {update.message.from_user.id}: {e}")
