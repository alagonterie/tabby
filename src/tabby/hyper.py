import atexit
from logging import getLogger
from typing import Any, Iterable

from tableauhyperapi import HyperProcess, Connection, TableDefinition, SqlType

from .args import args
from .request_schemas import Webhook, Change

_logger = getLogger(__name__)

_hyper_process: HyperProcess | None = None
dbs: dict[str, Connection] | None = None

entity_column_defs: dict[str, dict[str, SqlType]] = {}


def start_hyper() -> None:
    _init_all_connections()

    if args.rally_refresh_on_start:
        _create_tables_with_rally_data()


def is_open(data_source: str) -> bool:
    global dbs
    return (
        dbs is not None and
        data_source in dbs and
        dbs[data_source].is_open
    )


def init_connection(data_source: str) -> None:
    from os import makedirs
    from pathlib import PurePath

    from tableauhyperapi import CreateMode, Telemetry

    global _hyper_process, dbs
    if not _hyper_process or not _hyper_process.is_open:
        _hyper_process = HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU)

    if not dbs:
        dbs = {}

    if data_source not in dbs or not dbs[data_source].is_open:
        makedirs(args.tableau_datasource_dir, exist_ok=True)

        dbs[data_source] = Connection(
            endpoint=_hyper_process.endpoint,
            database=PurePath(args.tableau_datasource_dir, f'{data_source}.hyper'),
            create_mode=CreateMode.CREATE_AND_REPLACE
        )


def close_connection(data_source: str):
    global _hyper_process, dbs
    if _hyper_process is not None and _hyper_process.is_open:
        _hyper_process.close()
    if dbs is not None and data_source in dbs:
        dbs[data_source].close()


def _init_all_connections():
    for entity in args.rally_entities:
        init_connection(entity)


def _close_all_connections():
    for entity in args.rally_entities:
        close_connection(entity)


atexit.register(_close_all_connections)


def process_changes(webhook: Webhook) -> None:
    entity_type = webhook.message.object_type
    entity_id = webhook.message.object_id
    action = webhook.message.action

    global entity_column_defs
    attrs = entity_column_defs.get(entity_type, {})

    state = []
    changes = []
    if action == 'Created':
        row_dict = {attr.name: attr.value for attr in webhook.message.state.values()}
        row_data = [kv for kv in sorted(
            [(k, row_dict.get(k)) for k in attrs.keys()],
            key=lambda kv: _sanitize_column_name(kv[0])
        )]

        state = _process_row_values(entity_type, row_data)
    elif action == 'Updated':
        changes = [change for change in webhook.message.changes.values() if not any(attrs) or change.name in attrs]

    row_count = _process_changes(entity_type, entity_id, action, changes, state)

    change_names = ', '.join([change.display_name for change in changes])
    update_description = f' with {len(changes)} change(s) [{change_names}]' if action == 'Updated' else ''
    user = webhook.message.transaction.user.email.split('@')[0]
    suffix = ' (Failed)' if row_count == 0 else ''

    message = f'{entity_type} {entity_id} {action.lower()}{update_description} by {user}{suffix}'
    if row_count == 'ignored':
        pass
    elif row_count > 0:
        _logger.info(message)
    else:
        _logger.warning(message)


