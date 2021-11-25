from functools import partial
from re import X

from environs import Env
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, MessageHandler

from constants import CLIENT_ID
from fetch_moltin_data import (
    add_product_to_cart,
    fetch_authorization_token,
    fetch_cart_items,
    fetch_image_by_id,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
)


def send_products_interface_to_chat(products, chat):
    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products['data']
    ]
    keyboard.append([InlineKeyboardButton('Cart', callback_data='Cart')])

    chat.reply_text('Catalog', reply_markup=InlineKeyboardMarkup(keyboard))


def send_product_details_interface_to_chat(product, chat, auth_token):
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = fetch_image_by_id(auth_token, product_image_id)['data']
    product_image_url = product_image['link']['href']

    product_id = product['id']
    product_name = product['name']
    product_price = product['meta']['display_price']['with_tax']['formatted']
    available_product_quantity = product['meta']['stock']['level']
    product_description = product['description']

    caption = (
        f'{product_name}\n\n{product_price} per kg\n\n'
        f'{available_product_quantity} kg in stock\n\n {product_description}'
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f'{quantity} kg',
                callback_data=f'{product_id};{quantity}',
            )
            for quantity in [1, 5, 10]
        ],
        [
            InlineKeyboardButton('Back', callback_data='Back'),
            InlineKeyboardButton('Cart', callback_data='Cart'),
        ],
    ]

    chat.bot.send_photo(
        chat.chat_id,
        product_image_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def send_cart_interface_to_chat(cart, chat):
    bot_reply = ''.join(
        f"{cart_item['name']}\n"
        f"{cart_item['meta']['display_price']['with_tax']['unit']['formatted']} per kg\n"
        f"{cart_item['quantity']} kg in cart for "
        f"{cart_item['meta']['display_price']['with_tax']['value']['formatted']}\n\n"
        for cart_item in cart['data']
    )

    if not bot_reply:
        bot_reply = 'Your cart is empty'
    else:
        bot_reply = (
            "Your cart:\n\n"
            + bot_reply
            + (
                f"Total: {cart['meta']['display_price']['with_tax']['formatted']}"
            )
        )

    keyboard = [
        [
            InlineKeyboardButton(
                f'Remove {cart_item["name"]} from Cart',
                callback_data=f'{cart_item["id"]}',
            )
        ]
        for cart_item in cart['data']
    ]
    keyboard.append([InlineKeyboardButton('Pay', callback_data='Pay')])
    keyboard.append(
        [InlineKeyboardButton('Back to menu', callback_data='Back to menu')]
    )

    chat.reply_text(
        bot_reply,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def start(update, db):
    """
    Хэндлер для состояния START.
    """

    auth_token = fetch_authorization_token(CLIENT_ID)
    db.set(f'{update.message.chat_id}_auth_token', auth_token)

    products = fetch_products(auth_token)
    send_products_interface_to_chat(products, update.message)

    return 'HANDLE_MENU'


def handle_menu(update, db):
    request = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if request == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        product = fetch_product_by_id(auth_token, request)['data']
        send_product_details_interface_to_chat(product, chat, auth_token)

        return 'HANDLE_DESCRIPTION'


def handle_description(update, db):
    request = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if request == 'Back':
        products = fetch_products(auth_token)
        send_products_interface_to_chat(
            products, update.callback_query.message
        )

        return 'HANDLE_MENU'
    elif request == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        product_id, quantity = request.split(';')
        cart = add_product_to_cart(
            auth_token,
            chat.chat_id,
            product_id,
            int(quantity),
        )

        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'


def handle_cart(update, db):
    request = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    if request == 'Back to menu':
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

        products = fetch_products(auth_token)
        send_products_interface_to_chat(
            products, update.callback_query.message
        )

        return 'HANDLE_MENU'
    if request == 'Pay':
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

        bot_reply = 'Enter your email'
        keyboard = [
            [
                InlineKeyboardButton(
                    'Back to cart',
                    callback_data='Back to cart',
                )
            ],
        ]

        chat.reply_text(
            bot_reply,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return 'WAITING_EMAIL'
    else:
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

        cart = remove_cart_item_by_id(
            auth_token,
            chat.chat_id,
            request,
        )
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'


def wait_email(update, db):
    if update.message:
        request = update.message.text
        chat = update.message
    elif update.callback_query:
        request = update.callback_query.data
        chat = update.callback_query.message

    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    if request == 'Back to cart':
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        chat.reply_text(f'You sent me an email: {request}')


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
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': wait_email,
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
