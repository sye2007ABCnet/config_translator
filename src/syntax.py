"""Синтаксический разбор конфигурации и вычисление констант."""

import math
from operator import add, mul, sub

from errors import TranslationError
from lexer import END_KIND, tokenize

RESERVED_NAMES = ("set", "sqrt", "min")
FUNCTION_NAMES = ("sqrt", "min")
SQRT_ARGUMENT_COUNT = 1
SUM_OPERATIONS = {"+": add, "-": sub}
PRODUCT_OPERATIONS = {"*": mul}


def describe(token):
    """Описывает лексему для сообщения об ошибке."""
    if token.kind == END_KIND:
        return "конец файла"
    return f"'{token.text}'"


class Parser:
    """Разбирает лексемы и сразу вычисляет значения и выражения.

    Грамматика:
        программа  = { "set" имя "=" значение | значение }
        значение   = число | строка | массив | "$" сумма "$"
        массив     = "[" [ значение { ";" значение } ] "]"
        сумма      = произведение { ("+" | "-") произведение }
        произведение = множитель { "*" множитель }
        множитель  = число | имя | вызов | "(" сумма ")"
        вызов      = ("sqrt" | "min") "(" сумма { ";" сумма } ")"
    """

    def __init__(self, tokens):
        """Запоминает лексемы; объявленных констант пока нет."""
        self.tokens = tokens
        self.position = 0
        self.constants = {}

    def peek(self):
        """Возвращает текущую лексему, не сдвигаясь."""
        return self.tokens[self.position]

    def advance(self):
        """Возвращает текущую лексему и переходит к следующей."""
        token = self.tokens[self.position]
        if token.kind != END_KIND:
            self.position += 1
        return token

    def is_symbol(self, text):
        """Проверяет, что текущая лексема — символ text."""
        return self.peek().text == text

    def error(self, message, token):
        """Создаёт ошибку с позицией лексемы."""
        return TranslationError(message, token.line, token.column)

    def expect_symbol(self, text):
        """Пропускает символ text или сообщает об ошибке."""
        token = self.peek()
        if not self.is_symbol(text):
            raise self.error(
                f"ожидается '{text}', встречено: {describe(token)}", token
            )
        self.advance()

    def require_number(self, value, token):
        """Проверяет, что операнд — число."""
        if not isinstance(value, int):
            raise self.error("операнд должен быть числом", token)

    def parse_program(self):
        """Разбирает весь текст и возвращает список пар (имя, значение).

        У значения верхнего уровня, не связанного с константой, имя None.
        """
        items = []
        while self.peek().kind != END_KIND:
            if self.is_symbol("set"):
                items.append(self.parse_set())
            else:
                items.append((None, self.parse_value()))
        return items

    def parse_set(self):
        """Разбирает 'set имя = значение' и запоминает константу."""
        self.advance()
        token = self.advance()
        if token.kind != "name" or token.text in RESERVED_NAMES:
            raise self.error(
                f"ожидается имя константы, встречено: {describe(token)}",
                token,
            )
        if token.text in self.constants:
            raise self.error(f"константа '{token.text}' уже задана", token)
        self.expect_symbol("=")
        value = self.parse_value()
        self.constants[token.text] = value
        return token.text, value

    def parse_value(self):
        """Разбирает значение: число, строку, массив или выражение."""
        token = self.peek()
        if token.kind == "number":
            self.advance()
            return int(token.text, 2)
        if token.kind == "string":
            self.advance()
            return token.text[2:-1]
        if self.is_symbol("["):
            return self.parse_array()
        if self.is_symbol("$"):
            return self.parse_constant_expression()
        raise self.error(
            f"ожидается значение, встречено: {describe(token)}", token
        )

    def parse_array(self):
        """Разбирает массив значений, разделённых точкой с запятой."""
        self.advance()
        items = []
        if not self.is_symbol("]"):
            items.append(self.parse_value())
            while self.is_symbol(";"):
                self.advance()
                items.append(self.parse_value())
        token = self.peek()
        if not self.is_symbol("]"):
            raise self.error(
                f"ожидается ';' или ']', встречено: {describe(token)}", token
            )
        self.advance()
        return items

    def parse_constant_expression(self):
        """Разбирает выражение между знаками $ и вычисляет его."""
        self.advance()
        value = self.parse_sum()
        self.expect_symbol("$")
        return value

    def parse_chain(self, parse_operand, operations):
        """Разбирает операнды, соединённые операциями, слева направо."""
        value = parse_operand()
        while self.peek().text in operations:
            sign = self.advance()
            right = parse_operand()
            self.require_number(value, sign)
            self.require_number(right, sign)
            value = operations[sign.text](value, right)
        return value

    def parse_sum(self):
        """Разбирает сложение и вычитание."""
        return self.parse_chain(self.parse_product, SUM_OPERATIONS)

    def parse_product(self):
        """Разбирает умножение."""
        return self.parse_chain(self.parse_factor, PRODUCT_OPERATIONS)

    def parse_factor(self):
        """Разбирает число, константу, вызов функции или скобки."""
        token = self.advance()
        if token.kind == "number":
            return int(token.text, 2)
        if token.kind == "name":
            return self.parse_name(token)
        if token.text == "(":
            value = self.parse_sum()
            self.expect_symbol(")")
            return value
        raise self.error(
            f"ожидается операнд, встречено: {describe(token)}", token
        )

    def parse_name(self, token):
        """Возвращает значение константы или результат вызова функции."""
        if token.text in FUNCTION_NAMES:
            return self.parse_call(token)
        if token.text not in self.constants:
            raise self.error(f"константа '{token.text}' не задана", token)
        return self.constants[token.text]

    def parse_call(self, token):
        """Разбирает аргументы функции и вычисляет её."""
        self.expect_symbol("(")
        arguments = [self.parse_sum()]
        while self.is_symbol(";"):
            self.advance()
            arguments.append(self.parse_sum())
        self.expect_symbol(")")
        for argument in arguments:
            self.require_number(argument, token)
        return self.call_function(token, arguments)

    def call_function(self, token, arguments):
        """Вычисляет sqrt (целая часть корня) или min."""
        if token.text == "min":
            return min(arguments)
        if len(arguments) != SQRT_ARGUMENT_COUNT:
            raise self.error("sqrt принимает ровно один аргумент", token)
        try:
            return math.isqrt(arguments[0])
        except ValueError:
            raise self.error("корень из отрицательного числа", token) from None


def parse(text):
    """Разбирает текст конфигурации и возвращает список (имя, значение)."""
    return Parser(tokenize(text)).parse_program()
