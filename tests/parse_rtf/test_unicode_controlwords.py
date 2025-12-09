"""Test Unicode character preservation in control words

This test suite verifies that Unicode characters in RTF control words
(lquote, rquote, ldblquote, rdblquote, bullet, endash, emdash) are
properly encoded and preserved during RTF de-encapsulation.

This addresses the issue where byte strings with Unicode escape sequences
like b'\\u2014' were incorrectly producing literal bytes instead of the
intended Unicode characters.
"""

import unittest
import warnings

from RTFDE.transformers import RTFCleaner
from lark.lexer import Token


class TestUnicodeControlWords(unittest.TestCase):
    """Test Unicode character preservation in RTF control words"""

    def setUp(self):
        """Set up test fixtures"""
        self.transformer = RTFCleaner()

    def test_no_syntax_warnings(self):
        """Verify that importing transformers.py produces no SyntaxWarning in Python 3.11+"""
        # This test ensures the fix eliminates the deprecation warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always", SyntaxWarning)
            warnings.simplefilter("always", DeprecationWarning)

            # Re-import the module to catch any warnings
            import importlib
            import RTFDE.transformers
            importlib.reload(RTFDE.transformers)

            # Filter for syntax/deprecation warnings about invalid escape sequences
            relevant_warnings = [
                w for w in warning_list
                if issubclass(w.category, (SyntaxWarning, DeprecationWarning))
                and 'invalid escape sequence' in str(w.message).lower()
            ]

            self.assertEqual(
                len(relevant_warnings), 0,
                f"Expected no SyntaxWarning/DeprecationWarning, but got {len(relevant_warnings)}: "
                f"{[str(w.message) for w in relevant_warnings]}"
            )

    def test_lquote_produces_correct_unicode(self):
        """Test that \\lquote produces left single quotation mark (U+2018)"""
        token = Token('CONTROLWORD', b'\\lquote')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u2018'.encode('utf-8')  # Left single quote '

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '\u2018')
        self.assertEqual(len(result), 3)  # UTF-8 encoding of U+2018 is 3 bytes

    def test_rquote_produces_correct_unicode(self):
        """Test that \\rquote produces right single quotation mark (U+2019)"""
        token = Token('CONTROLWORD', b'\\rquote')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u2019'.encode('utf-8')  # Right single quote '

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '\u2019')
        self.assertEqual(len(result), 3)

    def test_ldblquote_produces_correct_unicode(self):
        """Test that \\ldblquote produces left double quotation mark (U+201C)"""
        token = Token('CONTROLWORD', b'\\ldblquote')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u201C'.encode('utf-8')  # Left double quote "

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '\u201C')
        self.assertEqual(len(result), 3)

    def test_rdblquote_produces_correct_unicode(self):
        """Test that \\rdblquote produces right double quotation mark (U+201D)"""
        token = Token('CONTROLWORD', b'\\rdblquote')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u201D'.encode('utf-8')  # Right double quote "

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '\u201D')
        self.assertEqual(len(result), 3)

    def test_bullet_produces_correct_unicode(self):
        """Test that \\bullet produces bullet character (U+2022)"""
        token = Token('CONTROLWORD', b'\\bullet')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u2022'.encode('utf-8')  # Bullet •

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '•')
        self.assertEqual(len(result), 3)

    def test_endash_produces_correct_unicode(self):
        """Test that \\endash produces en dash character (U+2013)"""
        token = Token('CONTROLWORD', b'\\endash')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u2013'.encode('utf-8')  # En dash –

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '–')
        self.assertEqual(len(result), 3)

    def test_emdash_produces_correct_unicode(self):
        """Test that \\emdash produces em dash character (U+2014)"""
        token = Token('CONTROLWORD', b'\\emdash')
        result = self.transformer.CONTROLWORD(token)
        expected = '\u2014'.encode('utf-8')  # Em dash —

        self.assertEqual(result, expected)
        self.assertEqual(result.decode('utf-8'), '—')
        self.assertEqual(len(result), 3)

    def test_all_unicode_controlwords_comprehensive(self):
        """Comprehensive test for all Unicode control words"""
        test_cases = [
            (b'\\lquote', '\u2018'),
            (b'\\rquote', '\u2019'),
            (b'\\ldblquote', '\u201C'),
            (b'\\rdblquote', '\u201D'),
            (b'\\bullet', '\u2022'),
            (b'\\endash', '\u2013'),
            (b'\\emdash', '\u2014'),
        ]

        for control_word, unicode_char in test_cases:
            with self.subTest(control_word=control_word):
                token = Token('CONTROLWORD', control_word)
                result = self.transformer.CONTROLWORD(token)
                expected = unicode_char.encode('utf-8')

                self.assertEqual(result, expected,
                    f"{control_word} should produce {expected} but got {result}")
                self.assertEqual(result.decode('utf-8'), unicode_char,
                    f"{control_word} should decode to U+{ord(unicode_char):04X} but got U+{ord(result.decode('utf-8')):04X}")
                self.assertEqual(len(result), 3,
                    f"{control_word} should produce 3 UTF-8 bytes but got {len(result)}")

    def test_byte_values_are_correct(self):
        """Test that the actual byte values match expected UTF-8 encoding"""
        test_cases = [
            (b'\\lquote', b'\xe2\x80\x98'),
            (b'\\rquote', b'\xe2\x80\x99'),
            (b'\\ldblquote', b'\xe2\x80\x9c'),
            (b'\\rdblquote', b'\xe2\x80\x9d'),
            (b'\\bullet', b'\xe2\x80\xa2'),
            (b'\\endash', b'\xe2\x80\x93'),
            (b'\\emdash', b'\xe2\x80\x94'),
        ]

        for control_word, expected_bytes in test_cases:
            with self.subTest(control_word=control_word):
                token = Token('CONTROLWORD', control_word)
                result = self.transformer.CONTROLWORD(token)

                self.assertEqual(result, expected_bytes,
                    f"{control_word} should produce bytes {expected_bytes.hex()} "
                    f"but got {result.hex()}")

    def test_non_unicode_controlwords_still_work(self):
        """Test that non-Unicode control words (par, tab, line) still work correctly"""
        test_cases = [
            (b'\\par', b'\n'),
            (b'\\tab', b'\t'),
            (b'\\line', b'\n'),
        ]

        for control_word, expected in test_cases:
            with self.subTest(control_word=control_word):
                token = Token('CONTROLWORD', control_word)
                result = self.transformer.CONTROLWORD(token)

                self.assertEqual(result, expected,
                    f"{control_word} should produce {expected!r} but got {result!r}")

    def test_unknown_controlword_returns_empty_bytes(self):
        """Test that unknown control words return empty bytes"""
        token = Token('CONTROLWORD', b'\\unknownword')
        result = self.transformer.CONTROLWORD(token)

        self.assertEqual(result, b"")

    def test_bytes_not_literal_strings(self):
        """Test that the fix doesn't produce literal '\\u2014' strings"""
        token = Token('CONTROLWORD', b'\\emdash')
        result = self.transformer.CONTROLWORD(token)

        # The old broken code would produce 6 bytes: [92, 117, 50, 48, 49, 52]
        # representing the literal string "\\u2014"
        broken_output = b'\\u2014'

        self.assertNotEqual(result, broken_output,
            "The result should NOT be the literal string '\\u2014'")
        self.assertNotEqual(len(result), 6,
            "The result should NOT be 6 bytes (the old broken behavior)")

        # The correct output should be 3 bytes: [226, 128, 148]
        # representing the UTF-8 encoding of the em dash character
        self.assertEqual(len(result), 3,
            "The result should be 3 bytes (UTF-8 encoding of em dash)")
        self.assertEqual(list(result), [226, 128, 148],
            "The byte values should be [226, 128, 148] for UTF-8 em dash")


if __name__ == '__main__':
    unittest.main()