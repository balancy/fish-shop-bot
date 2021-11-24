import requests


def fetch_authorization_token(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }

    response = requests.post(
        'https://api.moltin.com/oauth/access_token', data=data
    )
    response.raise_for_status()

    return response.json()['access_token']


def fetch_products(token):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        'https://api.moltin.com/v2/products', headers=headers
    )
    response.raise_for_status()

    return response.json()


def fetch_product_by_id(token, product_id):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}', headers=headers
    )
    response.raise_for_status()

    return response.json()
