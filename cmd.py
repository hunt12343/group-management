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
    chat_id = update.message.chat_id

    logger.info(f"Attempting to mute user {user_to_mute} in chat {chat_id}")

    try:
        # Check if the bot has admin privileges
        chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if not chat_member.can_restrict_members:
            await update.message.reply_text("I don't have permission to restrict members. Please make me an admin with the required rights.")
            return

        # Ensure the user to mute is not an admin
        target_member = await context.bot.get_chat_member(chat_id, user_to_mute)
        if target_member.status in ["administrator", "creator"]:
            await update.message.reply_text("I cannot mute administrators or the group owner.")
            return

        # Mute the user
        muted_users.add(user_to_mute)
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_to_mute,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted.")
    except Exception as e:
        logger.error(f"Failed to mute user {user_to_mute}: {e}")
        await update.message.reply_text(f"Failed to mute user: {e}")


async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to unmute.")
        return

    user_to_unmute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id

    logger.info(f"Attempting to unmute user {user_to_unmute} in chat {chat_id}")

    try:
        # Check if the bot has admin privileges
        chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if not chat_member.can_restrict_members:
            await update.message.reply_text("I don't have permission to restrict members. Please make me an admin with the required rights.")
            return

        # Ensure the user is muted before unmuting
        if user_to_unmute not in muted_users:
            await update.message.reply_text("This user is not muted.")
            return

        # Unmute the user by restoring permissions
        muted_users.discard(user_to_unmute)
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_to_unmute,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")
    except Exception as e:
        logger.error(f"Failed to unmute user {user_to_unmute}: {e}")
        await update.message.reply_text(f"Failed to unmute user: {e}")


async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message from muted user: {e}")
