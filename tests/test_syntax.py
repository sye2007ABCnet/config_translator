"""Тесты разбора и вычисления констант."""

import unittest

from errors import TranslationError
from syntax import parse


def error_message(text):
    """Возвращает сообщение об ошибке для некорректного текста."""
    with unittest.TestCase().assertRaises(TranslationError) as caught:
        parse(text)
    return str(caught.exception)


class ValueTests(unittest.TestCase):
    """Числа, строки и массивы."""

    def test_binary_numbers(self):
        """Двоичные числа переводятся в целые."""
        self.assertEqual(parse("0b101 0B11 0b0"), [5, 3, 0])

    def test_string(self):
        """Строка без обрамления q( )."""
        self.assertEqual(parse("q(Это строка)"), ["Это строка"])

    def test_empty_array(self):
        """Пустой массив."""
        self.assertEqual(parse("[]"), [[]])

    def test_array_of_numbers(self):
        """Массив чисел."""
        self.assertEqual(parse("[0b1; 0b10; 0b11]"), [[1, 2, 3]])

    def test_mixed_array(self):
        """Массив из чисел и строк."""
        self.assertEqual(parse("[0b1; q(a)]"), [[1, "a"]])

    def test_nested_arrays(self):
        """Вложенные массивы любой глубины."""
        self.assertEqual(
            parse("[[0b1; [0b10]]; []; [[[q(x)]]]]"),
            [[[1, [2]], [], [[["x"]]]]],
        )

    def test_array_over_several_lines(self):
        """Массив можно записать в несколько строк."""
        self.assertEqual(parse("[\n0b1;\n0b10\n]"), [[1, 2]])

    def test_trailing_separator(self):
        """Лишняя точка с запятой в конце массива недопустима."""
        self.assertIn("ожидается значение", error_message("[0b1;]"))

    def test_missing_separator(self):
        """Значения без разделителя недопустимы."""
        self.assertIn("ожидается ';' или ']'", error_message("[0b1 0b10]"))

    def test_unclosed_array(self):
        """Массив без закрывающей скобки."""
        self.assertIn("ожидается ';' или ']'", error_message("[0b1"))

    def test_empty_text(self):
        """Пустой текст даёт пустой результат."""
        self.assertEqual(parse(""), [])


class CommentPlacementTests(unittest.TestCase):
    """Комментарии могут стоять между любыми лексемами."""

    def test_comments_everywhere(self):
        """Комментарии внутри set, массива и выражения."""
        text = (
            "set { после set } a ' до равно\n"
            "= [0b1 { в массиве } ; 0b10 ' ещё\n]\n"
            "$ { в выражении } a ' конец\n$"
        )
        self.assertEqual(parse(text), [[1, 2]])


class SetTests(unittest.TestCase):
    """Объявление констант."""

    def test_set_is_not_in_result(self):
        """Объявленные константы в результат не попадают."""
        self.assertEqual(parse("set a = 0b1 set b = q(x)"), [])

    def test_unused_constant_is_not_in_result(self):
        """Неиспользуемая константа не влияет на результат."""
        self.assertEqual(parse("set a = [0b1; q(x)] q(y)"), ["y"])

    def test_value_after_set(self):
        """Значение после set попадает в результат."""
        self.assertEqual(parse("set a = 0b1 0b10"), [2])

    def test_constant_array_and_string(self):
        """Константой может быть число, строка или массив."""
        text = "set n = 0b1 set s = q(x) set a = [0b10] $n$ $s$ $a$"
        self.assertEqual(parse(text), [1, "x", [2]])

    def test_redefinition(self):
        """Повторное объявление константы недопустимо."""
        message = error_message("set a = 0b1\nset a = 0b10")
        self.assertEqual(
            message, "строка 2, столбец 5: константа 'a' уже задана"
        )

    def test_reserved_name(self):
        """Служебные слова нельзя использовать как имена констант."""
        for name in ("set", "sqrt", "min"):
            self.assertIn("ожидается имя", error_message(f"set {name} = 0b1"))

    def test_set_at_end_of_file(self):
        """Слово set в конце файла без имени."""
        self.assertIn("встречено: конец файла", error_message("set"))

    def test_missing_name(self):
        """После set нужно имя."""
        self.assertIn("ожидается имя", error_message("set = 0b1"))

    def test_missing_equals(self):
        """После имени нужен знак равенства."""
        self.assertIn("ожидается '='", error_message("set a 0b1"))

    def test_missing_value(self):
        """После знака равенства нужно значение."""
        self.assertIn("встречено: конец файла", error_message("set a ="))

    def test_stray_symbol(self):
        """Лишний символ на верхнем уровне."""
        self.assertIn("ожидается значение", error_message("= 0b1"))


