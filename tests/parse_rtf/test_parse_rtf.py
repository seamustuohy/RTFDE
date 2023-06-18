"""Test proper parsing of RTF files

Ensure that:
- Correct RTF data doesn't raise any errors.
- Malformed RTF data fails to parse and is described helpfully
- Malformed encapsulated RTF data fails to parse and is described helpfully
- RTF parsing captures the correct data
"""

import unittest
import logging
from os.path import join
from RTFDE.exceptions import MalformedRtf, MalformedEncapsulatedRtf, NotEncapsulatedRtf
from RTFDE.deencapsulate import DeEncapsulator
from RTFDE.utils import encode_escaped_control_chars
from RTFDE.text_extraction import get_python_codec
from RTFDE.text_extraction import TextDecoder

from tests.test_utils import DATA_BASE_DIR
from lark import logger as lark_logger

class TestParseRtf(unittest.TestCase):
    """Test proper parsing of RTF files

Ensure that:
    - Correct RTF data doesn't raise any errors.
    - Malformed RTF data fails to parse and is described helpfully
    - Malformed encapsulated RTF data fails to parse and is described helpfully
    - RTF parsing captures the correct data
    """


    def test_get_first_20_header_control_words(self):
        """ Check that _get_header_control_words__before_first_group gets the first 20 control words of the RTF data or all the tokens which occur before the first group (whichever comes first.)"""
        template_path =  join(DATA_BASE_DIR,
                                          "rtf_parsing",
                                          "from_header_template.rtf")
        # Has 20 control words
        ctrl_words = (b"\\deff0"*16) + b"\\fromhtml1"
        rtf = self.replace_text_in_template(template_path, ctrl_words)
        output = self.run_parsing(rtf)
        ctrl_wds = output.get_header_control_words_before_first_group()
        ctrl_wds =[i.value.strip() for i in ctrl_wds]
        correct_ctrl = [b'\\rtf1',
                        b'\\ansi',
                        b'\\ansicpg1252',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\deff0',
                        b'\\fromhtml1']
        self.assertEqual(ctrl_wds, correct_ctrl)

        # group comes before 20 control words
        ctrl_words = (b"\\deff0"*5) + b"\\fromhtml1 \\deff0" + b'{\colortbl\red0\green0\blue0;\red5\green99\blue193;}'
        rtf = self.replace_text_in_template(template_path, ctrl_words)
        output = self.run_parsing(rtf)
        ctrl_wds = output.get_header_control_words_before_first_group()
        ctrl_wds = [i.value.strip() for i in ctrl_wds]
        correct_ctrl = [b'\\rtf1', b'\\ansi', b'\\ansicpg1252', b'\\deff0', b'\\deff0', b'\\deff0', b'\\deff0', b'\\deff0', b'\\fromhtml1', b'\\deff0']
        self.assertEqual(ctrl_wds, correct_ctrl)

        # fromhtml header parsing not affected by this function
        ctrl_words = b'{\\colortbl\\red0\\green0\\blue0;\\red5\\green99\\blue193;}' + b"\\fromhtml1 \\deff0"
        rtf = self.replace_text_in_template(template_path, ctrl_words)
        # The fromhtml header needs to be in the first 10 tokens. Tokens includes groups in this case. So this should succeed.
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="group before fromhtml in header")

    def test_codepage_num(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")

        # bad
        bad_charsets = [b"\\ansicpg1234", b"\\ansicpg"]
        for badchar in bad_charsets:
            rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
            rtf = self.replace_text_in_template(None, badchar, rep_str=b"\\ansicpg1252", string=rtf)
            self.check_deencapsulate_validity(rtf,
                                              expect_error=MalformedRtf,
                                              name="bad codepage keyword: {0}".format(badchar))

        # good
        # Supported code pages from https://github.com/decalage2/oletools/blob/master/oletools/common/codepages.py
        # Retrieved on 2020-12-18
        # Doesn't include when it attempts to pull the cpNNN codepage from python
        # utf8 (65001) codepage removed so we can check against fallback to utf8
        # NOTE: oletools supports some codepages which MS doesn't include so those are not included here: (32768, 32769)
        supported_codepage_nums = [37, 708, 709, 710, 870, 1047, 1141, 1201, 10000, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10021, 10029, 10079, 10081, 12000, 12001, 20127, 28591, 28592, 28593, 28594, 28595, 28596, 28597, 28598, 28599, 28603, 28605, 38598, 65000]
        for goodpg in supported_codepage_nums:
            codec = get_python_codec(goodpg)
            self.assertIsInstance(codec, str)
            self.assertNotEqual(codec, 'utf8')

        # Codepage is optional. Therefore a missing codepage number is fine.
        rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
        rtf = self.replace_text_in_template(None, b"", rep_str=b"\\ansicpg1252", string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="Ansi codepage num is optional")

    def test_charset_header(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")

        # Bad charset
        bad_charsets = [b"\\ANSI", b"ansi", b"\\PC", b"\\osx"]
        for badchar in bad_charsets:
            rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
            rtf = self.replace_text_in_template(None, badchar, rep_str=b"\\ansi", string=rtf)
            self.check_deencapsulate_validity(rtf,
                                              expect_error=MalformedRtf,
                                              name="bad charset keyword: {0}".format(badchar))

        # Good charset
        # included \\ after the charset keyword to ensure we don't capture the \\ansicpg
        good_charsets = [b"\\ansi\\", b"\\mac\\", b"\\pc\\", b"\\pca\\"]
        for goodchar in good_charsets:
            rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
            rtf = self.replace_text_in_template(None, goodchar, rep_str=b"\\ansi\\", string=rtf)
            self.check_deencapsulate_validity(rtf,
                                              expect_error=None,
                                              name="Good charset keyword: {0}".format(goodchar))

        # group before charset
        new_front = b'{\\rtf1{\\colortbl\\red0\\green0\\blue0;\\red5\\green99\\blue193;}'
        rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
        rtf = new_front + rtf[6:] # Replaces `{\\rtf1`
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="no groups before charset")

        # Missing
        rtf = self.replace_text_in_template(template_path, b"\\fromhtml1")
        rtf = self.replace_text_in_template(None, b"\\", rep_str=b"\\ansi\\", string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="missing charset")
        # Test missing using default fallback to ansi
        output = self.run_parsing(rtf)
        charset = output.validate_charset(fallback_to_default=True)
        self.assertEqual(b"\\ansi", charset)

    def test_get_python_codec(self):
        """Test getting correct python codec."""
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")
        base = self.replace_text_in_template(template_path, b"\\fromhtml1")
        # Big-5
        big5string = b'\xb3o\xacO\xa4@\xad\xd3\xa4\xe5\xa5\xbb\xa6r\xb2\xc5\xa6\xea\xa1C'
        rtf = self.replace_text_in_template(None,
                                       replacement=b"\\ansicpg10002",
                                       rep_str=b"\\ansicpg1252",
                                       string=base)

        output = self.run_parsing(rtf)
        # output.validate_encapsulation()
        # charset = output._validate_charset()
        ansicpg_header = output.get_ansicpg_header()
        possible_cpg_num = int(ansicpg_header.value.strip()[8:])
        text_codec = get_python_codec(possible_cpg_num)
        big5string.decode(text_codec)
        self.assertEqual(text_codec, "big5")
        self.assertEqual(big5string.decode(text_codec),
                         '這是一個文本字符串。')
        # Hebrew
        hebrew = b'\xe6\xe4\xe5 \xee\xe7\xf8\xe5\xe6\xfa \xe8\xf7\xf1\xe8.'
        rtf = self.replace_text_in_template(None,
                                       replacement=b"\\ansicpg10005",
                                       rep_str=b"\\ansicpg1252",
                                       string=base)
        output = self.run_parsing(rtf)
        ansicpg_header = output.get_ansicpg_header()
        possible_cpg_num = int(ansicpg_header.value.strip()[8:])
        text_codec = get_python_codec(possible_cpg_num)
        self.assertEqual(text_codec, "hebrew")
        self.assertEqual(hebrew.decode(text_codec), "זהו מחרוזת טקסט.")


    def test_from_header_html(self):
        """ check that a basic fromhtml header works."""
        from_html =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_text_in_template(from_html, b"\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="working fromheaderhtml")

    def test_from_header_text(self):
        """Check that a basic fromtext header works."""
        from_text =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_text_in_template(from_text, b"\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="working fromheader text")

    def test_missing_from_header(self):
        """Ensure that if a from header isn't present we don't parse the file."""
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_text_in_template(missing_from, b"")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=NotEncapsulatedRtf,
                                          name="missing fromheader text")

        missing_but_one_in_body =  join(DATA_BASE_DIR,
                                     "rtf_parsing",
                                     "from_header_template.rtf")
        rtf = self.replace_text_in_template(missing_but_one_in_body, b"")
        rtf = self.replace_text_in_template(None, b"\\fromtext",
                                       rep_str=b"INSERT_BODY_TEXT_HERE",
                                       string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=NotEncapsulatedRtf,
                                          name="Missing from header, but one far later.")

    def test_multiple_from_headers(self):
        """Test what happens when you have multiple FROM (fromhtml1 or fromtext) headers."""
        multiple_from_html =  join(DATA_BASE_DIR,
                                   "rtf_parsing",
                                   "from_header_template.rtf")
        rtf = self.replace_text_in_template(multiple_from_html, b"\\fromhtml1\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        multiple_from_html_first =  join(DATA_BASE_DIR,
                                         "rtf_parsing",
                                         "from_header_template.rtf")
        rtf = self.replace_text_in_template(multiple_from_html_first, b"\\fromhtml1\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        multiple_from_txt_first =  join(DATA_BASE_DIR,
                                        "rtf_parsing",
                                        "from_header_template.rtf")
        rtf = self.replace_text_in_template(multiple_from_txt_first, b"\\fromtext\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

    def test_from_header_before_rtf(self):
        """Check that this fails. """
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_text_in_template(missing_from, b"")
        # Append a new curly and the control word to the start of the rtf file
        # TODO: Fix this array use on a bytes object
        rtf = b"{\\fromhtml1" + rtf[1:]
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="from header before magic")

    def test_broken_magic(self):
        """Ensure that if a from header is before rtf1 that we fail."""
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_text_in_template(missing_from, b"\\fromhtml1")
        # Append a new curly and broken rtf to the start of the rtf file
        # TODO: Fix this array use on a bytes object
        rtf_no_one = b"{\\rtf" + rtf[6:] # Removes `{\\rtf1`
        self.check_deencapsulate_validity(rtf_no_one,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")
        # TODO: Fix this array use on a bytes object
        rtf_two = b"{\\rtf2" + rtf[6:]
        self.check_deencapsulate_validity(rtf_two,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")
        # TODO: Fix this array use on a bytes object
        RTF = b"{\\RTF1" + rtf[6:]
        self.check_deencapsulate_validity(RTF,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")
        # TODO: Fix this array use on a bytes object
        PiRTF = b"{\\ARRRRRR-TEEE-FFF" + rtf[6:] # Because Pirates
        self.check_deencapsulate_validity(PiRTF,
                                          expect_error=MalformedRtf,
                                          name="Ahoy, matey! this here file magic be broken")


    def test_fonttble_too_early(self):
        """fail when fonttable is before the fromhtml keyword
        - fail fonttble
        - correctly extract the header type
        - with multiple header vals (one in header and one string later on)
        """
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")

        early_font_table = b'{\\fonttbl\n{\\f0\\fswiss Arial;}\n{\\f1\\fmodern Courier New;}\n{\\f2\\fnil\\fcharset2 Symbol;}\n{\\f3\\fmodern\\fcharset0 Courier New;}}' + b"\\fromhtml1 \\deff0"
        rtf = self.replace_text_in_template(template_path, early_font_table)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="fonttable before fromhtml in header")

    def test_missing_fonttable(self):
        """fail when fonttable is missing"""
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "font_table_template.rtf")

        no_font_table = b""
        rtf = self.replace_text_in_template(template_path,
                                            no_font_table,
                                            rep_str=b"REPLACE_FONT_TABLE_HERE")
        NA = b"REPLACE_FONT_TABLE_HERE"
        default = b"""{\\fonttbl
{\\f0\\fswiss Arial;}
{\\f1\\fmodern Courier New;}
{\\f2\\fnil\\fcharset2 Symbol;}
{\\f3\\fmodern\\fcharset0 Courier New;}}"""
        self.check_deencapsulate_validity(rtf,
                                          expect_error=ValueError,
                                          name="fonttable Missing")
                                          # print_error=True)

    def test_extracted_correct_from_header(self):
        """
        - correctly extract the header type
        - with multiple header vals (one in header and one string in body of)
        """
        template_data =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_text_in_template(template_data, b"\\fromhtml1")
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        self.assertEqual('html', output.get_content_type())

        rtf = self.replace_text_in_template(template_data, b"\\fromtext")
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        self.assertEqual('text', output.get_content_type())

         # Try with them back to back. First should win.
        rtf = self.replace_text_in_template(template_data, b"\\fromtext\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        rtf = self.replace_text_in_template(template_data, b"\\fromhtml1\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

    def test_parse_tilde_control_chars(self):
        """Correctly parse control chars
        """
        path =  join(DATA_BASE_DIR,
                     "rtf_parsing",
                     "control_chars.rtf")
        if path is not None:
            with open(path, 'rb') as fp:
                rtf = fp.read()
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="Parse the tilde the \~ command char.")

    def test_parse_spaces_in_own_groups(self):
        """Correctly parse spaces when in their own groups
        """
        path =  join(DATA_BASE_DIR,
                     "rtf_parsing",
                     "five_spaces.rtf")
        if path is not None:
            with open(path, 'rb') as fp:
                rtf = fp.read()
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="Parse spaces in their own groups.")
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        # self.maxDiff = None
        self.assertEqual(b'INSERT_BODY_TEXT_HERE     ', output.text)

    def test_parse_multiple_features(self):
        """Correctly parse spaces when in their own groups
        """
        path =  join(DATA_BASE_DIR,
                     "rtf_parsing",
                     "encapsulated_example.rtf")
        htmlpath =  join(DATA_BASE_DIR,
                        "rtf_parsing",
                        "encapsulated_example.html")

        if path is not None:
            with open(path, 'rb') as fp:
                rtf = fp.read()
        if htmlpath is not None:
            with open(htmlpath, 'rb') as fp:
                html = fp.read()

        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          print_error=True,
                                          name="Test parse multiple features.")
        self.maxDiff = None
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        # print("RUNNING DIFF")
        # print(repr(html))
        # The CR+LF newlines should not match.
        self.assertNotEqual(html, output.html)
        # The LF newlines should be replaced.
        html = html.replace(b'\r\n', b'\n')
        self.assertEqual(html, output.html)


    def debug_error(self, err):
        print("FOUND ERROR")
        # print(dir(err))
        # print(err)
        # print(err.start)
        # print(err.considered_rules)
        # print(err.state)
        # print(dir(err.state))
        print("Current stack of tokens")
        # print(err.state.state_stack)
        # print(err.state.value_stack)
        for i in err.state.value_stack:
            print(i)
            # print(dir(i))
            # print(len(i))
            # print(type(i))
        # 'lexer', 'parse_conf', 'position', 'state_stack', 'value_stack'
        print(err.token_history)
        # print(err.interactive_parser.lexer_thread )

        print("FOUND ERROR DONE")
        return True

    def replace_text_in_template(self, path, replacement,
                            rep_str=b"REPLACE_FROM_HEADER_HERE",
                            string=None):
        if path is not None:
            with open(path, 'rb') as fp:
                raw_rtf = fp.read()
        else:
            raw_rtf = string
        rep_rtf = raw_rtf.replace(rep_str, replacement)
        return rep_rtf

    def run_parsing(self, rtf):
        output = DeEncapsulator(rtf)
        escaped_rtf = encode_escaped_control_chars(output.raw_rtf)
        output.parse_rtf(escaped_rtf)
        output.get_doc_tree()
        return output

    def check_deencapsulate_validity(self, data,
                                     expect_error=None,
                                     name="test",
                                     print_error=False):
        """Helper to check if a test input raises or doesn't raise an error."""
        found_error = None
        try:
            output = DeEncapsulator(data)
            output.deencapsulate()
        except Exception as _e:
            found_error = _e
            if print_error is True:
                import traceback
                traceback.print_exception(type(found_error),
                                          found_error,
                                          found_error.__traceback__)
        # output.deencapsulate()
        if expect_error is not None:
            if found_error is None:
                self.fail("Expected {} but DeEncapsulator finished without error on {}.".format(expect_error, name))
            if not isinstance(found_error, expect_error):
                self.fail('Unexpected error {} from DeEncapsulator for {}.'.format(found_error, name))
        else:
            if found_error is not None:
                self.fail('Error {} raised by DeEncapsulator for {}, But, it should not have raised an error.'.format(type(found_error), name))


# just in case somebody calls this file as a script
if __name__ == '__main__':
    unittest.main()
