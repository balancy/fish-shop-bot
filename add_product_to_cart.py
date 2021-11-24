import argparse
import json

import requests


def add_product_to_cart(token, product_id, quantity, cart_name):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }

    response = requests.post(
        f'https://api.moltin.com/v2/carts/{cart_name}/items',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get cart")
    parser.add_argument(
        '-c',
        '--cart_name',
        type=str,
        help='cart name',
        default='main_cart',
    )
    parser.add_argument(
        '-t',
        '--token',
        type=str,
        help='bearer token',
    )
    parser.add_argument(
        '-p',
        '--product_id',
        type=str,
        help='product id',
    )
    parser.add_argument(
        '-q',
        '--quantity',
        type=int,
        help='quantity',
        default=1,
    )
    args = parser.parse_args()

    add_product_to_cart(
        args.token,
        args.product_id,
        args.quantity,
        args.cart_name,
    )
