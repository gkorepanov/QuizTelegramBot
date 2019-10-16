# QuizTelegramBot

## Features:
 - Create new quiz posts right in Telegram
 - Post new quizzes to channels / personal chats
 - View statistics for each post and average
 - Photo/text posts support

## Quiz post example
<img src="docs/img/quiz_example.png" width="30%">

## Statistics example
<img src="docs/img/stats_example.png" width="46%">

## Utils
Bot is written using
 - Awesome [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot) package
 - [MongoDB](https://www.mongodb.com/)

## Setup
Dockerfile / docker-compose files are available at the repo, providing
the quizkest way to run the bot locally / on remote server.
Create a file named `.keys` with following content:
```bash
TELEGRAM_TOKEN=<YOUR TOKEN>
```
and run `./build_docker.sh && docker-compose up`

If you want the bot to work behind proxy, add the following lines to `.keys` file:
```
SOCKS5_PROXY=<SOCKS5 proxy ip>
SOCKS5_PROXY_USER=<USERNAME>
SOCKS5_PROXY_PASSWORD=<PASSWORD>
```                               
