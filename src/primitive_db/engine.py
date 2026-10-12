import prompt


def print_help():
    """Печатает список доступных команд."""
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def welcome():
    """Приветствие и цикл обработки команд пользователя."""
    print("Первая попытка запустить проект!")
    print()
    print("***")
    print_help()

    while True:
        command = prompt.string("Введите команду: ")
        match command:
            case "exit":
                break
            case "help":
                print()
                print_help()
            case _:
                print(f"Неизвестная команда: {command}")