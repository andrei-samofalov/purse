import time
from threading import Thread

from integration.client import SimpleClient
from integration.server import app
import logging

logging.basicConfig(level=logging.INFO)


def _send_req():
    time.sleep(1)
    client = SimpleClient(host='localhost', port=8000, use_ssl=False)
    while True:
        client.do_test_exception()


def main():
    Thread(target=_send_req, daemon=True).start()
    app.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == '__main__':
    main()
