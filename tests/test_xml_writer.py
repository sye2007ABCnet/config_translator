"""Тесты формирования XML."""

import unittest
from xml.etree.ElementTree import fromstring

from xml_writer import to_xml, value_to_element

HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'


class ValueToElementTests(unittest.TestCase):
    """Элементы для отдельных значений."""

    def test_number(self):
        """Число — элемент number с десятичной записью."""
        element = value_to_element(80)
        self.assertEqual((element.tag, element.text), ("number", "80"))

    def test_negative_number(self):
        """Отрицательное число."""
        self.assertEqual(value_to_element(-3).text, "-3")

    def test_string(self):
        """Строка — элемент string."""
        element = value_to_element("текст")
        self.assertEqual((element.tag, element.text), ("string", "текст"))

    def test_array(self):
        """Массив — элемент array с вложенными элементами."""
        element = value_to_element([1, "a"])
        self.assertEqual(
            [(child.tag, child.text) for child in element],
            [("number", "1"), ("string", "a")],
        )

    def test_nested_array(self):
        """Вложенные массивы."""
        element = value_to_element([[1], [[]]])
        self.assertEqual([child.tag for child in element], ["array", "array"])
        self.assertEqual(element[1][0].tag, "array")


class ToXmlTests(unittest.TestCase):
    """Документ целиком."""

    def test_empty_config(self):
        """Пустой список даёт пустой корень."""
        self.assertEqual(to_xml([]), HEADER + "<config />\n")

    def test_number_in_root(self):
        """Значение попадает прямо в корень, без обёрток."""
        self.assertEqual(
            to_xml([80]),
            HEADER + "<config>\n  <number>80</number>\n</config>\n",
        )

    def test_string_in_root(self):
        """Строка попадает прямо в корень."""
        self.assertEqual(
            to_xml(["x"]),
            HEADER + "<config>\n  <string>x</string>\n</config>\n",
        )

    def test_nested_array_document(self):
        """Вложенный массив записывается с отступами."""
        self.assertEqual(
            to_xml([[1, [2]]]),
            HEADER
            + "<config>\n"
            + "  <array>\n"
            + "    <number>1</number>\n"
            + "    <array>\n"
            + "      <number>2</number>\n"
            + "    </array>\n"
            + "  </array>\n"
            + "</config>\n",
        )

    def test_no_constant_tag(self):
        """Тега constant в документе нет."""
        self.assertNotIn("constant", to_xml([1, "a", [2]]))

    def test_order_is_kept(self):
        """Порядок элементов сохраняется."""
        root = fromstring(to_xml([1, "a", [2]]))
        self.assertEqual(
            [child.tag for child in root], ["number", "string", "array"]
        )

    def test_special_characters_are_escaped(self):
        """Служебные символы XML экранируются."""
        root = fromstring(to_xml(["<a & b>"]))
        self.assertEqual(root[0].text, "<a & b>")

    def test_spaces_in_string_are_kept(self):
        """Пробелы по краям строки сохраняются."""
        root = fromstring(to_xml(["  x  "]))
        self.assertEqual(root[0].text, "  x  ")

    def test_empty_string_and_array(self):
        """Пустая строка и пустой массив."""
        root = fromstring(to_xml(["", []]))
        self.assertEqual([child.tag for child in root], ["string", "array"])


if __name__ == "__main__":
    unittest.main()