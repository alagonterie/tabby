from flask import Flask


def configure_logger(app: Flask) -> None:
    from sys import stdout
    from logging import StreamHandler, getLogger, INFO, Formatter
    from logging.handlers import TimedRotatingFileHandler

    from colorlog import ColoredFormatter

    custom_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }

    console_format = "%(white)s%(asctime)s%(log_color)s %(levelname)-8s%(reset)s %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console_formatter = ColoredFormatter(console_format, datefmt=date_format, reset=True, log_colors=custom_colors)
    handler = StreamHandler(stdout)
    handler.setFormatter(console_formatter)
    root = getLogger()

    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    root.addHandler(handler)

    log_level = INFO
    root.setLevel(log_level)
    app.logger.setLevel(log_level)

    file_handler = TimedRotatingFileHandler('./tabby.log', when='midnight', interval=1, backupCount=7)
    file_formatter = Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s', datefmt=date_format)
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)
