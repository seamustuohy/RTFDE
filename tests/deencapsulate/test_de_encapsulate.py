""" Test Proper De-Encapsulation of files
"""

import unittest
import secrets
import quopri # Decode MIME quoted-printable data
from os.path import join, abspath, isfile
from os import walk
from os import environ
from lxml.html.diff import InsensitiveSequenceMatcher, tokenize
from RTFDE.deencapsulate import DeEncapsulator
from RTFDE.utils import encode_escaped_control_chars

from lark.exceptions import UnexpectedToken
## Directory with test data, independent of current working directory
from tests.test_utils import DATA_BASE_DIR

from html.parser import HTMLParser

class ExtractHTMLText(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data
        # Remove to ignore newline differences
        # self.text = self.text.replace("\n"," ")
        # Remove to ignore whitespace differences
        # self.text = ' '.join(self.text.split())

class TestPrivateMsgTestCases(unittest.TestCase):
    """Test against a private folder full of RTF files exported from .msg files.

    This test will run against whatever path is set in the RTFDE_PRIVATE_MSG_FOLDER environment variable. If you do not set this environment variable this test will look for .rtf files in the `tests/test_data/personal_rtf_test_files` folder. If it finds none there it will exit without any error.

    > export RTFDE_PRIVATE_MSG_FOLDER="/path/to/folder/with/messages/"
    > python3 -m unittest discover -v --locals

    If you want to run tests that check the contents of the original HTML file against the encapsulated version you can use the RTFDE_PRIVATE_MSG_OUTPUT_FOLDER environment variable. If you do not set this environment variable this test will look for .html files in the `tests/test_data/personal_rtf_test_output_files` folder. If it does not find a file with the same name as the .rtf file that it is testing it will not attempt to compare it to anything. (`file.rtf` needs a corresponding `file.html`).

    > export RTFDE_PRIVATE_MSG_OUTPUT_FOLDER="/path/to/folder/with/html/outputs/"
    > python3 -m unittest discover -v --locals

    It is important to use the --locals variable for unittest since it will expose the filename where an error occurs alongside the unittest failure. Look for the variable named `FAILING_FILENAME`

    The folder `tests/test_data/personal_rtf_test_files` in the source code repository has been included in the .gitignore to allow developers to safely use it for this purpose.


    See code in `scripts/prep_private_rtf_test_folder.sh` for guidance on how to populate a private test folder with RTF files extracted from a folder full of .msg files.
"""
    def test_private_msg_folder(self):

        try:
            folder_path = environ["RTFDE_PRIVATE_MSG_FOLDER"]
        except KeyError:
            folder_path = join(DATA_BASE_DIR, "personal_rtf_test_files")
        try:
            output_path = environ["RTFDE_PRIVATE_MSG_OUTPUT_FOLDER"]
        except KeyError:
            output_path = join(DATA_BASE_DIR, "personal_rtf_test_output_files")
        for (dirpath, dirnames, filenames) in walk(folder_path):
            for f in filenames:
                if not f.endswith('.rtf'):
                    continue
                else:
                    raw_rtf = None
                    abfpath = join(abspath(dirpath), f)
                    FAILING_FILENAME = f
                    with open(abfpath, 'rb') as fp:
                        raw_rtf = fp.read()
                    rtf_obj = DeEncapsulator(raw_rtf)
                    try:
                        rtf_obj.deencapsulate()
                    except:
                        self.fail(f"\nFailed to deencapsulate test file: {f}")
                    # If output result then compare it
                    html_filename = f.replace('.rtf', '.html')
                    output_to_compare = join(abspath(output_path),
                                             html_filename)
                    if isfile(output_to_compare):
                        with open(output_to_compare, 'rb') as fp:
                            html_output = fp.read()
                        f = ExtractHTMLText()
                        f.feed(html_output.decode())
                        html_output_text = f.text
                        f = ExtractHTMLText()
                        f.feed(rtf_obj.content.decode())
                        rtf_output_text = f.text
                        self.assertEqual(rtf_output_text, html_output_text,
                                         msg=f"\nFailed comparing personal test file: {html_filename}")


class TestBinaryData(unittest.TestCase):
    """Test binary data in RTF files."""

    def test_encoded_bytes_stay_encoded_character(self):
        """Test that any hexbytes that are not encoded into the RTF stay in the bytes returned without being modified."""
        raw_rtf = self.get_small_template()
        bin_data = secrets.token_bytes(1)
        binary_string = b'This test is one string ' + bin_data + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        self.assertEqual(binary_string, rtf_obj.content)
        if not (binary_string == rtf_obj.content):
            with open('/tmp/bin_data_fail_input.bytes', 'wb') as fp:
                fp.write(binary_string)
            with open('/tmp/bin_data_fail_output.bytes', 'wb') as fp:
                fp.write(rtf_obj.content)

    def test_bin_data_captured(self):
        """Tests that binary data is captured.
        """
        # Test one bin string
        raw_rtf = self.get_small_template()
        bin_data = secrets.token_bytes(20)
        binary_string = b'This test is one string \\bin20' + bin_data + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)

        self.assertIsNotNone(rtf_obj.found_binary)
        self.assertEqual(b'This test is one string that is it.',
                         rtf_obj.content)
        # Proove that the stripped data contains the bin_data at the right place.
        # re_built_string = rtf_obj.content[:]
        bin_dat = rtf_obj.found_binary[0]
        self.assertEqual(bin_dat['start_pos'], 216)
        self.assertEqual(bin_dat['end_pos'], 242)
        self.assertEqual(bin_dat['bin_start_pos'], 222)
        self.assertEqual(bin_dat['bytes'], bin_data)
        self.assertEqual(bin_dat['ctrl_char'][0], b'\\bin')
        self.assertEqual(bin_dat['ctrl_char'][1], b'20')

        # Make sure spaces after the control char are handled correctly
        binary_string = b'This test is one string \\bin20 ' + bin_data + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        bin_dat = rtf_obj.found_binary[0]
        self.assertEqual(bin_dat['bytes'], bin_data)
        self.assertEqual(bin_dat['ctrl_char'][1], b'20')
        self.assertEqual(bin_dat['start_pos'], 216)
        self.assertEqual(bin_dat['end_pos'], 243)
        self.assertEqual(bin_dat['bin_start_pos'], 223)

        # Test multiple bin string in an rtf file
        bin_addition = b' and more \\bin20 ' + bin_data
        bin_addition = bin_addition*5
        binary_string = b'This test is one string ' + bin_addition + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        self.assertEqual(len(rtf_obj.found_binary), 5)

        # Test bin with negative params are ignored as they are invalid (i.e. \\bin-1234)
        binary_string = b'This test is one string \\bin-20 ' + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        with self.assertRaises(AttributeError):
            _test = rtf_obj.found_binary

        # Test bin with no params are ignored as they are invalid
        binary_string = b'This test is one string \\bin ' + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        with self.assertRaises(AttributeError):
            _test = rtf_obj.found_binary

        # Test bin with 0 length params only include 0 length bytes (i.e. \\bin0 AND \\bin00000000 )
        binary_string = b'This test is one string \\bin0 \\bin0000000' + b'that is it.'
        rep_rtf = raw_rtf.replace(b"REPLACE_ME", binary_string)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        self.assertEqual(len(rtf_obj.found_binary), 2)
        for byte_obj in rtf_obj.found_binary:
            self.assertEqual(byte_obj['bytes'], b'')


    def deencapsulate_string(self, raw_rtf):
        rtf_obj = DeEncapsulator(raw_rtf)
        rtf_obj.deencapsulate()
        return rtf_obj

    def get_small_template(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "small_template.rtf")
        with open(template_path, 'rb') as fp:
            raw_rtf = fp.read()
        return raw_rtf

