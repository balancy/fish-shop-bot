import argparse
import json

import requests


def fetch_cart_items(token, cart_name):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_name}/items', headers=headers
    )
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get list of cart items')
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
    args = parser.parse_args()

    cart_items = fetch_cart_items(args.token, args.cart_name)
    print(json.dumps(cart_items, indent=2))
