from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def start(update, context):
    update.message.reply_text("Press the button to send a message to the bot owner:", reply_markup=reply_markup)

def main():
    updater = Updater("6759114451:AAGWHSxbJGZwP_a4OFrREL-eDVUGyXVYm0U", use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

main()
