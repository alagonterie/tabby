from flask import Flask


def start_tabby(tabby: Flask) -> None:
    from .rally import start_rally
    from .hyper import start_hyper
    from .cloud_publisher import start_cloud_publisher
    from .args import args
    from .webhook_processer import start_webhook_processor
    from .ngrok import start_ngrok

    start_rally()
    start_hyper()

    if args.tableau_publish:
        start_cloud_publisher()

    if not args.run_as_script:
        # TODO: Refresh rally webhook on start with args.rally_entities

        start_webhook_processor()
        start_ngrok()

        tabby.run(port=args.port)
