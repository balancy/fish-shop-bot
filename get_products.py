import argparse

import requests


def fetch_products(token):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        'https://api.moltin.com/v2/products', headers=headers
    )
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Get list of products using given Bearer token"
    )
    parser.add_argument(
        "-t",
        "--token",
        type=str,
        help="bearer token",
    )
    args = parser.parse_args()

    products = fetch_products(args.token)
    print(products)
