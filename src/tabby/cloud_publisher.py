from logging import getLogger
from typing import cast

from tableauserverclient import PersonalAccessTokenAuth, Server

_logger = getLogger(__name__)

_auth: PersonalAccessTokenAuth | None = None
_server: Server | None = None


def start_cloud_publisher() -> None:
    from .args import args

    global _auth, _server
    _auth = PersonalAccessTokenAuth(
        token_name=args.tableau_token_name,
        personal_access_token=args.tableau_token_value,
        site_id=args.tableau_site_name
    )
    _server = Server(args.tableau_server_url, use_server_version=True)

    from threading import Thread
    thread_process = Thread(target=_cloud_publisher)
    thread_process.daemon = True
    thread_process.start()


def _cloud_publisher():
    from time import sleep

    from .args import args

    while True:
        _publish_all_data_sources()
        sleep(args.tableau_publish_frequency)


def _publish_all_data_sources():
    from pathlib import PurePath

    from tableauserverclient import Pager, DatasourceItem, ProjectItem

    from .args import args
    from .hyper import close_connection, init_connection

    global _server, _auth
    with _server.auth.sign_in(_auth):
        project_id: str | None = None
        for project in Pager(_server.projects):
            if project.name == args.tableau_project_name:
                project_id = project.id

        if project_id is None:
            project = ProjectItem(args.tableau_project_name)
            project_id = cast(ProjectItem, _server.projects.create(project)).id

        # TODO: Publish each data source in parallel if possible.
        publish_mode = Server.PublishMode.Overwrite
        for entity_data_source in args.rally_entities:
            close_connection(entity_data_source)
            try:
                datasource = DatasourceItem(project_id)
                file = PurePath(args.tableau_datasource_dir, f'{entity_data_source}.hyper')
                _server.datasources.publish(datasource, str(file), publish_mode, as_job=True)
            except Exception as ex:
                _logger.error(str(ex))
            finally:
                init_connection(entity_data_source)
