from typing import Dict, List
from telegram import InlineKeyboardButton


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
                    is_correct: bool):
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
