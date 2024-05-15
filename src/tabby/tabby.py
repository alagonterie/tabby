from http import HTTPStatus

from flask import Flask, request

from .logger import configure_logger
from .request_schemas import Webhook
from .tabby_start import start_tabby
from .webhook_processer import enqueue_webhook_for_processing

tabby = Flask(__name__)
configure_logger(tabby)


@tabby.route('/')
def home():
    return 'Hello, Tabby!', HTTPStatus.OK


@tabby.route('/webhooks/9bef1c1e-996f-41a6-9370-de0423d0746b', methods=['POST'])
def webhooks():
    webhook = Webhook.from_json(request.json)
    enqueue_webhook_for_processing(webhook)
    return '', HTTPStatus.OK


def main():
    start_tabby(tabby)


if __name__ == '__main__':
    main()
