from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to keep track of muted users
muted_users = set()

# List of owner IDs
OWNER_IDS = [5667016949, 1474610394]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your bot. Use /amute and /aunmute to control users.")

async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to the user you want to mute.")
        return

    user_to_mute = update.message.reply_to_message.from_user.id
    chat_id = update.message.chat_id
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been muted.")

    except Exception as e:
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

    try:
        muted_users.discard(user_to_unmute)

        # Remove restrictions
        await context.bot.restrict_chat_member(
            chat_id,
            user_to_unmute,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(f"User {update.message.reply_to_message.from_user.full_name} has been unmuted.")

    except Exception as e:
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

def main() -> None:
    port = int(os.getenv("PORT", 8000))
    # Replace 'YOUR_TOKEN_HERE' with your actual bot token
    application = Application.builder().token("6970211159:AAH-D8Ixmb3ZAIaTN2ZsulHNIhEPhShqMh4").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("amute", amute))
    application.add_handler(CommandHandler("aunmute", aunmute))

    # Add message handler to delete messages from muted users
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, delete_muted_messages))

    application.run_polling(port=port)

if __name__ == '__main__':
    main()