def _process_changes(
    entity_type: str,
    entity_id: str,
    action: str,
    changes: list[Change],
    state: list[Any]
) -> int | str:
    from tableauhyperapi import Inserter, escape_string_literal

    db = dbs[entity_type]
    table_def = db.catalog.get_table_definition(entity_type)

    row_count = 0
    if action == 'Created':
        num_entities = db.execute_scalar_query(
            query=f'SELECT COUNT(1) '
                  f'FROM {table_def.table_name} '
                  f'WHERE {table_def.get_column_by_name('ObjectUUID').name} = {escape_string_literal(entity_id)}'
        )

        is_already_deleted = num_entities > 0
        if is_already_deleted:
            return 'ignored'

        with Inserter(db, table_def) as inserter:
            inserter.add_row(state)
            inserter.execute()
            row_count = 1

    elif action == 'Updated':
        column_assignments = []
        for change in changes:
            column_name_str = _sanitize_column_name(change.name)

            column = table_def.get_column_by_name(column_name_str)
            if column is None:
                _logger.warning(f'Ignoring change to column {column_name_str}')
                continue

            column_name = column.name
            if change.value is None and change.old_value is None:
                added = len(change.added) if change.added is not None else 0
                removed = len(change.removed) if change.removed is not None else 0
                net_change = added - removed
                operator = '+' if net_change >= 0 else '-'

                if net_change != 0:
                    column_assignments.append(f'{column_name} = {column_name} {operator} {abs(net_change)}')
            else:
                value = _process_change_value(change.value, change.type)
                column_assignments.append(f'{column_name} = {value}')

        if any(column_assignments):
            row_count = db.execute_command(
                command=f'UPDATE {table_def.table_name} '
                        f'SET {', '.join(column_assignments)} '
                        f'WHERE {table_def.get_column_by_name('ObjectUUID').name} = {escape_string_literal(entity_id)}'
            )

    elif action == 'Recycled':
        num_entities = db.execute_scalar_query(
            query=f'SELECT COUNT(1) '
                  f'FROM {table_def.table_name} '
                  f'WHERE {table_def.get_column_by_name('ObjectUUID').name} = {escape_string_literal(entity_id)}'
        )

        is_already_deleted = num_entities == 0
        if is_already_deleted:
            return 'ignored'

        row_count = db.execute_command(
            command=f'DELETE FROM {table_def.table_name} '
                    f'WHERE {table_def.get_column_by_name('ObjectUUID').name} = {escape_string_literal(entity_id)}'
        )

    return row_count


def _process_change_value(value: Any | None, change_type: str) -> Any:
    from tableauhyperapi import escape_string_literal

    if value is None:
        value = 'NULL'
    elif isinstance(value, str):
        value = escape_string_literal(value)
    elif isinstance(value, dict):
        value = value.get('value')
        value = _process_change_value(value, change_type)
    elif isinstance(value, (int, float)):
        pass
    else:
        _logger.warning(f'Unexpected column type used during update: {change_type}/{type(value)}')

    return value


def _create_tables_with_rally_data() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import as_completed

    from tableauhyperapi import Inserter

    with ThreadPoolExecutor(max_workers=1 if args.rally_get_limit > 100 else None) as executor:
        future_to_entities = {executor.submit(_get_all_entities, entity): entity for entity in args.rally_entities}

    rally_entities_dict: dict[str, list[dict[str, Any]]] = {}
    for future in as_completed(future_to_entities):
        entity_name, entities = future.result()
        rally_entities_dict[entity_name] = entities

    # Build dynamic table defs and all rows to be inserted.
    # If a column value is null for all records, exclude from def.

    # First pass. Get all columns that will hold at least one non-None value for at least one row.
    with ThreadPoolExecutor() as executor:
        future_to_entity = {executor.submit(_process_entity, entity_name, entities):
                            entity_name for entity_name, entities in rally_entities_dict.items()}

    global entity_column_defs
    for future in as_completed(future_to_entity):
        entity_name, entity_columns = future.result()
        entity_column_defs[entity_name] = entity_columns

    # Build table defs and column/attribute sets from entity_column_defs.
    with ThreadPoolExecutor() as executor:
        future_to_table_def = {executor.submit(_create_table_def, entity_name, entity_columns):
                               entity_name for entity_name, entity_columns in entity_column_defs.items()}

    table_defs: list[TableDefinition] = []
    for future in as_completed(future_to_table_def):
        table_defs.append(future.result())

    # Create tables with table defs.
    with ThreadPoolExecutor() as executor:
        executor.map(_create_table, table_defs)

    # Second pass. Build rows to be inserted.
    def process_rally_entities(entity_key: str, rally_entities: list[dict[str, Any]]) -> (str, list[list[Any]]):
        entity_data: list[list[Any]] = []
        for row_dict in rally_entities:
            row_data = [kv for kv in sorted(
                [(k, row_dict.get(k)) for k in entity_column_defs[entity_key]],
                key=lambda kv: _sanitize_column_name(kv[0])
            )]

            row_values = _process_row_values(entity_key, row_data)
            entity_data.append(row_values)

        return entity_key, entity_data

    with ThreadPoolExecutor() as executor:
        future_to_entity_rows = {executor.submit(process_rally_entities, entity_name, rally_entities):
                                 entity_name for entity_name, rally_entities in rally_entities_dict.items()}

    table_rows_to_add: dict[str, list[list[Any]]] = {}
    for future in as_completed(future_to_entity_rows):
        entity_name, rows_to_add = future.result()
        table_rows_to_add[entity_name] = rows_to_add

    # Insert rows into tables.
    def insert_rows_to_table(table_def):
        table_name = table_def.table_name.name.unescaped
        with Inserter(dbs[table_name], table_def) as inserter:
            inserter.add_rows(table_rows_to_add.get(table_name))
            inserter.execute()

        num_entities = dbs[table_name].execute_scalar_query(query=f'SELECT COUNT(1) from {table_def.table_name}')
        _logger.info(f'Inserted {num_entities} {table_name} record(s) into hyper database')

    with ThreadPoolExecutor() as executor:
        future_to_table_def = {executor.submit(insert_rows_to_table, table_def): table_def for table_def in table_defs}

    for future in as_completed(future_to_table_def):
        future.result()


