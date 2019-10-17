"""
MongoDb documents structure:

user = {
    'telegram_id': <TELEGRAM ID>,
    'last_click': <TIMESTAMP>,
    'posts_clicked': {
        <POST ID>: {'timestamp': <TIMESTAMP>, 'answer': <TEXT>},
        <POST ID>: {'timestamp': <TIMESTAMP>, 'answer': <TEXT>}
    },
    'posts_created': {
        <POST ID>: {'timestamp': <TIMESTAMP>},
        <POST ID>: {'timestamp': <TIMESTAMP>}
    },
    posts_created_count: <INT>
}

post = {
    'text': <TEXT>,
    'photo': <TELEGRAM PHOTO ID>,
    'clicks_count': <INT>,
    'correct_clicks_count': <INT>,
    'buttons': {
        <TEXT>: {
            'clicks_count': <INT>,
            'alert_text': <TEXT>,
            'is_correct': <BOOL>
        }
    },
    'author': <USER ID>
}
"""


from typing import Dict, Optional, Tuple
import datetime

from quizbot.db.mongo import get_collection
from pymongo import ReturnDocument
from bson import ObjectId


def create_post(text: Optional[str],
                photo: Optional[str],
                buttons: Dict,
                user_id: ObjectId) -> ObjectId:
    post = {
        'text': text,
        'photo': photo,
        'buttons': buttons,
        'author': user_id,
        'clicks_count': 0,
        'correct_clicks_count': 0
    }
    post_id = get_collection('posts').insert_one(post).inserted_id

    get_collection('users').update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {f'posts_created.{post_id}.timestamp': datetime.datetime.now()},
         '$inc': {f'posts_created_count': 1}})

    return post_id


def find_post(post_id: ObjectId) -> Dict:
    post = get_collection('posts').find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError(f"No post ID {post_id} in database")
    return post


def is_post_clicked_by_user(post_id: ObjectId, user_id: ObjectId) -> Tuple[bool, str]:
    field = f'posts_clicked.{post_id}.answer'
    result = get_collection('users').find_one(
        {f'_id': ObjectId(user_id), field: {'$exists': True}},
        {field: 1})

    if not result:
        return False, ''

    return True, result['posts_clicked'][str(post_id)]['answer']


def find_or_create_user(telegram_id: str) -> ObjectId:
    return get_collection('users').find_one_and_update(
        {'telegram_id': telegram_id},
        {'$set': {'telegram_id': telegram_id}},
        {},
        return_document=ReturnDocument.AFTER,
        upsert=True)['_id']


def update_stats_on_click(user_id: ObjectId, post_id: ObjectId,
                          user_answer: str, is_correct: bool) -> None:
    timestamp = datetime.datetime.now()
    get_collection('posts').update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {f'buttons.{user_answer}.clicks_count': 1,
                  f'clicks_count': 1,
                  f'correct_clicks_count': int(is_correct)}})

    get_collection('users').update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {f"last_click": timestamp,
                  f"posts_clicked.{post_id}.timestamp": timestamp,
                  f"posts_clicked.{post_id}.answer": user_answer}})


def total_user_posts(user_id: ObjectId) -> int:
    return get_collection('users').find_one(
        {'_id': ObjectId(user_id)},
        {'posts_created_count': 1}).get('posts_created_count', 0)


def count_user_posts_clicks(user_id: ObjectId) -> Tuple[int, int]:
    posts = get_collection('users').find_one(
        {'_id': ObjectId(user_id)},
        {'posts_created': 1})['posts_created']

    posts_info = get_collection('posts').find(
        {'_id': {"$in": [ObjectId(post_id) for post_id in posts]}},
        {'clicks_count': 1, 'correct_clicks_count': 1}
    )

    clicks_count = 0
    correct_clicks_count = 0
    for info in posts_info:
        clicks_count += info.get('clicks_count', 0)
        correct_clicks_count += info.get('correct_clicks_count', 0)

    return clicks_count, correct_clicks_count


def count_post_clicks(post: Dict) -> Tuple[int, int]:
    return post['clicks_count'], post['correct_clicks_count']


def is_post_existing(post_id: ObjectId) -> bool:
    return get_collection('posts').find_one(
        {'_id': ObjectId(post_id)}, {}) is not None

