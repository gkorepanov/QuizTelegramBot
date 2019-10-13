from telegram.ext import CommandHandler


def start(update, context):
    update.message.reply_text(
        'Hi! My name is Quiz Bot. Send me arbitrary post (image or text)!')


start_handler = CommandHandler('start', start)
