from typing import cast, Any

from pyral import Rally, RallyRESTResponse

_rally: Rally | None = None


def start_rally() -> None:
    from .args import args

    global _rally
    _rally = Rally(apikey=args.rally_apikey)
    _rally.enableLogging('rally.log')


def get(entity: str) -> list[dict[str, Any]]:
    from datetime import datetime
    from sys import stdout
    from logging import getLogger

    from .args import args

    rally_entities = cast(
        RallyRESTResponse,
        _rally.get(
            entity,
            fetch=True,
            projectScopeUp=True,
            projectScopeDown=True,
            pagesize=args.rally_get_pagesize,
            limit=args.rally_get_limit
        )
    )

    total = min(args.rally_get_limit, rally_entities.resultCount)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gray_timestamp = f'\033[37m{timestamp}\033[0m'
    green_info = f'\033[32mINFO\033[0m'

    entity_dicts: list[dict[str, Any]] = []
    try:
        for i, entity_object in enumerate(rally_entities):
            entity_dicts.append(entity_object.__dict__)

            if i % 5 == 0 or i >= total - 1:
                percentage = (len(entity_dicts) / total) * 100
                print(f'\r{gray_timestamp} {green_info}     Loading {total} {entity} records ({percentage:05.2f}%)', end='')
                stdout.flush()
    except Exception as ex:
        getLogger(__name__).error(str(ex))

    print()
    return entity_dicts
