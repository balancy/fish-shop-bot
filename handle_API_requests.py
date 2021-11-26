import json

import requests
from requests.models import HTTPError


class UserExistsError(HTTPError):
    pass


def fetch_authorization_token(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }

    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data=data,
    )
    response.raise_for_status()

    return response.json()


def fetch_products(token):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        'https://api.moltin.com/v2/products',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_product_by_id(token, product_id):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_image_by_id(token, image_id):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def add_product_to_cart(token, cart_name, product_id, quantity):
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


def fetch_cart_items(token, cart_name):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_name}/items', headers=headers
    )
    response.raise_for_status()

    return response.json()


def remove_cart_item_by_id(token, cart_name, item_id):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_name}/items/{item_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def create_customer(token, email):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'type': 'customer',
            'name': 'name',
            'email': email,
            'password': 'password',
        }
    }

    response = requests.post(
        'https://api.moltin.com/v2/customers',
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 409:
        raise UserExistsError

    response.raise_for_status()

    return response.json()
