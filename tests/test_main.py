"""Тесты командной строки и примеров конфигураций."""

import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from xml.etree.ElementTree import fromstring

from main import EXIT_ERROR, EXIT_OK, main


def example_path(name):
    """Возвращает путь к файлу из каталога examples."""
    return os.path.join(os.path.dirname(__file__), "..", "examples", name)


def run_main(argv):
    """Запускает main и возвращает (код, stdout, stderr)."""
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def element_to_value(element):
    """Превращает XML-элемент обратно в число, строку или список."""
    if element.tag == "number":
        return int(element.text)
    if element.tag == "string":
        return element.text
    return [element_to_value(child) for child in element]


def values_of(xml_text):
    """Возвращает список значений верхнего уровня из XML."""
    return [element_to_value(child) for child in fromstring(xml_text)]


class MainTestCase(unittest.TestCase):
    """База для тестов с временным каталогом."""

    def setUp(self):
        """Создаёт временный каталог."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name

    def path(self, name):
        """Возвращает путь внутри временного каталога."""
        return os.path.join(self.folder, name)

    def write_input(self, text):
        """Создаёт входной файл с текстом и возвращает его путь."""
        path = self.path("input.conf")
        with open(path, "w", encoding="utf-8") as target:
            target.write(text)
        return path

    def translate(self, text):
        """Переводит текст и возвращает (код, XML или None, stderr)."""
        output = self.path("output.xml")
        code, _, err = run_main(["-i", self.write_input(text), "-o", output])
        if not os.path.exists(output):
            return code, None, err
        with open(output, encoding="utf-8") as source:
            return code, source.read(), err


class TranslateTests(MainTestCase):
    """Успешные и неуспешные запуски."""

    def test_success(self):
        """Результат записан в выходной файл, код 0."""
        code, xml, _ = self.translate("0b101")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(values_of(xml), [5])

    def test_declared_constant_is_not_written(self):
        """Объявленная константа не попадает в XML."""
        code, xml, _ = self.translate("set a = 0b101")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(values_of(xml), [])
        self.assertNotIn("constant", xml)

    def test_used_constant_is_substituted(self):
        """Использованная константа подставляется значением."""
        _, xml, _ = self.translate("set a = 0b101\n$a + 0b1$")
        self.assertEqual(values_of(xml), [6])
        self.assertNotIn("constant", xml)

    def test_message_about_result(self):
        """После успешной записи выводится сообщение."""
        output = self.path("out.xml")
        _, out, _ = run_main(["-i", self.write_input("0b1"), "-o", output])
        self.assertIn(output, out)

    def test_syntax_error(self):
        """Синтаксическая ошибка: код 1, сообщение, файл не создаётся."""
        code, xml, err = self.translate("set a = ")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIsNone(xml)
        self.assertIn("ошибка: строка 1", err)

    def test_error_position_in_message(self):
        """Сообщение содержит строку и столбец."""
        _, _, err = self.translate("set a = 0b1\nset b = ?")
        self.assertIn("строка 2, столбец 9", err)

    def test_missing_input_file(self):
        """Нет входного файла: код 1."""
        code, _, err = run_main(
            ["-i", self.path("none.conf"), "-o", self.path("out.xml")]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не удалось прочитать", err)

    def test_input_is_not_utf8(self):
        """Входной файл не в UTF-8: код 1."""
        path = self.path("bad.conf")
        with open(path, "wb") as target:
            target.write(b"\xff\xfe\x00")
        code, _, err = run_main(["-i", path, "-o", self.path("out.xml")])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не удалось прочитать", err)

    def test_output_cannot_be_written(self):
        """Выходной путь недоступен: код 1."""
        code, _, err = run_main(
            ["-i", self.write_input("0b1"), "-o", self.path("no/dir/out.xml")]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не удалось записать", err)

    def test_missing_arguments(self):
        """Без обязательных ключей argparse завершает работу с кодом 2."""
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main([])
        self.assertEqual(caught.exception.code, 2)

    def test_long_option_names(self):
        """Работают длинные имена ключей."""
        output = self.path("out.xml")
        code, _, _ = run_main(
            ["--input", self.write_input("0b1"), "--output", output]
        )
        self.assertEqual(code, EXIT_OK)

    def test_comments_and_nesting_together(self):
        """Комментарии, вложенные массивы и выражения в одном файле."""
        text = (
            "' начало\n"
            "{ многострочный\nкомментарий }\n"
            "set n = 0b11\n"
            "[q(a); [$n * n$; [$min(n; 0b10)$]]]\n"
        )
        _, xml, _ = self.translate(text)
        self.assertEqual(values_of(xml), [["a", [9, [2]]]])


class ExampleTests(MainTestCase):
    """Три примера конфигураций из разных предметных областей."""

    def translate_example(self, name):
        """Переводит пример и возвращает значения верхнего уровня."""
        output = self.path("out.xml")
        code, _, _ = run_main(["-i", example_path(name), "-o", output])
        self.assertEqual(code, EXIT_OK)
        with open(output, encoding="utf-8") as source:
            return values_of(source.read())

    def test_web_server(self):
        """Веб-сервер."""
        self.assertEqual(
            self.translate_example("web_server.conf"),
            [
                "example server",
                80,
                800,
                ["localhost", "example.org", "www.example.org"],
                [10, 30, 20],
            ],
        )

    def test_game_level(self):
        """Игровой уровень."""
        self.assertEqual(
            self.translate_example("game_level.conf"),
            [
                "Cave of Echoes",
                32,
                1024,
                [[1, 1], [30, 5], [31, 31]],
                ["bat", "spider", "golem"],
                320,
                32,
            ],
        )

    def test_pendulum_lab(self):
        """Лабораторная установка."""
        self.assertEqual(
            self.translate_example("pendulum_lab.conf"),
            [
                "Pendulum period",
                [100, 200, 400],
                15,
                100,
                100,
                10,
                ["stopwatch", "ruler", ["sensor A", "sensor B"]],
            ],
        )

    def test_examples_have_no_constant_tag(self):
        """В результатах примеров нет тега constant."""
        for name in (
            "web_server.conf",
            "game_level.conf",
            "pendulum_lab.conf",
        ):
            output = self.path("out.xml")
            run_main(["-i", example_path(name), "-o", output])
            with open(output, encoding="utf-8") as source:
                self.assertNotIn("constant", source.read())


if __name__ == "__main__":
    unittest.main()