class ExpressionTests(unittest.TestCase):
    """Вычисление константных выражений."""

    def test_number(self):
        """Выражение из одного числа."""
        self.assertEqual(parse("$0b101$"), [5])

    def test_addition_and_subtraction(self):
        """Сложение и вычитание выполняются слева направо."""
        self.assertEqual(parse("$0b1010 - 0b11 + 0b1$"), [8])

    def test_negative_result(self):
        """Результат вычитания может быть отрицательным."""
        self.assertEqual(parse("$0b1 - 0b100$"), [-3])

    def test_multiplication(self):
        """Умножение."""
        self.assertEqual(parse("$0b11 * 0b101$"), [15])

    def test_precedence(self):
        """Умножение выполняется раньше сложения."""
        self.assertEqual(parse("$0b1 + 0b10 * 0b11$"), [7])

    def test_parentheses(self):
        """Скобки меняют порядок действий."""
        self.assertEqual(parse("$(0b1 + 0b10) * 0b11$"), [9])

    def test_nested_parentheses(self):
        """Вложенные скобки."""
        self.assertEqual(parse("$((0b1 + 0b1) * (0b10 + 0b1))$"), [6])

    def test_constant_reference(self):
        """Выражение использует ранее заданную константу."""
        self.assertEqual(parse("set a = 0b101 $a + 0b1$"), [6])

    def test_constants_chain(self):
        """Константа может быть вычислена из других констант."""
        text = "set a = 0b10 set b = $a * a$ set c = $b + a$ $a$ $b$ $c$"
        self.assertEqual(parse(text), [2, 4, 6])

    def test_constant_value_of_any_type(self):
        """Выражение из одного имени возвращает массив или строку."""
        text = "set a = [0b1; q(x)] set b = q(s) $a$ $b$"
        self.assertEqual(parse(text), [[1, "x"], "s"])

    def test_expression_inside_array(self):
        """Выражение может быть элементом массива, в том числе вложенного."""
        text = "set a = 0b10 [$a + 0b1$; [$a * a$; [$a - 0b1$]]]"
        self.assertEqual(parse(text), [[3, [4, [1]]]])

    def test_sqrt(self):
        """Корень — целая часть."""
        self.assertEqual(parse("$sqrt(0b10000)$ $sqrt(0b1010)$"), [4, 3])

    def test_sqrt_of_expression(self):
        """Аргумент sqrt — выражение."""
        self.assertEqual(parse("$sqrt(0b100 * 0b100)$"), [4])

    def test_min(self):
        """Минимум из нескольких чисел."""
        self.assertEqual(parse("$min(0b11; 0b1; 0b10)$"), [1])

    def test_min_of_one_argument(self):
        """Минимум из одного числа."""
        self.assertEqual(parse("$min(0b11)$"), [3])

    def test_nested_functions(self):
        """Вложенные вызовы функций и операций."""
        text = "$min(sqrt(0b1001) + 0b1; min(0b1000; 0b110) - 0b10) * 0b10$"
        self.assertEqual(parse(text), [8])

    def test_function_with_constant(self):
        """Функции принимают константы."""
        text = "set a = 0b10100 $min(a; 0b11) + sqrt(a)$"
        self.assertEqual(parse(text), [7])


class ExpressionErrorTests(unittest.TestCase):
    """Ошибки в выражениях."""

    def test_unknown_constant(self):
        """Константа не задана."""
        self.assertEqual(
            error_message("$a + 0b1$"),
            "строка 1, столбец 2: константа 'a' не задана",
        )

    def test_constant_used_before_set(self):
        """Константу нельзя использовать до объявления."""
        self.assertIn("не задана", error_message("$a$ set a = 0b1"))

    def test_string_operand(self):
        """Со строкой нельзя выполнять арифметику."""
        message = error_message("set a = q(x) $a + 0b1$")
        self.assertIn("операнд должен быть числом", message)

    def test_array_operand(self):
        """С массивом нельзя выполнять арифметику."""
        self.assertIn(
            "операнд должен быть числом",
            error_message("set a = [0b1] $0b1 * a$"),
        )

    def test_function_of_string(self):
        """Функции принимают только числа."""
        self.assertIn(
            "операнд должен быть числом",
            error_message("set a = q(x) $sqrt(a)$"),
        )

    def test_sqrt_of_negative(self):
        """Корень из отрицательного числа."""
        self.assertIn(
            "корень из отрицательного", error_message("$sqrt(0b1 - 0b10)$")
        )

    def test_sqrt_arguments(self):
        """sqrt принимает один аргумент."""
        self.assertIn(
            "ровно один аргумент", error_message("$sqrt(0b1; 0b10)$")
        )

    def test_function_without_parenthesis(self):
        """После имени функции нужна скобка."""
        self.assertIn("ожидается '('", error_message("$min 0b1$"))

    def test_function_without_arguments(self):
        """Функция без аргументов недопустима."""
        self.assertIn("ожидается операнд", error_message("$min()$"))

    def test_unclosed_call(self):
        """Вызов без закрывающей скобки."""
        self.assertIn("ожидается ')'", error_message("$min(0b1; 0b10$"))

    def test_unclosed_parenthesis(self):
        """Скобка без пары."""
        self.assertIn("ожидается ')'", error_message("$(0b1 + 0b10$"))

    def test_missing_closing_dollar(self):
        """Выражение без закрывающего знака $."""
        self.assertIn("ожидается '$'", error_message("$0b1 + 0b10"))

    def test_empty_expression(self):
        """Пустое выражение."""
        self.assertIn("ожидается операнд", error_message("$$"))

    def test_missing_operand(self):
        """У операции нет правого операнда."""
        self.assertIn("ожидается операнд", error_message("$0b1 +$"))

    def test_error_position_on_second_line(self):
        """Ошибка в выражении указывает верную строку."""
        message = error_message("set a = 0b1\nset b = $a + c$")
        self.assertEqual(
            message, "строка 2, столбец 14: константа 'c' не задана"
        )


if __name__ == "__main__":
    unittest.main()