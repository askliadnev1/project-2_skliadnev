VALID_TYPES = {"int", "str", "bool"}


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
    columns_text = ", ".join(
        f"{name}:{column_type}" for name, column_type in table_columns.items()
    )
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