from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handle_API_requests import fetch_image_by_id


def send_products(products, chat):
    """Send products list with keyboard to the chat.

    Args:
        products: products dictionary
        chat: telegram chat instance to send products to
    """
    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products['data']
    ]
    keyboard.append([InlineKeyboardButton('Cart', callback_data='Cart')])

    chat.reply_text('Catalog', reply_markup=InlineKeyboardMarkup(keyboard))


def send_product_details(product, chat, auth_token):
    """Send product details with keyboard to the chat.

    Args:
        product: product details dictionary
        chat: telegram chat instance to send product details to
        auth_token: bearer token to request a product image
    """
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
    """Transfrom cart item dicionary to formatted string

    Args:
        cart_item: cart item dicionary

    Returns:
        formatted string
    """
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


def send_cart(cart, chat):
    """Send cart items list with keyboard to chat

    Args:
        cart: cart items dictionary
        chat: telegram chat instance to send cart items to
    """
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
