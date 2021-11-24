from functools import partial

from environs import Env
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, MessageHandler

from constants import CLIENT_ID
from fetch_moltin_data import (
    fetch_authorization_token,
    fetch_products,
    fetch_product_by_id,
)


def start(update, db):
    """
    Хэндлер для состояния START.
    """

    token = fetch_authorization_token(CLIENT_ID)
    db.set(f'{update.message.chat_id}_auth_token', token)

    products = fetch_products(token)

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products['data']
    ]

    update.message.reply_text(
        'Please choose:', reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return 'HANDLE_MENU'


def echo(update, db):
    """
    Хэндлер для состояния ECHO.
    """

    update.message.reply_text(update.message.text)

    return 'ECHO'


def handle_menu(update, db):
    """
    Хэндлер для состояния HANDLE_MENU.
    """

    product_id = update.callback_query.data
    chat_id = update.callback_query.message.chat_id

    token = db.get(f'{chat_id}_auth_token').decode()
    product = fetch_product_by_id(token, product_id)['data']

    message = (
        f'{product["name"]}\n\n'
        f'{product["meta"]["display_price"]["with_tax"]["formatted"]} per kg\n\n'
        f'{product["meta"]["stock"]["level"]}kg in stock\n\n'
        f'{product["description"]}'
    )

    update.callback_query.message.reply_text(message)

    return 'START'


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
        request = update.callback_query.data
        chat_id = update.callback_query.message.chat_id

    if request == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    state_functions = {
        'START': start,
        'ECHO': echo,
        'HANDLE_MENU': handle_menu,
    }
    state_handler = state_functions[user_state]

    next_state = state_handler(update, db)

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
    dp.add_handler(CallbackQueryHandler(partial(handle_request, db=db)))
    updater.start_polling()
