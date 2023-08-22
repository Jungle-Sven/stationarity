from dydx3 import Client


def api(exchange):
    if exchange == 'dydx':
        public_client = Client(
        host='https://api.dydx.exchange',
        )
        return public_client

if __name__ == '__main__':
    pass