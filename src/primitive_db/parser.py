def parse_value(text):
    """Превращает текст в значение: "abc" -> str, 28 -> int, true -> bool."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    try:
        return int(text)
    except ValueError:
        raise ValueError(text) from None


def parse_values(text):
    """'("Sergei", 28, true)' -> ["Sergei", 28, True]."""
    text = text.strip()
    if not (text.startswith("(") and text.endswith(")")):
        raise ValueError(text)
    return [parse_value(part) for part in text[1:-1].split(",")]


def parse_condition(text):
    """'age = 28' -> {'age': 28}."""
    column, separator, value = text.partition("=")
    column = column.strip()
    if not separator or not column:
        raise ValueError(text.strip())
    return {column: parse_value(value)}