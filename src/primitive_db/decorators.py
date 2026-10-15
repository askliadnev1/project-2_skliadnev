import time
from functools import wraps


def handle_db_errors(func):
    """Перехватывает ошибки работы с БД и печатает понятное сообщение."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: {error.args[0]} не существует.")
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")

    return wrapper


def confirm_action(action_name):
    """Фабрика декораторов: спрашивает подтверждение перед опасной операцией."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            question = f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            answer = input(question)
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Замеряет время выполнения функции и печатает его."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result

    return wrapper


def create_cacher():
    """Создаёт функцию кэширования; сам кэш хранится в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result