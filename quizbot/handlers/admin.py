from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram import InputTextMessageContent
from telegram import InlineQueryResultArticle, InlineQueryResultCachedPhoto
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

import quizbot.handlers.post as postutils
import quizbot.db as db
import quizbot.db.models

from quizbot.handlers.inline import INLINE_STATS
from quizbot.handlers.state import State


import logging

LOGGER = logging.getLogger(__name__)


def start(update, context: CallbackContext) -> str:
    update.message.reply_text("Hi! Send me arbitrary post (image or text)!")
    return State.WAITING_POST


def start_post_creation(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("Great, I've got a post content from you! "
                              "Now add buttons with /addbutton command.")

    context.user_data['text'] = None
    context.user_data['photo'] = None
    context.user_data['buttons'] = dict()

    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1]
    else:
        context.user_data['text'] = update.message.text
    return State.EDITING_POST


def start_button_creation(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("Send me the button text!")
    return State.WAITING_BUTTON_TEXT


def add_button_text(update: Update, context: CallbackContext) -> str:
    context.user_data['buttons'][update.message.text] = {
        'alert_text': '',
        'clicks_count': 0,
        'correct_clicks_count': 0,
        'is_correct': False
    }
    context.user_data['button_text'] = update.message.text
    update.message.reply_text("Fine. Now send me the alert text to be shown "
                              "when the button is pressed by user.")
    return State.WAITING_BUTTON_ALERT_TEXT


def add_button_alert_text(update: Update, context: CallbackContext) -> str:
    button_text = context.user_data['button_text']
    context.user_data['buttons'][button_text]['alert_text'] = update.message.text
    update.message.reply_text(f"Great, the button {button_text} added! "
                              f"Now either /addbutton or /finish post creation.")
    return State.EDITING_POST


def display_keyboard_to_choose_correct_answer(update: Update, context: CallbackContext) -> str:
    buttons = context.user_data['buttons']
    keyboard = [[KeyboardButton(text) for text in buttons]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Choose correct answer:', reply_markup=markup)
    return State.WAITING_CORRECT_ANSWER


def finish_post_creation(update: Update, context: CallbackContext) -> str:
    buttons = context.user_data['buttons']
    correct_answer = update.message.text

    if correct_answer not in buttons:
        update.message.reply_text(f'No such button: {correct_answer}!')
        return State.WAITING_CORRECT_ANSWER
    else:
        update.message.reply_text('Fine, here is your new post:', reply_markup=ReplyKeyboardRemove())

    buttons[correct_answer]['is_correct'] = True
    photo = context.user_data['photo']

    user_id = db.models.find_or_create_user(update.effective_user.id)
    post_id = db.models.create_post(text=context.user_data['text'],
                                    photo=photo.file_id if photo else None,
                                    buttons=buttons,
                                    user_id=user_id)
    post = db.models.find_post(post_id)

    LOGGER.info(f"Generated post: {post}")

    keyboard = postutils.get_post_keyboard(buttons=buttons, post_id=post_id)
    keyboard.append([InlineKeyboardButton('Publish to channel',
                                          switch_inline_query=f'#{post_id}')])
    keyboard.append([InlineKeyboardButton('Post statistics',
                                          callback_data=f'{post_id}|{INLINE_STATS}')])
    markup = InlineKeyboardMarkup(keyboard)

    if postutils.post_type(post) == 'text':
        update.message.reply_text(post['text'], reply_markup=markup)
    elif postutils.post_type(post) == 'photo':
        update.message.reply_photo(photo, reply_markup=markup)

    return State.WAITING_POST


def inline_find_post(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query

    if not query.startswith('#'):
        return

    post_id = query[1:]
    LOGGER.info(f"Inline query with id {post_id}")

    try:
        post = db.models.find_post(post_id)
    except:
        LOGGER.error(f"Error looking for ID {post_id} in inline query")
        return

    content = postutils.get_content_description(post)
    markup = InlineKeyboardMarkup(postutils.get_post_keyboard(post['buttons'], post_id))

    result = None
    if postutils.post_type(post) == 'text':
        result = InlineQueryResultArticle(
            id=post_id,
            title="New post",
            description=f"Create new post with {content}",
            input_message_content=InputTextMessageContent(post['text']),
            reply_markup=markup)

    elif postutils.post_type(post) == 'photo':
        result = InlineQueryResultCachedPhoto(
            id=post_id,
            photo_file_id=post['photo'],
            title="New post",
            description=f"Create new post with {content}",
            reply_markup=markup)

    update.inline_query.answer([result])


def cancel_post_creation(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("You canceled post creation. "
                              "Just send me another one when you're back!")
    return State.WAITING_POST


def show_stats(update: Update, context: CallbackContext) -> None:
    user_id = db.models.find_or_create_user(update.effective_user.id)
    posts_count = db.models.total_user_posts(user_id)

    if posts_count == 0:
        update.message.reply_text("You have no posts yet!")
        return

    clicks_count, correct_clicks_count = db.models.count_user_posts_clicks(user_id)
    average_clicks_per_post = float(clicks_count) / posts_count

    if clicks_count == 0:
        average_correct_percentage = 0
    else:
        average_correct_percentage = float(correct_clicks_count) / clicks_count

    update.message.reply_text(f"Statistics of your posts:\n"
                              f"  - *Total number*: {posts_count}\n"
                              f"  - *Average users answers per post*: {average_clicks_per_post}\n"
                              f"  - *Average correct answers*: {average_correct_percentage:.0%}",
                              parse_mode=ParseMode.MARKDOWN)