class TestTextCleanDeEncapsulate(unittest.TestCase):
    """ Test minimal deviation of original and de-encapsulated plain text content.

    After de-encapsulation, the plain text should differ only minimally from the original plain text content."""

    def test_japanese_encoded_text(self):
        """ """
        rtf_path = join(DATA_BASE_DIR, "plain_text", "japanese_iso_2022.rtf")
        original_body = "すみません。\n".encode()
        with open(rtf_path, 'rb') as fp:
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
        with open(quote_printable_txt_path, 'rb') as fp:
            raw_text = fp.read()
            original_decoded_text = raw_text
        with open(quote_printable_rtf_path, 'rb') as fp:
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
        with open(quote_printable_txt_path, 'rb') as fp:
            raw_text = fp.read()
            original_decoded_text = quopri.decodestring(raw_text)
            original_decoded_text = original_decoded_text.decode(charset)
        with open(quote_printable_rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            output_text = rtf_obj.text
        self.assertEqual(original_decoded_text, output_text.decode())



class TestTextDecoding(unittest.TestCase):
    """Test text decoding code"""

    def test_theta(self):
        """ """
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "theta.rtf")
        original_body = '  ф\n'.encode()
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            # print(rtf_obj.full_tree)
            output_text = rtf_obj.text
        # print(repr(output_text))
        self.assertEqual(output_text, original_body)

    def test_translated_by(self):
        """ """
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "translated_by.rtf")
        original_body = 'ترجمة: سمير المجذوب\n'.encode()
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
            # print(rtf_obj.full_tree)
            output_text = rtf_obj.text
        # print(repr(output_text))
        self.assertEqual(output_text, original_body)


    def test_unicode_decoding(self):
        """ """
        # print("\n")
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "surrogates.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        self.assertTrue("😊".encode() in rtf_obj.content)
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "surrogate_pairs.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        correct_repr = 'Ǣ?\nǢ\n😊\n😊??\n😊\n'.encode()
        # print(correct_repr)
        # print(rtf_obj.content)
        self.assertEqual(correct_repr, rtf_obj.content)

        # Test that non unicode chars do not decode
        from RTFDE.text_extraction import unicode_escape_to_chr
        surh = b"\\u-10179"
        surl = b"\\u-8694"
        bad_encodings = [
            b"0x000000A9",
            b"0x00A9",
            b"0xC2 0xA9",
            b"&copy;",
            b"&#xA9;",
            b"&#169;"
        ]
        for bad in bad_encodings:
            with self.assertRaises(ValueError):
                unicode_escape_to_chr(bad)
        surrogate_encodings = [b"\\u-10179", b"\\u-8694"]
        for sur in surrogate_encodings:
            self.assertIsInstance(unicode_escape_to_chr(sur), str)


    def test_surrogate_in_htmlrtf(self):
        """Don't show surrogate text within htmlrtf block."""
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "surrogate_pairs_02.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        correct_repr = b'&#128522;'
        self.assertEqual(correct_repr, rtf_obj.content)
        #print(rtf_obj.content)

    def test_surrogate_without_16bitsigned(self):
        """Test surrogate which doesn't use a 16 signed integer."""
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "surrogate_pairs_03.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        #print(rtf_obj.content)
        correct_repr =  b'&#128522;'
        self.assertEqual(correct_repr, rtf_obj.content)
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "surrogate_pairs_04.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        correct_repr = b'&#128522; \xf0\x9f\x93\x9e'
        self.assertEqual(correct_repr, rtf_obj.content)

    def test_hexencoded(self):
        original_body = '【 This is a test 】'.encode()
        raw_rtf = self.get_small_template()
        # print(raw_rtf)
        # Add fontdef
        font_def = b"""{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}{\\f1\\fswiss\\fcharset128 "PMingLiU";}{\\f2\\fnil\\fcharset1 Arial;}}"""
        base = b"""{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}"""
        new_rtf = raw_rtf.replace(base, font_def)
        # print(new_rtf)
        # Add hec encoded item
        hex_encoded_text = b"""{\\lang1028 \\f1 \\'81\\'79} This is a test {\\lang1028 \\f1 \\'81\\'7a}"""
        rep_rtf = new_rtf.replace(b"REPLACE_ME", hex_encoded_text)
        # print(rep_rtf)
        rtf_obj = self.deencapsulate_string(rep_rtf)
        # rtf_obj.deencapsulate()
        output_text = rtf_obj.content
        # 'not a valid ANSI representation'
        self.assertEqual(output_text, original_body)
        # print(repr(output_text))
        # print(repr(rtf_obj.content))

    def text_hexencode_as_replacement(self):
        """test that unicode text with hex encoded replacement works."""
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "unicode_HH_replacement.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        correct_repr = b'&#128522;'
        self.assertEqual(correct_repr, rtf_obj.content)
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "unicode_HH_replacement_01.rtf")
        rtf_obj = self.deencapsulate(rtf_path)
        correct_repr = b'&#128522; \xf0\x9f\x93\x9e'
        self.assertEqual(correct_repr, rtf_obj.content)

    def test_windows_950_codec(self):
        """Windows 950 codec's currently fail. Ensure that they still fail in tests so we can identify when the underlying libraries fix this.

        https://github.com/seamustuohy/RTFDE/issues/19
        """
        rtf_path = join(DATA_BASE_DIR, "rtf_parsing", "windows_950.rtf")
        # Word successfully parses this, showing "Hello" followed by a space then a single character, though it's either one it doesn't know how to render or is meant to look like a box.
        original_body = "Hello ??" # TODO: Fix once we know what the char is.
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            with self.assertRaises(UnicodeDecodeError):
                rtf_obj.deencapsulate()

    def test_font_table_variation(self):
        from RTFDE.text_extraction import get_font_table,parse_font_tree
        raw_rtf = self.get_small_template()
        base = b"""{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}"""

        # Test \\cpg is consistant with fcharset
        base_w_cpg = b"""{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}{\\f2\\cpg1253\\fcharset161 Arial;}}"""
        new_rtf = raw_rtf.replace(base, base_w_cpg)
        rtf_obj = self.full_tree_from_string(new_rtf)
        raw_font_table = get_font_table(rtf_obj.full_tree.children[1])
        font_table = parse_font_tree(raw_font_table)
        # print(repr(font_table))
        # print(type(font_table))
        self.assertEqual(font_table[b'\\f2'].codepage, 1253)

        # Test \\fcharset takes precedence over \\cpg
        base_w_cpg = b"""{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}{\\f2\\cpg1253\\fcharset204 Arial;}}"""
        new_rtf = raw_rtf.replace(base, base_w_cpg)
        rtf_obj = self.full_tree_from_string(new_rtf)
        raw_font_table = get_font_table(rtf_obj.full_tree.children[1])
        font_table = parse_font_tree(raw_font_table)
        # \\fcharset204 == codepage 1251
        self.assertEqual(font_table[b'\\f2'].codepage, 1251)

    def test_text_decoder(self):
        # TODO
        from RTFDE.text_extraction import TextDecoder
        pass

    def test_default_font(self):
        from RTFDE.text_extraction import get_default_font
        raw_rtf = self.get_small_template()

        # set_font_info with missing deff0
        new_rtf = raw_rtf.replace(b'\\deff0', b'')
        rtf_obj = self.deencapsulate_string(new_rtf)
        # deff0 is not required
        self.assertIsNone(get_default_font(rtf_obj.full_tree))

        # multiple deff0 is fine. Only use the first found
        new_rtf = raw_rtf.replace(b'\\deff0', b'\\deff0\\deff1\\deff2')
        rtf_obj = self.deencapsulate_string(new_rtf)
        self.assertEqual(get_default_font(rtf_obj.full_tree),
                         b'\\f0')




    def test_codepage_num_from_charset(self):
        from RTFDE.text_extraction import get_codepage_num_from_fcharset
        acceptable = [0,128,129,134,136,161,162,177,178,186,204,222,238]
        for i in acceptable:
            self.assertIsNotNone(get_codepage_num_from_fcharset(i))
        acceptable_none = [1,2,255]
        for i in acceptable_none:
            self.assertIsNone(get_codepage_num_from_fcharset(i))
        from random import randrange
        for i in range(20):
            test = randrange(600)
            if test in acceptable:
                continue
            else:
                self.assertIsNone(get_codepage_num_from_fcharset(test))

    def get_small_template(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "small_template.rtf")
        with open(template_path, 'rb') as fp:
            raw_rtf = fp.read()
        return raw_rtf

    def full_tree_from_string(self, raw_rtf):
        rtf_obj = DeEncapsulator(raw_rtf)
        escaped_rtf = encode_escaped_control_chars(rtf_obj.raw_rtf)
        rtf_obj.parse_rtf(escaped_rtf)
        return rtf_obj

    def deencapsulate_string(self, raw_rtf):
        rtf_obj = DeEncapsulator(raw_rtf)
        rtf_obj.deencapsulate()
        return rtf_obj

    def deencapsulate(self, rtf_path):
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            rtf_obj = DeEncapsulator(raw_rtf)
            rtf_obj.deencapsulate()
        return rtf_obj


# just in case somebody calls this file as a script
if __name__ == '__main__':
    unittest.main()
