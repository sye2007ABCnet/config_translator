"""Инструмент командной строки: учебный конфигурационный язык -> XML."""

import argparse
import sys

from errors import TranslationError
from syntax import parse
from xml_writer import to_xml

EXIT_OK = 0
EXIT_ERROR = 1


def parse_arguments(argv=None):
    """Разбирает ключи командной строки: входной и выходной файлы."""
    parser = argparse.ArgumentParser(
        description="Преобразует конфигурацию из учебного языка в XML."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="путь к входному файлу"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="путь к выходному XML-файлу"
    )
    return parser.parse_args(argv)


def read_text(path):
    """Читает входной файл целиком."""
    try:
        with open(path, encoding="utf-8") as source:
            return source.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise TranslationError(
            f"не удалось прочитать '{path}': {exc}"
        ) from exc


def write_text(path, text):
    """Записывает результат в выходной файл."""
    try:
        with open(path, "w", encoding="utf-8") as target:
            target.write(text)
    except OSError as exc:
        raise TranslationError(f"не удалось записать '{path}': {exc}") from exc


def main(argv=None):
    """Точка входа. Возвращает код завершения процесса."""
    arguments = parse_arguments(argv)
    try:
        xml = to_xml(parse(read_text(arguments.input)))
        write_text(arguments.output, xml)
    except TranslationError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"Результат записан в {arguments.output}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
