""" Test Proper De-Encapsulation of files
"""

import unittest
import quopri # Decode MIME quoted-printable data
from os.path import join
from lxml.html.diff import InsensitiveSequenceMatcher, tokenize
from RTFDE.deencapsulate import DeEncapsulator

## Directory with test data, independent of current working directory
from tests.test_utils import DATA_BASE_DIR

class TestHtmlCleanDeEncapsulate(unittest.TestCase):
    """ Test minimal deviation of original and de-encapsulated HTML content.

    After de-encapsulation, the HTML and plain text should differ only minimally from the original HTML or plain text content.
"""

    def test_u_encoded_html(self):
        "Tests that de-encapsulation on u encoded encoded HTML works."
        rtf_path = join(DATA_BASE_DIR, "html", "multiple-encodings.rtf")
        txt_path = join(DATA_BASE_DIR, "html", "multiple-encodings.txt")
        with open(txt_path, 'r') as fp:
            raw_text = fp.read()
            original_text = raw_text
        with open(rtf_path, 'r') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            output_text = rtf_obj.html
        self.compare_html(original_text, output_text)

    def compare_html(self, original_text, output_text):
        """Do a diff of two HTML files.

        Only the text, <img> tags and <a href=***> attributes in the HTML are diffed.
        """
        # We start with a diff of the text tokens alone. This allows us to check that the content is the same (weather or not some non-visible structural elements may have been added/removed/modified)
        old_html_tokens = tokenize(output_text)
        new_html_tokens = tokenize(original_text)
        s = InsensitiveSequenceMatcher(a=old_html_tokens, b=new_html_tokens)
        commands = s.get_opcodes()
        # If the content is the same it will only have one opcode which states that the objects are equal
        self.assertEqual(len(commands), 1)
        self.assertEqual('equal', commands[0][0])
        # Now we do the real test of equality between the original and the de-encapsulated copy
        self.assertEqual(original_text, output_text)

class TestTextCleanDeEncapsulate(unittest.TestCase):
    """ Test minimal deviation of original and de-encapsulated plain text content.

    After de-encapsulation, the plain text should differ only minimally from the original plain text content."""

    def test_japanese_encoded_text(self):
        """ """
        rtf_path = join(DATA_BASE_DIR, "plain_text", "japanese_iso_2022.rtf")
        original_body = "すみません。\n"
        with open(rtf_path, 'r') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            output_text = rtf_obj.text
        self.assertEqual(output_text, original_body)

    def test_quoted_printable(self):
        """Test that encoded text in an original quoted printable message is still quoted when de-encapsulated.

        This test checks that it is STILL NOT IMPLEMENTED. So, if you fix it this test will expose that and we will need to change the test."""
        quote_printable_rtf_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.rtf")
        quote_printable_txt_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.txt")
        with open(quote_printable_txt_path, 'r') as fp:
            raw_text = fp.read()
            original_decoded_text = raw_text
        with open(quote_printable_rtf_path, 'r') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            output_text = rtf_obj.text
        self.assertNotEqual(original_decoded_text, output_text)

    def test_decoded_quoted_printable(self):
        """Test that decoded text in an original quoted printable message is still quoted when de-encapsulated."""
        quote_printable_rtf_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.rtf")
        quote_printable_txt_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.txt")
        charset = "cp1251"
        with open(quote_printable_txt_path, 'r') as fp:
            raw_text = fp.read()
            original_decoded_text = quopri.decodestring(raw_text)
            original_decoded_text = original_decoded_text.decode(charset)
        with open(quote_printable_rtf_path, 'r') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            output_text = rtf_obj.text
        self.assertEqual(original_decoded_text, output_text)

# just in case somebody calls this file as a script
if __name__ == '__main__':
    unittest.main()
