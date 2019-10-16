from telegram.ext import (CommandHandler, ConversationHandler,
                          MessageHandler, InlineQueryHandler,
                          CallbackQueryHandler)
from telegram.ext import Filters
from quizbot.handlers.admin import (
    start,
    start_post_creation,
    start_button_creation,
    cancel_post_creation,
    finish_post_creation,
    add_button_alert_text,
    add_button_text,
    display_keyboard_to_choose_correct_answer,
    inline_find_post,
    show_stats
)

from quizbot.handlers.inline import process_inline_button_click
from quizbot.handlers.state import State

import logging

LOGGER = logging.getLogger(__name__)

conv_handler = ConversationHandler(
    name='post_creating_handler',
    entry_points=[CommandHandler('start', start)],
    states={
        State.WAITING_POST: [MessageHandler(Filters.text | Filters.photo, start_post_creation)],
        State.EDITING_POST: [CommandHandler('addbutton', start_button_creation),
                             CommandHandler('finish', display_keyboard_to_choose_correct_answer)],
        State.WAITING_BUTTON_TEXT: [MessageHandler(Filters.text, add_button_text)],
        State.WAITING_BUTTON_ALERT_TEXT: [MessageHandler(Filters.text, add_button_alert_text)],
        State.WAITING_CORRECT_ANSWER: [MessageHandler(Filters.text, finish_post_creation)]
    },
    persistent=True,
    fallbacks=[CommandHandler('cancel', cancel_post_creation),
               CommandHandler('start', start)]
)


handlers = [
    CommandHandler('stats', show_stats),
    CallbackQueryHandler(process_inline_button_click),
    InlineQueryHandler(inline_find_post),
    conv_handler
]
