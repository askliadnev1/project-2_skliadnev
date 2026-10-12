from primitive_db.utils import load_table_data

VALID_TYPES = {"int": int, "str": str, "bool": bool}


def format_columns(columns):
    """{'ID': 'int', 'name': 'str'} -> 'ID:int, name:str'."""
    return ", ".join(f"{name}:{col_type}" for name, col_type in columns.items())


def create_table(metadata, table_name, columns):
    """Создаёт таблицу. Возвращает обновлённые метаданные или None при ошибке."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    table_columns = {"ID": "int"}
    for column in columns:
        name, separator, column_type = column.partition(":")
        if not separator or not name or column_type not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return None
        if name == "ID" and column_type == "int":
            continue
        if name in table_columns:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return None
        table_columns[name] = column_type

    metadata[table_name] = table_columns
    columns_text = format_columns(table_columns)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу. Возвращает обновлённые метаданные или None при ошибке."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

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
        if column not in columns or type(value) is not VALID_TYPES[columns[column]]:
            raise ValueError(f"{column} = {value}")


def matches(record, where_clause):
    """Подходит ли запись под условие where."""
    return all(record.get(column) == value for column, value in where_clause.items())


def insert(metadata, table_name, values):
    """Добавляет запись. Возвращает обновлённые данные таблицы или None."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    columns = metadata[table_name]
    data_columns = [name for name in columns if name != "ID"]
    if len(values) != len(data_columns):
        print(
            f"Некорректное значение: ожидается {len(data_columns)} "
            f"значений, получено {len(values)}. Попробуйте снова."
        )
        return None

    record = {}
    for name, value in zip(data_columns, values):
        if type(value) is not VALID_TYPES[columns[name]]:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return None
        record[name] = value

    table_data = load_table_data(table_name)
    new_id = max((row["ID"] for row in table_data), default=0) + 1
    table_data.append({"ID": new_id, **record})
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def select(table_data, where_clause=None):
    """Все записи или только подходящие под условие."""
    if where_clause is None:
        return table_data
    return [record for record in table_data if matches(record, where_clause)]


def update(table_data, set_clause, where_clause):
    """Обновляет поля в записях, подходящих под условие."""
    for record in table_data:
        if matches(record, where_clause):
            record.update(set_clause)
    return table_data


def delete(table_data, where_clause):
    """Удаляет записи, подходящие под условие."""
    return [record for record in table_data if not matches(record, where_clause)]