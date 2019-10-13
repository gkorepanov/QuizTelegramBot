from telegram.ext import CommandHandler, ConversationHandler, MessageHandler
from telegram.ext import Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class State:
    WAITING_POST = 'WAITING_POST'
    EDITING_POST = 'EDITING_POST'
    WAITING_BUTTON_TEXT = 'WAITING_BUTTON_TEXT'
    WAITING_BUTTON_REPLY = 'WAITING_BUTTON_REPLY'


def start(update, context):
    update.message.reply_text("Hi! Send me arbitrary post (image or text)!")
    return State.WAITING_POST


def add_post(update, context):
    update.message.reply_text("Great, I've got a post content from you! "
                              "Now add buttons with /addbutton command.")
    context.user_data['buttons'] = []
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1]
    else:
        context.user_data['text'] = update.message.text
    return State.EDITING_POST


def add_button(update, context):
    update.message.reply_text("Send me the button text!")
    return State.WAITING_BUTTON_TEXT


def add_button_text(update, context):
    context.user_data['buttons'].append({'text': update.message.text})
    update.message.reply_text("Fine. Now send me the alert text to be shown "
                              "when the button is pressed by user.")
    return State.WAITING_BUTTON_REPLY


def add_button_reply(update, context):
    context.user_data['buttons'][-1]['reply'] = update.message.text
    button_text = context.user_data['buttons'][-1]['text']
    update.message.reply_text(f"Great, the button {button_text} added! "
                              f"Now either /add_button or /finish post creation.")
    return State.EDITING_POST


def finish_post_creation(update, context):
    if context.user_data['buttons']:
        keyboard = [InlineKeyboardButton(button['text'], callback_data=str(i))
                    for i, button in enumerate(context.user_data['buttons'])]

        keyboard.append(InlineKeyboardButton('Publish to channel',
                                             callback_data='#some_id',
                                             switch_inline_query=True))

        markup = InlineKeyboardMarkup(keyboard)
    else:
        markup = None

    if 'text' in context.user_data:
        update.message.reply_text(context.user_data['text'], reply_markup=markup)
    elif 'photo' in context.user_data:
        update.message.reply_photo(context.user_data['photo'], reply_markup=markup)
    else:
        raise ValueError("No data to create post found")

    return State.WAITING_POST


def cancel(update, context):
    update.message.reply_text("You canceled post creation. "
                              "Just send me another one when you're back!")
    return State.WAITING_POST


start_handler = CommandHandler('start', start)


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        State.WAITING_POST: [MessageHandler(Filters.text | Filters.photo, add_post)],
        State.EDITING_POST: [CommandHandler('addbutton', add_button),
                             CommandHandler('finish', finish_post_creation)],
        State.WAITING_BUTTON_TEXT: [MessageHandler(Filters.text, add_button_text)],
        State.WAITING_BUTTON_REPLY: [MessageHandler(Filters.text, add_button_reply)]
    },
    persistent=True,
    fallbacks=[CommandHandler('cancel', cancel)]
)
