from common.utils.doc_config import doc_language

module_docstrings = {
    'en': """
    Module for localizing docstrings in the project.

    This module provides a decorator that allows setting localized docstrings
    for functions based on the current language setting.

    The language can be switched by modifying the 'doc_language' variable.
    """,
    'de': """
    Modul zur Lokalisierung von Docstrings im Projekt.

    Dieses Modul stellt einen Dekorator bereit, mit dem lokalisierte Docstrings
    für Funktionen basierend auf der aktuellen Spracheinstellung gesetzt werden können.

    Die Sprache kann durch Ändern der Variablen 'doc_language' umgeschaltet werden.
    """,
    'ru': """
    Модуль для локализации docstring'ов в проекте.

    Этот модуль предоставляет декоратор, который позволяет устанавливать 
    локализованные docstring'и для функций на основе текущего языка.

    Язык можно переключить, изменив значение переменной 'doc_language'.
    """
}


def localized_docstring(docstrings):
    def decorator(obj):
        obj.__doc__ = docstrings.get(doc_language, "No documentation available")
        return obj
    return decorator


__doc__ = module_docstrings.get(doc_language, "No documentation available")

if __name__ == '__main__':
    print(__doc__)
