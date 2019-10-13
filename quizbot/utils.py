import os


def str2bool(line: str):
    return line.lower() in ['1', 't', 'true', 'y', 'yes']


def is_debug_mode():
    return str2bool(os.environ.get('DEBUG', 'True'))
