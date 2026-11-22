"""Лексический анализ учебного конфигурационного языка."""

import re
from dataclasses import dataclass

from errors import TranslationError

TOKEN_PATTERNS = (
    ("space", r"\s+"),
    ("line_comment", r"'[^\n]*"),
    ("block_comment", r"\{[^}]*\}"),
    ("unclosed_comment", r"\{"),
    ("stray_brace", r"\}"),
    ("number", r"0[bB][01]+(?![a-zA-Z0-9])"),
    ("bad_number", r"[0-9][a-zA-Z0-9]*"),
    ("string", r"q\([^)]*\)"),
    ("unclosed_string", r"q\("),
    ("name", r"[a-zA-Z][a-zA-Z0-9]*"),
    ("symbol", r"[=\[\];$+\-*()]"),
)
SKIPPED_KINDS = ("space", "line_comment", "block_comment")
ERROR_MESSAGES = {
    "unclosed_comment": "незакрытый многострочный комментарий",
    "stray_brace": "лишняя закрывающая фигурная скобка",
    "bad_number": "некорректное число '{text}': "
    "ожидается 0b или 0B и двоичные цифры",
    "unclosed_string": "незакрытая строка: ожидается ')'",
}
END_KIND = "end"


@dataclass(frozen=True)
class Token:
    """Лексема: вид, текст и позиция в исходном тексте."""

    kind: str
    text: str
    line: int
    column: int


def locate(text, offset):
    """Возвращает номер строки и столбца (с единицы) для смещения."""
    line = text.count("\n", 0, offset) + 1
    column = offset - text.rfind("\n", 0, offset)
    return line, column


def build_pattern():
    """Собирает регулярное выражение из всех видов лексем."""
    parts = (f"(?P<{kind}>{regex})" for kind, regex in TOKEN_PATTERNS)
    return re.compile("|".join(parts))


def tokenize(text):
    """Разбивает текст на лексемы; последней идёт лексема конца файла."""
    pattern = build_pattern()
    tokens = []
    position = 0
    while position < len(text):
        match = pattern.match(text, position)
        if match is None:
            line, column = locate(text, position)
            message = f"недопустимый символ {text[position]!r}"
            raise TranslationError(message, line, column)
        kind = match.lastgroup
        if kind in ERROR_MESSAGES:
            line, column = locate(text, position)
            message = ERROR_MESSAGES[kind].format(text=match.group())
            raise TranslationError(message, line, column)
        if kind not in SKIPPED_KINDS:
            line, column = locate(text, position)
            tokens.append(Token(kind, match.group(), line, column))
        position = match.end()
    line, column = locate(text, position)
    tokens.append(Token(END_KIND, "", line, column))
    return tokens
