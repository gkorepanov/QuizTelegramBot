from telegram.ext import (CommandHandler, ConversationHandler,
                          MessageHandler, InlineQueryHandler,
                          CallbackQueryHandler)
from telegram.ext import Filters

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram import InputTextMessageContent
from telegram import InlineQueryResultArticle, InlineQueryResultCachedPhoto
from quizbot.db import db
from pymongo import ReturnDocument
from bson.objectid import ObjectId

import logging
import datetime

LOGGER = logging.getLogger(__name__)


class State:
    WAITING_POST = 'WAITING_POST'
    EDITING_POST = 'EDITING_POST'
    WAITING_BUTTON_TEXT = 'WAITING_BUTTON_TEXT'
    WAITING_BUTTON_ALERT_TEXT = 'WAITING_BUTTON_ALERT_TEXT'
    WAITING_RIGHT_ANSWER = 'WAITING_RIGHT_ANSWER'


def start(update, context):
    update.message.reply_text("Hi! Send me arbitrary post (image or text)!")
    return State.WAITING_POST


def add_post(update, context):
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


def add_button(update, context):
    update.message.reply_text("Send me the button text!")
    return State.WAITING_BUTTON_TEXT


def add_button_text(update, context):
    context.user_data['buttons'][update.message.text] = {
        'alert_text': '',
        'clicks_count': 0,
        'is_correct': False
    }
    context.user_data['button_text'] = update.message.text
    update.message.reply_text("Fine. Now send me the alert text to be shown "
                              "when the button is pressed by user.")
    return State.WAITING_BUTTON_ALERT_TEXT


def add_button_alert_text(update, context):
    button_text = context.user_data['button_text']
    context.user_data['buttons'][button_text]['alert_text'] = update.message.text
    update.message.reply_text(f"Great, the button {button_text} added! "
                              f"Now either /addbutton or /finish post creation.")
    return State.EDITING_POST


def get_post_keyboard(post, post_id):
    if not post['buttons']:
        return []

    return [[InlineKeyboardButton(text, callback_data=f"{post_id}|{text}")
            for text in post['buttons']]]


def post_type(post):
    if post['text'] and (not post['photo']):
        return 'text'
    if post['photo'] and (not post['text']):
        return 'photo'
    raise ValueError("Invalid post type")


