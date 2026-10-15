from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data

VALID_TYPES = {"int": int, "str": str, "bool": bool}

select_cache = create_cacher()


def format_columns(columns):
    """{'ID': 'int', 'name': 'str'} -> 'ID:int, name:str'."""
    return ", ".join(f"{name}:{col_type}" for name, col_type in columns.items())


def check_table_exists(metadata, table_name):
    """Выбрасывает KeyError, если таблицы нет."""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}"')


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу. Возвращает обновлённые метаданные или None при ошибке."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    table_columns = {"ID": "int"}
    for column in columns:
        name, separator, column_type = column.partition(":")
        if not separator or not name or column_type not in VALID_TYPES:
            raise ValueError(column)
        if name == "ID" and column_type == "int":
            continue
        if name in table_columns:
            raise ValueError(column)
        table_columns[name] = column_type

    metadata[table_name] = table_columns
    columns_text = format_columns(table_columns)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу. Возвращает обновлённые метаданные или None при ошибке."""
    check_table_exists(metadata, table_name)
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Печатает список всех таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")


def validate_clause(metadata, table_name, clause):
    """Проверяет, что столбцы условия существуют и значения нужного типа."""
    columns = metadata[table_name]
    for column, value in clause.items():
        if column not in columns:
            raise KeyError(f'Столбец "{column}"')
        if type(value) is not VALID_TYPES[columns[column]]:
            raise ValueError(f"{column} = {value}")


def matches(record, where_clause):
    """Подходит ли запись под условие where."""
    return all(record.get(column) == value for column, value in where_clause.items())


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись. Возвращает обновлённые данные таблицы или None."""
    check_table_exists(metadata, table_name)
    columns = metadata[table_name]
    data_columns = [name for name in columns if name != "ID"]
    if len(values) != len(data_columns):
        raise ValueError(
            f"ожидается {len(data_columns)} значений, получено {len(values)}"
        )

    record = {}
    for name, value in zip(data_columns, values):
        if type(value) is not VALID_TYPES[columns[name]]:
            raise ValueError(value)
        record[name] = value

    table_data = load_table_data(table_name)
    new_id = max((row["ID"] for row in table_data), default=0) + 1
    table_data.append({"ID": new_id, **record})
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def filter_records(table_data, where_clause):
    """Все записи или только подходящие под условие."""
    if where_clause is None:
        return table_data
    return [record for record in table_data if matches(record, where_clause)]


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает записи по условию; одинаковые запросы берутся из кэша."""
    key = repr((table_data, where_clause))
    return select_cache(key, lambda: filter_records(table_data, where_clause))


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля в записях, подходящих под условие."""
    for record in table_data:
        if matches(record, where_clause):
            record.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удаляет записи, подходящие под условие."""
    return [record for record in table_data if not matches(record, where_clause)]