from environs import Env
from telegram.ext import Filters, Updater
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
)

from handle_API_requests import (
    add_product_to_cart,
    create_customer,
    fetch_authorization_token,
    fetch_cart_items,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
    InvalidEmail,
    UserExistsError,
)
from handle_interfaces import (
    send_cart_interface_to_chat,
    send_product_details_interface_to_chat,
    send_products_interface_to_chat,
)


def start(update, context):
    chat = update.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    client_id = context.bot_data['client_id']
    auth_token = fetch_authorization_token(client_id)['access_token']
    context.bot_data['auth_token'] = auth_token

    products = fetch_products(auth_token)
    send_products_interface_to_chat(products, chat)

    return 'HANDLE_MENU'


def handle_menu(update, context):
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, chat.chat_id)
        send_cart_interface_to_chat(cart, chat)

        return 'HANDLE_CART'
    else:
        product = fetch_product_by_id(auth_token, query)['data']
        send_product_details_interface_to_chat(product, chat, auth_token)

        return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

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


def handle_cart(update, context):
    query = update.callback_query.data
    chat = update.callback_query.message
    auth_token = context.bot_data['auth_token']

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


def wait_email(update, context):
    query = update.message.text
    chat = update.message
    auth_token = context.bot_data['auth_token']

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

    return ConversationHandler.END


def idle(update, db):
    print('idle')
    return None


if __name__ == '__main__':
    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    moltin_client_id = env.str('CLIENT_ID')

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher
    dp.bot_data['client_id'] = moltin_client_id

    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'HANDLE_MENU': [CallbackQueryHandler(handle_menu)],
            'HANDLE_DESCRIPTION': [CallbackQueryHandler(handle_description)],
            'HANDLE_CART': [CallbackQueryHandler(handle_cart)],
            'WAITING_EMAIL': [Filters.text, wait_email],
        },
        fallbacks=[CommandHandler('cancel', idle)],
    )

    dp.add_handler(handler)

    updater.start_polling()
    updater.idle()
