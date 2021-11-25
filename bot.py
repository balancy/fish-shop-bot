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
    create_customer,
    fetch_authorization_token,
    fetch_cart_items,
    fetch_image_by_id,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
    InvalidEmail,
    UserExistsError,
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
        f'{product_name}\n\n'
        f'{product_price} per kg\n\n'
        f'{available_product_quantity} kg in stock\n\n'
        f'{product_description}'
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
            InlineKeyboardButton('Back to menu', callback_data='Back to menu'),
            InlineKeyboardButton('Cart', callback_data='Cart'),
        ],
    ]

    chat.bot.send_photo(
        chat.chat_id,
        product_image_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def format_cart_item_for_display(cart_item):
    name = cart_item['name']
    formatted_price = cart_item['meta']['display_price']['with_tax']
    unit_price = formatted_price['unit']['formatted']
    position_price = formatted_price['value']['formatted']
    quantity = cart_item['quantity']

    return (
        f'{name}\n'
        f'{unit_price} per kg\n'
        f'{quantity} kg in cart for {position_price}\n\n'
    )


def send_cart_interface_to_chat(cart, chat):
    bot_reply = ''.join(
        format_cart_item_for_display(cart_item) for cart_item in cart['data']
    )

    if not bot_reply:
        bot_reply = 'Your cart is empty'
    else:
        total_amount = cart['meta']['display_price']['with_tax']['formatted']
        bot_reply = f'Your cart:\n\n{bot_reply}Total: {total_amount}'

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
    chat = update.message

    auth_token = fetch_authorization_token(CLIENT_ID)['access_token']
    db.set(f'{chat.chat_id}_auth_token', auth_token)

    products = fetch_products(auth_token)
    send_products_interface_to_chat(products, chat)

    return 'HANDLE_MENU'


def handle_menu(update, db):
    if chat := update.message:
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)
        return 'HANDLE_MENU'

    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        product = fetch_product_by_id(auth_token, query)['data']
        send_product_details_interface_to_chat(product, chat, auth_token)

        return 'HANDLE_DESCRIPTION'


def handle_description(update, db):
    if chat := update.message:
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)
        return 'HANDLE_MENU'

    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products_interface_to_chat(products, chat)

        return 'HANDLE_MENU'
    elif query == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        product_id, quantity = query.split(';')
        cart = add_product_to_cart(
            auth_token,
            chat.chat_id,
            product_id,
            int(quantity),
        )

        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'


def handle_cart(update, db):
    if chat := update.message:
        chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)
        return 'HANDLE_MENU'

    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products_interface_to_chat(products, chat)

        return 'HANDLE_MENU'
    if query == 'Pay':
        chat.reply_text('Enter your email:')

        return 'WAITING_EMAIL'
    else:
        cart = remove_cart_item_by_id(
            auth_token,
            chat.chat_id,
            query,
        )
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'


def wait_email(update, db):
    query = update.message.text
    chat = update.message
    auth_token = db.get(f'{chat.chat_id}_auth_token').decode()

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    try:
        create_customer(token=auth_token, email=query)
    except InvalidEmail:
        bot_reply = f'Email {query} is incorrect.\nEnter your email:'
    except UserExistsError:
        bot_reply = f'User with email {query} exists already.'
    else:
        bot_reply = f'User with email {query} added to the DB.'

    chat.reply_text(bot_reply)

    return 'IDLE'


def idle(update, db):
    return None


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
        chat = update.message
    elif update.callback_query:
        request = update.callback_query.data
        chat = update.callback_query.message

    if request == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat.chat_id).decode("utf-8")

    state_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': wait_email,
        'IDLE': idle,
    }
    state_handler = state_functions[user_state]

    next_state = state_handler(update, db)

    db.set(chat.chat_id, next_state)


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
