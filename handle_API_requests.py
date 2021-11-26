import json

import requests
from requests.models import HTTPError


class UserExistsError(HTTPError):
    pass


def fetch_authorization_token(client_id):
    """Make an API request to fetch bearer token

    Args:
        client_id: elasticpath client id

    Returns:
        API response containing authorization token
    """
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
    """Make an API request to fetch all products in catalog

    Args:
        token: authorization token

    Returns:
        API response containing products
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        'https://api.moltin.com/v2/products',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_product_by_id(token, product_id):
    """Make an API request to fetch product details

    Args:
        token: authorization token
        product_id: id of product to fetch details of

    Returns:
        API response containing product details
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_image_by_id(token, image_id):
    """Make an API request to fetch image

    Args:
        token: authorization token
        image_id: id of image to fetch

    Returns:
        API response containing image url
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def add_product_to_cart(token, cart_name, product_id, quantity):
    """Make an API request to add product to cart

    Args:
        token: authorization token
        cart_name: name of cart to add product to
        product_id: id of product to add to cart
        quantity: quantity of product to add to cart

    Returns:
        API response containing all cart items
    """
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
    """Make an API request to fetch all cart items

    Args:
        token: authorization token
        cart_name: name of cart to fetch items from

    Returns:
        API response containing all cart items
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_name}/items', headers=headers
    )
    response.raise_for_status()

    return response.json()


def remove_cart_item_by_id(token, cart_name, item_id):
    """Make an API request to remove item from cart

    Args:
        token: authorization token
        cart_name: name of cart to remove item from
        item_id: id of item to remove from cart

    Returns:
        API response containing all cart items
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_name}/items/{item_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def create_customer(token, email):
    """Make an API request to create customer

    Args:
        token: authorization token
        email: customer email to use during creating

    Returns:
        API response containing customer details
    """
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
