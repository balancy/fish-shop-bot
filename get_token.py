from environs import Env
import requests


def get_authorization_details(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }

    response = requests.post(
        'https://api.moltin.com/oauth/access_token', data=data
    )
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    API_URL = env.str('API_URL')
    STORE_ID = env.str('STORE_ID')
    STORE_UUID = env.str('STORE_UUID')
    CLIENT_ID = env.str('CLIENT_ID')
    CLIENT_SECRET = env.str('CLIENT_SECRET')

    token = get_authorization_details(CLIENT_ID)['access_token']
    print(token)
