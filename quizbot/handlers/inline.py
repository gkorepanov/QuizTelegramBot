from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext
from bson import ObjectId


import quizbot.db.models
import quizbot.db as db
import quizbot.handlers.post as postutils

import logging

LOGGER = logging.getLogger(__name__)
INLINE_STATS = '__view_stats__'


def process_inline_button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    post_id, data = query.data.split('|')
    if data == INLINE_STATS:
        return show_post_statistics(query, ObjectId(post_id))
    else:
        return process_quiz_button_click(update, ObjectId(post_id), data)


def show_post_statistics(query: CallbackQuery, post_id: ObjectId) -> None:
    try:
        post = db.models.find_post(post_id)
    except:
        LOGGER.error(f"Could not find post {post_id} on statistics button click")
        query.answer(text="Post has not been found. "
                          "Approach the developer.", show_alert=False)
        return

    clicks_count, correct_clicks_count = db.models.count_post_clicks(post)
    query.answer(text=f"Правильных ответов: {correct_clicks_count} / {clicks_count}",
                 show_alert=True)


def process_quiz_button_click(update: Update, post_id: ObjectId, button_text: str) -> None:
    query = update.callback_query

    try:
        post = db.models.find_post(post_id)
    except:
        LOGGER.error(f"Could not find post {post_id} on quiz button click")
        query.answer(text="Пост не найден в базе данных. "
                          "Обратитесь к разработчику.", show_alert=False)
        return

    LOGGER.warning(f"Button `{button_text}` clicked for post: {post}")

    user_id = db.models.find_or_create_user(update.effective_user.id)

    do_update = True
    clicked, answer = db.models.is_post_clicked_by_user(post_id=post_id, user_id=user_id)

    if clicked:
        if answer != button_text:
            query.answer(text="Ответ нельзя изменить!", show_alert=False)
            return
        else:
            do_update = False

    is_correct = post['buttons'][button_text]['is_correct']

    if do_update:
        db.models.update_stats_on_click(user_id=user_id, post_id=post_id,
                                        user_answer=button_text, is_correct=is_correct)

    alert_text = postutils.make_alert_text(initial_text=post['buttons'][button_text]['alert_text'],
                                           count=post['buttons'][button_text]['clicks_count'],
                                           total_count=post['clicks_count'],
                                           is_correct=is_correct)

    query.answer(text=alert_text, show_alert=True)
