import json
import os

DATA_DIR = "data"


def load_metadata(filepath):
    """Загружает метаданные из JSON-файла. Если файла нет, возвращает {}."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def table_path(table_name):
    """Путь к файлу с данными таблицы: data/<имя_таблицы>.json."""
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загружает записи таблицы. Если файла нет, возвращает пустой список."""
    try:
        with open(table_path(table_name), encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет записи таблицы, при необходимости создаёт папку data."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(table_path(table_name), "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def delete_table_data(table_name):
    """Удаляет файл с данными таблицы, если он есть."""
    try:
        os.remove(table_path(table_name))
    except FileNotFoundError:
        pass