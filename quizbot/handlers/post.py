from typing import Dict, List, Tuple, Optional
from telegram import InlineKeyboardButton

MAX_TELEGRAM_API_POST_TEXT_LENGTH = 4096
MAX_TELEGRAM_API_ALERT_TEXT_LENGTH = 200


def get_post_keyboard(buttons, post_id) -> List[List[InlineKeyboardButton]]:
    if not buttons:
        return []

    return [[InlineKeyboardButton(text, callback_data=f"{post_id}|{text}")
            for text in buttons]]


def post_type(post: Dict) -> str:
    if post['text'] and (not post['photo']):
        return 'text'
    if post['photo'] and (not post['text']):
        return 'photo'
    raise ValueError("Invalid post type")


def get_content_description(post: Dict) -> str:
    content = ""

    if post_type(post) == 'text':
        content += f"text '{post['text']}'"
    elif post_type(post) == 'photo':
        content += f"photo"

    content += f" with {len(post['buttons'])} buttons"

    return content


def make_alert_text(*, initial_text: str,
                    count: int, total_count: int,
                    is_correct: bool,
                    show_header: bool = False):
    alert_text = initial_text

    if show_header:
        header = '✅ Правильно!\n\n' if is_correct else '❌ Неверно. \n\n'
        alert_text = header + alert_text

    percentage = count / total_count if total_count else 0
    alert_text += f'\n\nОтветили так же: {percentage:.0%} (из {total_count}).'

    return alert_text


def is_main_text_valid(text: str) -> bool:
    if len(text) > MAX_TELEGRAM_API_POST_TEXT_LENGTH:
        return False
    return True


def is_alert_text_valid(alert_text: str) -> Tuple[bool, Optional[str]]:
    for _is_correct in [False, True]:
        for _total_count in [0, 155, 1000]:
            for _count in [0, _total_count // 2, _total_count]:
                _text = make_alert_text(initial_text=alert_text,
                                        count=_count,
                                        total_count=_total_count,
                                        is_correct=_is_correct)
                if len(_text) > MAX_TELEGRAM_API_ALERT_TEXT_LENGTH:
                    return False, _text
    return True, None
