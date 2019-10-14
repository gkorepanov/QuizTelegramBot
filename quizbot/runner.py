# Generic imports
import logging
import os
from typing import Dict, List, Callable, Optional

# Telegram imports
from telegram.ext import Updater
from telegram.ext import PicklePersistence
from telegram import Update

# Custom imports
from quizbot.utils import str2bool


LOGGER = logging.getLogger(__name__)


def log_error(update: Update, context):
    LOGGER.fatal(context.error, exc_info=True)


def get_socks_proxy_params() -> Optional[Dict]:
    if not str2bool(os.environ.get('USE_SOCKS5_PROXY', 'False')):
        return None

    proxy_params = dict(proxy_url=os.environ['SOCKS5_PROXY'])
    if 'SOCKS5_PROXY_USER' in os.environ and \
            'SOCKS5_PROXY_PASSWORD' in os.environ:
        proxy_params['urllib3_proxy_kwargs'] = {
            'username': os.environ['SOCKS5_PROXY_USER'],
            'password': os.environ['SOCKS5_PROXY_PASSWORD']
        }

    return proxy_params


def run_get_updates(token: str, handlers: List[Callable]) -> None:
    proxy_params = get_socks_proxy_params()
    persistence = PicklePersistence(os.environ['PERSISTENCE_DATA_FILE'])

    if proxy_params is not None:
        LOGGER.warning(f"Using SOCKS5 proxy:\n{proxy_params}")

    updater = Updater(token, request_kwargs=proxy_params,
                      use_context=True, persistence=persistence)

    dp = updater.dispatcher

    for handler in handlers:
        dp.add_handler(handler)

    dp.add_error_handler(log_error)
    updater.start_polling()
    updater.idle()