def _get_all_entities(entity_name: str) -> tuple[str, list[dict[str, Any]]]:
    from .rally import get

    _logger.info(f'Getting {entity_name} entities from Rally...')
    return entity_name, get(entity_name)


def _process_entity(entity_name, rally_entities):
    from datetime import datetime

    from pyral.entity import Persistable
    from tableauhyperapi import SqlType

    entity_columns = {}
    for row_dict in rally_entities:
        if not row_dict or not any(row_dict):
            continue

        for column_name, column_value in row_dict.items():
            if column_value is None or str(column_name) == 'oid' or str(column_name).startswith('_'):
                continue

            is_timestamp = True
            try:
                datetime.strptime(str(column_value), '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                is_timestamp = False

            sql_type = None

            if is_timestamp:
                sql_type = SqlType.timestamp()
            elif isinstance(column_value, bool):
                sql_type = SqlType.bool()
            elif isinstance(column_value, int):
                sql_type = SqlType.big_int()
            elif isinstance(column_value, float):
                sql_type = SqlType.double()
            elif isinstance(column_value, list):
                sql_type = SqlType.small_int()
            elif isinstance(column_value, (str, Persistable)):
                sql_type = SqlType.text()

            if sql_type is None:
                continue

            entity_columns[column_name] = sql_type

    return entity_name, entity_columns


def _create_table_def(entity_name: str, entity_columns: dict[str, SqlType]) -> TableDefinition:
    from tableauhyperapi import Nullability

    table_def = TableDefinition(entity_name)
    for column_name in sorted(entity_columns.keys(), key=_sanitize_column_name):
        column_type = entity_columns[column_name]
        column_name = _sanitize_column_name(column_name)

        nullability = Nullability.NOT_NULLABLE if column_name == 'ObjectID' else Nullability.NULLABLE
        table_def.add_column(column_name, column_type, nullability)

    return table_def


def _create_table(table_def: TableDefinition):
    global dbs

    dbs[table_def.table_name.name.unescaped].catalog.create_table(table_def)
    _logger.info(f'Created the {table_def.table_name} table with {len(table_def.columns)} column(s)')


def _process_row_values(table_name: str, row_data: Iterable[tuple[str, Any | None]]) -> list[Any] | None:
    from datetime import datetime
    from pyral.entity import Persistable

    if not row_data or not any(row_data):
        return None

    row: list[Any] = []
    for column_name, column_value in row_data:

        if isinstance(column_value, dict):
            if 'name' in column_value:
                column_value = column_value['name']
            elif 'value' in column_value:
                column_value = column_value['value']

        if column_value is None or str(column_value) in ['', 'None'] or str(column_value).isspace():
            row.append(None)
            continue

        try:
            value = datetime.strptime(str(column_value), '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            value = column_value

        global entity_column_defs
        if isinstance(column_value, (int, float, bool)) and \
           entity_column_defs[table_name][column_name] == SqlType.text():
            value = str(column_value)
        elif isinstance(column_value, list):
            value = len(column_value)
        elif isinstance(column_value, Persistable):
            value = column_value.Name

        row.append(value)

    return row


def _sanitize_column_name(column_name: str) -> str:
    return str(column_name).replace('c_', '') \
        if str(column_name).startswith('c_') \
        else column_name
