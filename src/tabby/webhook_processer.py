from logging import getLogger
from queue import PriorityQueue
from time import time

from .request_schemas import Webhook

_logger = getLogger(__name__)

_priority_queue: PriorityQueue[tuple[int, float, Webhook]] = PriorityQueue()


def start_webhook_processor() -> None:
    from threading import Thread

    thread_process = Thread(target=_webhook_processor)
    thread_process.daemon = True
    thread_process.start()


def enqueue_webhook_for_processing(webhook: Webhook) -> None:
    _priority_queue.put((webhook.message.transaction.timestamp, time(), webhook))


def _webhook_processor():
    from .args import args
    from .hyper import is_open, process_changes

    # Buffer to account for potential latency from Rally service.
    # We want to process webhooks in the order that they were created by Rally users.
    # So, we use a priority queue sorted by the user creation timestamp.
    # However, latency could cause the early webhooks to arrive here late.
    # We add a buffer to allow any late arriving webhooks to queue into the correct order.
    # Rally documented a potential latency of 2 seconds, so we're defaulting with that.
    while True:
        timestamp, queued_time, webhook = _priority_queue.get()

        # If the webhook has not been in queue for rally_webhook_buffer seconds, put it back.
        if time() - queued_time < args.rally_webhook_buffer or not is_open(webhook.message.object_type):
            _priority_queue.put((timestamp, queued_time, webhook))
            continue

        try:
            process_changes(webhook)
        except Exception as ex:
            _logger.error(str(ex))

        _priority_queue.task_done()
