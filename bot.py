from functools import partial

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
)


def start(update, context, db):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """

    update.message.reply_text(text='Привет!')

    return "ECHO"


def echo(update, context, db):
    """
    Хэндлер для состояния ECHO.

    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """

    users_reply = update.message.text
    update.message.reply_text(users_reply)

    return "ECHO"


def handle_request(update, context, db):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """

    if update.message:
        request = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        print('--------------- callback --------------')
        request = update.callback_query.data
        chat_id = update.callback_query.message.chat_id

    if request == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
        print(f'{user_state=}')

    state_functions = {'START': start, 'ECHO': echo}
    state_handler = state_functions[user_state]

    next_state = state_handler(update, context, db)
    db.set(chat_id, next_state)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(
        MessageHandler(Filters.text, partial(handle_request, db=db))
    )
    # dp.add_handler(CallbackQueryHandler(partial(handle_users_reply, db=db)))
    # dp.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
