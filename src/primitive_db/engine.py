import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE
from primitive_db.core import (
    check_table_exists,
    create_table,
    delete,
    drop_table,
    format_columns,
    insert,
    list_tables,
    matches,
    select,
    update,
    validate_clause,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_condition, parse_values
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


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


def find_ids(table_data, where_clause):
    """ID записей, подходящих под условие."""
    return [record["ID"] for record in table_data if matches(record, where_clause)]


def split_from_where(user_input):
    """'select from users where age = 28' -> ('users', {'age': 28})."""
    parts = user_input.split(maxsplit=4)
    if len(parts) == 3 and parts[1] == "from":
        return parts[2], None
    if len(parts) == 5 and parts[1] == "from" and parts[3] == "where":
        return parts[2], parse_condition(parts[4])
    raise ValueError(user_input)


@handle_db_errors
def split_command(user_input):
    """Разбивает введённую строку на слова с учётом кавычек."""
    return shlex.split(user_input)


@handle_db_errors
def handle_create_table(metadata, args):
    """create_table <таблица> <столбец:тип> ..."""
    if len(args) < 3:
        raise ValueError(" ".join(args))
    result = create_table(metadata, args[1], args[2:])
    if result is not None:
        save_metadata(META_FILE, result)


@handle_db_errors
def handle_drop_table(metadata, args):
    """drop_table <таблица>."""
    if len(args) != 2:
        raise ValueError(" ".join(args))
    table_name = args[1]
    check_table_exists(metadata, table_name)
    result = drop_table(metadata, table_name)
    if result is not None:
        save_metadata(META_FILE, result)
        delete_table_data(table_name)


@handle_db_errors
def handle_insert(metadata, user_input):
    """insert into <таблица> values (...)."""
    parts = user_input.split(maxsplit=4)
    if len(parts) != 5 or parts[1] != "into" or parts[3] != "values":
        raise ValueError(user_input)
    table_name = parts[2]
    table_data = insert(metadata, table_name, parse_values(parts[4]))
    if table_data is not None:
        save_table_data(table_name, table_data)


@handle_db_errors
def handle_select(metadata, user_input):
    """select from <таблица> [where <столбец> = <значение>]."""
    table_name, where_clause = split_from_where(user_input)
    check_table_exists(metadata, table_name)
    if where_clause is not None:
        validate_clause(metadata, table_name, where_clause)
    rows = select(load_table_data(table_name), where_clause)
    print_table(metadata, table_name, rows)


@handle_db_errors
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
    check_table_exists(metadata, table_name)
    validate_clause(metadata, table_name, set_clause)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    found_ids = find_ids(table_data, where_clause)
    if not found_ids:
        print("Записи не найдены.")
        return
    new_data = update(table_data, set_clause, where_clause)
    if new_data is None:
        return
    save_table_data(table_name, new_data)
    for record_id in found_ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


@handle_db_errors
def handle_delete(metadata, user_input):
    """delete from <таблица> where <столбец> = <значение>."""
    table_name, where_clause = split_from_where(user_input)
    if where_clause is None:
        raise ValueError(user_input)
    check_table_exists(metadata, table_name)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    found_ids = find_ids(table_data, where_clause)
    if not found_ids:
        print("Записи не найдены.")
        return
    new_data = delete(table_data, where_clause)
    if new_data is None:
        return
    save_table_data(table_name, new_data)
    for record_id in found_ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


@handle_db_errors
def handle_info(metadata, args):
    """info <таблица>."""
    if len(args) != 2:
        raise ValueError(" ".join(args))
    table_name = args[1]
    check_table_exists(metadata, table_name)
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {format_columns(metadata[table_name])}")
    print(f"Количество записей: {len(load_table_data(table_name))}")


def run():
    """Главный цикл программы: читает команды и вызывает обработчики."""
    print("***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)
        user_input = prompt.string(">>>Введите команду: ").strip()
        args = split_command(user_input)
        if not args:
            continue

        match args[0]:
            case "create_table":
                handle_create_table(metadata, args)
            case "drop_table":
                handle_drop_table(metadata, args)
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
            case _:
                print(f"Функции {args[0]} нет. Попробуйте снова.")
        print()