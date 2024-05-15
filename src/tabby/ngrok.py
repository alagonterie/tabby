def start_ngrok() -> None:
    from logging import getLogger, ERROR

    from pyngrok.ngrok import set_auth_token, connect

    from .args import args

    pyngrok_logger = getLogger('pyngrok')
    pyngrok_logger.setLevel(ERROR)

    set_auth_token(args.ngrok_auth_token)

    tunnel = connect(addr=args.port, proto='http', name='tabby', hostname=args.ngrok_domain)
    getLogger(__name__).info(tunnel)
