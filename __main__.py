#!/usr/bin/env python3

# Generic imports
import logging
import os

# Custom imports
import quizbot.runner
from quizbot.utils import str2bool
from quizbot.handlers import handlers


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if __name__ == '__main__':
    token = os.environ['TELEGRAM_TOKEN']
    if str2bool(os.environ.get('USE_TELEGRAM_WEBHOOK', 'False')):
        raise NotImplementedError()
    else:
        quizbot.runner.run_get_updates(token=token, handlers=handlers)