def display_correct_answer_keyboard(update, context):
    buttons = context.user_data['buttons']
    keyboard = [[KeyboardButton(text) for text in buttons]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Choose correct answer:', reply_markup=markup)
    return State.WAITING_RIGHT_ANSWER


def finish_post_creation(update, context):
    buttons = context.user_data['buttons']
    correct_answer = update.message.text

    if correct_answer not in buttons:
        update.message.reply_text('No such answer, choose correct one from keyboard!')
        return State.WAITING_RIGHT_ANSWER
    else:
        update.message.reply_text('Fine, here is your new post:', reply_markup=ReplyKeyboardRemove())

    buttons[correct_answer]['is_correct'] = True
    photo = context.user_data['photo']
    post = {
        'text': context.user_data['text'],
        'photo': photo.file_id if photo else None,
        'buttons': buttons
    }

    post_id = db.posts.insert_one(post).inserted_id
    LOGGER.info(f"Generated post with id {post_id}: {post}")

    keyboard = get_post_keyboard(post, post_id)
    keyboard.append([InlineKeyboardButton('Publish to channel',
                                          switch_inline_query=f'#{post_id}')])
    markup = InlineKeyboardMarkup(keyboard)

    if post_type(post) == 'text':
        update.message.reply_text(post['text'], reply_markup=markup)
    elif post_type(post) == 'photo':
        update.message.reply_photo(photo, reply_markup=markup)

    return State.WAITING_POST


def get_content_description(post):
    content = ""

    if post_type(post) == 'text':
        content += f"text '{post['text']}'"
    elif post_type(post) == 'photo':
        content += f"photo"

    content += f" with {len(post['buttons'])} buttons"

    return content


def inlinequery(update, context):
    query = update.inline_query.query
    if not query.startswith('#'):
        return

    post_id = query[1:]

    LOGGER.info(f"Inline query with id {post_id}")

    try:
        post = db.posts.find_one({"_id": ObjectId(post_id)})
    except:
        LOGGER.error(f"Error querying ID {post_id}")
        return

    if not post:
        LOGGER.error(f"Could not find ID {post_id} in database")
        return

    content = get_content_description(post)
    markup = InlineKeyboardMarkup(get_post_keyboard(post, post_id))

    result = None
    if post_type(post) == 'text':
        result = InlineQueryResultArticle(
            id=post_id,
            title="New post",
            description=f"Create new post with {content}",
            input_message_content=InputTextMessageContent(post['text']),
            reply_markup=markup)

    elif post_type(post) == 'photo':
        result = InlineQueryResultCachedPhoto(
            id=post_id,
            photo_file_id=post['photo'],
            title="New post",
            description=f"Create new post with {content}",
            reply_markup=markup)

    update.inline_query.answer([result])


def get_total_clicks(post):
    return sum(button['clicks_count'] for button in post['buttons'].values())


def make_alert_text(initial_text, count, total_count, is_correct):
    alert_text = initial_text

    if is_correct:
        alert_text = '✅ Правильно!\n\n' + alert_text
    else:
        alert_text = '❌ Неверно. \n\n' + alert_text

    if total_count:
        alert_text += f'\n\nОтветили так же: {count / total_count:.0%} (из {total_count}).'
    else:
        alert_text += '\n\nВы ответили первым!'

    return alert_text


def update_or_create_user(telegram_id: str):
    user = db.users.find_one({'telegram_id': telegram_id})
    if user:
        return user

    user = {
        'telegram_id': telegram_id,
        'last_click': datetime.datetime.now(),
        'posts_clicked': {}
    }

    return db.users.find_one({'_id': db.users.insert_one(user).inserted_id})


def update_data_from_click(user, post, button_text: str, is_correct: bool):
    count = post['buttons'][button_text]['clicks_count']
    db.posts.update_one({'_id': post['_id']},
                        {'$set': {f'buttons.{button_text}.clicks_count': count + 1}})
    db.users.update_one({'_id': user['_id']},
                        {'$set': {f"posts_clicked.{post['_id']}.correct": is_correct,
                                  f"posts_clicked.{post['_id']}.timestamp": datetime.datetime.now(),
                                  f"posts_clicked.{post['_id']}.answer": button_text}})


def quiz_button_click(update, context):
    query = update.callback_query
    post_id, button_text = query.data.split('|')

    post = db.posts.find_one({"_id": ObjectId(post_id)})
    user = update_or_create_user(update.effective_user.id)

    LOGGER.warning(f"Button `{button_text}` clicked for post: {post}")

    do_update = True

    if post_id in user['posts_clicked']:
        answer = user['posts_clicked'][post_id]['answer']
        if answer != button_text:
            query.answer(text="Ответ нельзя изменить!", show_alert=False)
            return

        do_update = False

    count = post['buttons'][button_text]['clicks_count']
    is_correct = post['buttons'][button_text]['is_correct']
    alert_text = post['buttons'][button_text]['alert_text']
    total_count = get_total_clicks(post)

    if do_update:
        update_data_from_click(user, post, button_text, is_correct)

    alert_text = make_alert_text(alert_text, count, total_count, is_correct)
    query.answer(text=alert_text, show_alert=True)


def cancel(update, context):
    update.message.reply_text("You canceled post creation. "
                              "Just send me another one when you're back!")
    return State.WAITING_POST


conv_handler = ConversationHandler(
    name='post_creating_handler',
    entry_points=[CommandHandler('start', start)],
    states={
        State.WAITING_POST: [MessageHandler(Filters.text | Filters.photo, add_post)],
        State.EDITING_POST: [CommandHandler('addbutton', add_button),
                             CommandHandler('finish', display_correct_answer_keyboard)],
        State.WAITING_BUTTON_TEXT: [MessageHandler(Filters.text, add_button_text)],
        State.WAITING_BUTTON_ALERT_TEXT: [MessageHandler(Filters.text, add_button_alert_text)],
        State.WAITING_RIGHT_ANSWER: [MessageHandler(Filters.text, finish_post_creation)]
    },
    persistent=True,
    fallbacks=[CommandHandler('cancel', cancel),
               CommandHandler('start', start)]
)

quiz_button_click_handler = CallbackQueryHandler(quiz_button_click)
inline_handler = InlineQueryHandler(inlinequery)

handlers = [quiz_button_click_handler, inline_handler, conv_handler]
