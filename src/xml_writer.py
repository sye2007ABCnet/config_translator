"""Преобразование значений конфигурации в XML."""

from xml.etree.ElementTree import Element, SubElement, indent, tostring

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


def to_xml(items):
    """Возвращает текст XML-документа для списка пар (имя, значение)."""
    root = Element("config")
    for name, value in items:
        element = value_to_element(value)
        if name is None:
            root.append(element)
        else:
            SubElement(root, "constant", name=name).append(element)
    indent(root)
    return XML_DECLARATION + tostring(root, encoding="unicode") + "\n"
