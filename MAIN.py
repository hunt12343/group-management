from token_1 import token
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from aiohttp import web

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to keep track of muted users
muted_users = set()

# List of owner IDs
OWNER_IDS = [5667016949]

# List of admin IDs
admin_ids = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your bot. Use /amute, /aunmute, /addowner, /add_admin, and /remove_admin to control users.")


async def amute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS and update.effective_user.id not in admin_ids:
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
        await update.message.reply_text(f"Failed to mute user: {e}")


async def aunmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS and update.effective_user.id not in admin_ids:
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
        await update.message.reply_text(f"Failed to unmute user: {e}")


async def add_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the user ID to add as an owner. Usage: /addowner <user_id>")
        return

    try:
        new_owner_id = int(context.args[0])
        if new_owner_id in OWNER_IDS:
            await update.message.reply_text("This user is already an owner.")
        else:
            OWNER_IDS.append(new_owner_id)
            await update.message.reply_text(f"User ID {new_owner_id} has been added as an owner.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the user ID to add as an admin. Usage: /add_admin <user_id>")
        return

    try:
        new_admin_id = int(context.args[0])
        if new_admin_id in admin_ids:
            await update.message.reply_text("This user is already an admin.")
        else:
            admin_ids.add(new_admin_id)
            await update.message.reply_text(f"User ID {new_admin_id} has been added as an admin.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")


async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the user ID to remove as an admin. Usage: /remove_admin <user_id>")
        return

    try:
        admin_id_to_remove = int(context.args[0])
        if admin_id_to_remove in admin_ids:
            admin_ids.remove(admin_id_to_remove)
            await update.message.reply_text(f"User ID {admin_id_to_remove} has been removed as an admin.")
        else:
            await update.message.reply_text("This user is not an admin.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")


async def delete_muted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id in muted_users:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message from muted user: {e}")


async def health_check(request):
    return web.Response(text="OK", status=200)


def start_health_server():
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    return app


def main() -> None:
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("amute", amute))
    application.add_handler(CommandHandler("aunmute", aunmute))
    application.add_handler(CommandHandler("addowner", add_owner, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("add_admin", add_admin, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("remove_admin", remove_admin, filters=filters.ChatType.PRIVATE))

    # Add message handler to delete messages from muted users
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, delete_muted_messages))

    # Start health check server
    runner = web.AppRunner(start_health_server())
    application.run_polling(poll_interval=5, runner=runner)


if __name__ == "__main__":
    main()
