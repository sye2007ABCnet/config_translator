"""Ошибки трансляции учебного конфигурационного языка."""


class TranslationError(Exception):
    """Ошибка чтения, разбора или записи; сообщение содержит позицию."""

    def __init__(self, message, line=None, column=None):
        """Добавляет к сообщению номер строки и столбца, если они известны."""
        if line is not None:
            message = f"строка {line}, столбец {column}: {message}"
        super().__init__(message)
