"""Тесты лексического анализа."""

import unittest

from errors import TranslationError
from lexer import tokenize


def kinds_and_texts(text):
    """Возвращает пары (вид, текст) всех лексем, кроме конца файла."""
    return [(token.kind, token.text) for token in tokenize(text)[:-1]]


def error_message(text):
    """Возвращает сообщение об ошибке для некорректного текста."""
    with unittest.TestCase().assertRaises(TranslationError) as caught:
        tokenize(text)
    return str(caught.exception)


class NumberTests(unittest.TestCase):
    """Двоичные числа."""

    def test_lowercase_prefix(self):
        """Число с префиксом 0b."""
        self.assertEqual(kinds_and_texts("0b101"), [("number", "0b101")])

    def test_uppercase_prefix(self):
        """Число с префиксом 0B."""
        self.assertEqual(kinds_and_texts("0B1"), [("number", "0B1")])

    def test_decimal_number_is_rejected(self):
        """Десятичное число недопустимо."""
        self.assertIn("некорректное число '12'", error_message("12"))

    def test_bad_binary_digit(self):
        """Цифра, не являющаяся двоичной, недопустима."""
        self.assertIn("некорректное число '0b12'", error_message("0b12"))

    def test_prefix_without_digits(self):
        """Префикс без цифр недопустим."""
        self.assertIn("некорректное число '0b'", error_message("0b"))

    def test_number_followed_by_letters(self):
        """Буквы после числа недопустимы."""
        self.assertIn("некорректное число", error_message("0b101x"))


class NameAndStringTests(unittest.TestCase):
    """Имена и строки."""

    def test_names(self):
        """Имена из букв и цифр, начинаются с буквы."""
        self.assertEqual(
            kinds_and_texts("a Abc x1y2"),
            [("name", "a"), ("name", "Abc"), ("name", "x1y2")],
        )

    def test_name_starting_with_q(self):
        """Имя, начинающееся с q, не путается со строкой."""
        self.assertEqual(kinds_and_texts("qq"), [("name", "qq")])

    def test_string(self):
        """Строка q(...) с пробелами."""
        self.assertEqual(
            kinds_and_texts("q(Это строка)"), [("string", "q(Это строка)")]
        )

    def test_empty_string(self):
        """Пустая строка."""
        self.assertEqual(kinds_and_texts("q()"), [("string", "q()")])

    def test_string_with_comment_characters(self):
        """Внутри строки апостроф и фигурные скобки не начинают комментарий."""
        text = "q(it's {not} a comment)"
        self.assertEqual(kinds_and_texts(text), [("string", text)])

    def test_multiline_string(self):
        """Строка может занимать несколько строк."""
        text = "q(a\nb)"
        self.assertEqual(kinds_and_texts(text), [("string", text)])

    def test_unclosed_string(self):
        """Строка без закрывающей скобки."""
        self.assertIn("незакрытая строка", error_message("q(abc"))


class CommentTests(unittest.TestCase):
    """Однострочные и многострочные комментарии."""

    def test_line_comment_is_skipped(self):
        """Однострочный комментарий идёт до конца строки."""
        self.assertEqual(
            kinds_and_texts("a ' комментарий\nb"),
            [("name", "a"), ("name", "b")],
        )

    def test_block_comment_is_skipped(self):
        """Многострочный комментарий пропускается целиком."""
        text = "a {\nмного\nстрок\n} b"
        self.assertEqual(kinds_and_texts(text), [("name", "a"), ("name", "b")])

    def test_block_comment_hides_line_comment_mark(self):
        """Апостроф внутри многострочного комментария ничего не значит."""
        self.assertEqual(kinds_and_texts("{ it's }a"), [("name", "a")])

    def test_line_comment_hides_braces(self):
        """Скобки внутри однострочного комментария ничего не значат."""
        self.assertEqual(kinds_and_texts("' { }\na"), [("name", "a")])

    def test_unclosed_block_comment(self):
        """Многострочный комментарий без закрывающей скобки."""
        self.assertIn("незакрытый многострочный", error_message("a {b"))

    def test_stray_closing_brace(self):
        """Закрывающая скобка без открывающей."""
        self.assertIn("лишняя закрывающая", error_message("a }"))


class SymbolAndPositionTests(unittest.TestCase):
    """Символы, позиции и конец файла."""

    def test_symbols(self):
        """Все служебные символы."""
        text = "= [ ] ; $ + - * ( )"
        expected = [("symbol", char) for char in text.split()]
        self.assertEqual(kinds_and_texts(text), expected)

    def test_unknown_character(self):
        """Недопустимый символ."""
        self.assertIn("недопустимый символ '@'", error_message("a @ b"))

    def test_end_token(self):
        """Последняя лексема — конец файла."""
        self.assertEqual(tokenize("a")[-1].kind, "end")
        self.assertEqual(tokenize("")[-1].kind, "end")

    def test_positions(self):
        """Лексемы хранят строку и столбец."""
        tokens = tokenize("set a\n  = 0b1")
        positions = [(t.text, t.line, t.column) for t in tokens[:-1]]
        self.assertEqual(
            positions,
            [("set", 1, 1), ("a", 1, 5), ("=", 2, 3), ("0b1", 2, 5)],
        )

    def test_error_position(self):
        """Ошибка указывает строку и столбец."""
        self.assertEqual(
            error_message("a\n  @"),
            "строка 2, столбец 3: недопустимый символ '@'",
        )


if __name__ == "__main__":
    unittest.main()