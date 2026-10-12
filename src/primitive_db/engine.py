import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    format_columns,
    insert,
    list_tables,
    select,
    update,
    validate_clause,
)
from primitive_db.parser import parse_condition, parse_values
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

META_FILE = "db_meta.json"


def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def table_exists(metadata, table_name):
    """Проверяет, что таблица есть; если нет, печатает ошибку."""
    if table_name in metadata:
        return True
    print(f'Ошибка: Таблица "{table_name}" не существует.')
    return False


def print_table(metadata, table_name, rows):
    """Выводит записи таблицей через prettytable."""
    if not rows:
        print("Записи не найдены.")
        return
    columns = list(metadata[table_name])
    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row([row[column] for column in columns])
    print(table)


def split_from_where(user_input):
    """'select from users where age = 28' -> ('users', {'age': 28})."""
    parts = user_input.split(maxsplit=4)
    if len(parts) == 3 and parts[1] == "from":
        return parts[2], None
    if len(parts) == 5 and parts[1] == "from" and parts[3] == "where":
        return parts[2], parse_condition(parts[4])
    raise ValueError(user_input)


def handle_insert(metadata, user_input):
    """insert into <таблица> values (...)."""
    parts = user_input.split(maxsplit=4)
    if len(parts) != 5 or parts[1] != "into" or parts[3] != "values":
        raise ValueError(user_input)
    table_name = parts[2]
    table_data = insert(metadata, table_name, parse_values(parts[4]))
    if table_data is not None:
        save_table_data(table_name, table_data)


def handle_select(metadata, user_input):
    """select from <таблица> [where <столбец> = <значение>]."""
    table_name, where_clause = split_from_where(user_input)
    if not table_exists(metadata, table_name):
        return
    if where_clause is not None:
        validate_clause(metadata, table_name, where_clause)
    rows = select(load_table_data(table_name), where_clause)
    print_table(metadata, table_name, rows)


def handle_update(metadata, user_input):
    """update <таблица> set <столбец> = <значение> where <столбец> = <значение>."""
    parts = user_input.split(maxsplit=3)
    if len(parts) != 4 or parts[2] != "set":
        raise ValueError(user_input)
    table_name = parts[1]
    set_text, separator, where_text = parts[3].partition(" where ")
    if not separator:
        raise ValueError(user_input)
    set_clause = parse_condition(set_text)
    where_clause = parse_condition(where_text)
    if "ID" in set_clause:
        raise ValueError(set_text.strip())
    if not table_exists(metadata, table_name):
        return
    validate_clause(metadata, table_name, set_clause)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    found_ids = [record["ID"] for record in select(table_data, where_clause)]
    if not found_ids:
        print("Записи не найдены.")
        return
    save_table_data(table_name, update(table_data, set_clause, where_clause))
    for record_id in found_ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


def handle_delete(metadata, user_input):
    """delete from <таблица> where <столбец> = <значение>."""
    table_name, where_clause = split_from_where(user_input)
    if where_clause is None:
        raise ValueError(user_input)
    if not table_exists(metadata, table_name):
        return
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    found_ids = [record["ID"] for record in select(table_data, where_clause)]
    if not found_ids:
        print("Записи не найдены.")
        return
    save_table_data(table_name, delete(table_data, where_clause))
    for record_id in found_ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


def handle_info(metadata, args):
    """info <таблица>."""
    if len(args) != 2:
        raise ValueError(" ".join(args))
    table_name = args[1]
    if not table_exists(metadata, table_name):
        return
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {format_columns(metadata[table_name])}")
    print(f"Количество записей: {len(load_table_data(table_name))}")


def run():
    """Главный цикл программы: читает команды и вызывает функции из core."""
    print("***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)
        user_input = prompt.string(">>>Введите команду: ").strip()

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue

        command, *params = args
        try:
            match command:
                case "create_table" if len(params) >= 2:
                    result = create_table(metadata, params[0], params[1:])
                    if result is not None:
                        save_metadata(META_FILE, result)
                case "drop_table" if len(params) == 1:
                    result = drop_table(metadata, params[0])
                    if result is not None:
                        save_metadata(META_FILE, result)
                        delete_table_data(params[0])
                case "list_tables":
                    list_tables(metadata)
                case "insert":
                    handle_insert(metadata, user_input)
                case "select":
                    handle_select(metadata, user_input)
                case "update":
                    handle_update(metadata, user_input)
                case "delete":
                    handle_delete(metadata, user_input)
                case "info":
                    handle_info(metadata, args)
                case "help":
                    print_help()
                case "exit":
                    break
                case "create_table" | "drop_table":
                    raise ValueError(user_input)
                case _:
                    print(f"Функции {command} нет. Попробуйте снова.")
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        print()