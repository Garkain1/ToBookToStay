import unittest
from common.utils.localized_docs import localized_docstring
from common.utils.doc_config import doc_language


class TestLocalizedDocstring(unittest.TestCase):

    def setUp(self):
        self.docstrings = {
            'en': "This is an English docstring.",
            'ru': "Это документация на русском языке.",
            'de': "Dies ist ein deutscher Docstring."
        }

    def test_docstring(self):
        @localized_docstring(self.docstrings)
        def test_func():
            pass

        if doc_language == 'en':
            self.assertEqual(test_func.__doc__, "This is an English docstring.")
        elif doc_language == 'ru':
            self.assertEqual(test_func.__doc__, "Это документация на русском языке.")
        elif doc_language == 'de':
            self.assertEqual(test_func.__doc__, "Dies ist ein deutscher Docstring.")
        else:
            self.assertEqual(test_func.__doc__, "No documentation available")


if __name__ == '__main__':
    unittest.main()
