"""Преобразование значений конфигурации в XML."""

from xml.etree.ElementTree import Element, indent, tostring

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'


def value_to_element(value):
    """Строит XML-элемент для числа, строки или массива."""
    if isinstance(value, list):
        element = Element("array")
        element.extend(value_to_element(item) for item in value)
        return element
    element = Element("string" if isinstance(value, str) else "number")
    element.text = str(value)
    return element


def to_xml(values):
    """Возвращает текст XML-документа для списка значений верхнего уровня."""
    root = Element("config")
    root.extend(value_to_element(value) for value in values)
    indent(root)
    return XML_DECLARATION + tostring(root, encoding="unicode") + "\n"
