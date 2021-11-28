import logging

from environs import Env
from telegram.bot import Bot
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    Updater,
)

from handle_API_requests import (
    add_product_to_cart,
    create_customer,
    fetch_authorization_token,
    fetch_cart_items,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
    UserExistsError,
)
from handle_interfaces import (
    send_cart,
    send_product_details,
    send_products,
)
from logs_handler import TelegramLogsHandler

logger = logging.getLogger(__file__)


def start(update, context):
    """Start handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    chat = update.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    client_id = context.bot_data['client_id']
    auth_token = fetch_authorization_token(client_id)['access_token']
    context.bot_data['auth_token'] = auth_token

    products = fetch_products(auth_token)
    send_products(products, chat)

    return 'HANDLE_MENU'


def handle_menu(update, context):
    """Products menu handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart(cart, chat)

        return 'HANDLE_CART'

    product = fetch_product_by_id(auth_token, query)['data']
    send_product_details(product, chat, auth_token)

    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    """Product description handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return 'HANDLE_MENU'

    elif query == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart(cart, chat)

        return 'HANDLE_CART'

    product_id, quantity = query.split(';')
    cart = add_product_to_cart(
        auth_token,
        chat.chat_id,
        product_id,
        int(quantity),
    )

    send_cart(cart, chat)

    return 'HANDLE_CART'


def handle_cart(update, context):
    """User cart handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return 'HANDLE_MENU'
    if query == 'Pay':
        chat.reply_text('Enter your email:')

        return 'WAITING_EMAIL'

    cart = remove_cart_item_by_id(
        auth_token,
        chat.chat_id,
        query,
    )
    send_cart(cart, chat)

    return 'HANDLE_CART'


def wait_email(update, context):
    """Waiting user email input handler

    Args:
        update and context: standard bot handler args

    Returns:
        end of conversation state
    """
    query = update.message.text
    auth_token = context.bot_data['auth_token']

    try:
        create_customer(token=auth_token, email=query)
    except UserExistsError:
        bot_reply = f'User with email {query} exists already.'
    else:
        bot_reply = f'User with email {query} added to the system.'

    update.message.reply_text(bot_reply)

    return ConversationHandler.END


def handle_incorrect_email(update, context):
    """Demands user to reenter his email.

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    bot_reply = 'Reenter your email. It seems that it\'s incorrect:'
    update.message.reply_text(bot_reply)

    return 'WAITING_EMAIL'


def exit(update, context):
    """User fallback handler

    Args:
        update and context: standard bot handler args

    Returns:
        end of conversation state
    """
    update.message.reply_text('User exited the conversation')

    return ConversationHandler.END


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    bot_token = env.str('TG_BOT_TOKEN')
    moltin_client_id = env.str('CLIENT_ID')

    persistence = PicklePersistence(filename='conversationbot')
    updater = Updater(bot_token, use_context=True, persistence=persistence)
    dp = updater.dispatcher
    dp.bot_data['client_id'] = moltin_client_id

    logs_bot = Bot(token=env.str('LOGS_BOT_TOKEN'))
    logger.addHandler(
        TelegramLogsHandler(logs_bot, env.str('TG_USER_CHAT_ID'))
    )

    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'HANDLE_MENU': [CallbackQueryHandler(handle_menu)],
            'HANDLE_DESCRIPTION': [CallbackQueryHandler(handle_description)],
            'HANDLE_CART': [CallbackQueryHandler(handle_cart)],
            'WAITING_EMAIL': [
                MessageHandler(Filters.regex('^\w+@\w+\.\w+$'), wait_email),
                MessageHandler(Filters.text, handle_incorrect_email),
            ],
        },
        fallbacks=[CommandHandler('exit', exit)],
        persistent=True,
        name='conversation_handler',
    )

    dp.add_handler(handler)

    updater.start_polling()
    updater.idle()
