import argparse
import json

import requests


def fetch_cart(token, cart_name):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_name}', headers=headers
    )
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get cart')
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

    cart = fetch_cart(args.token, args.cart_name)
    print(json.dumps(cart, indent=2))
