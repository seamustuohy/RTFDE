"""Test proper parsing of RTF files

Ensure that:
- Correct RTF data doesn't raise any errors.
- Malformed RTF data fails to parse and is described helpfully
- Malformed encapsulated RTF data fails to parse and is described helpfully
- RTF parsing captures the correct data
"""

import unittest
from os.path import join
from RTFDE.exceptions import MalformedRtf, MalformedEncapsulatedRtf, NotEncapsulatedRtf
from RTFDE.deencapsulate import DeEncapsulator
from tests.test_utils import DATA_BASE_DIR

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
        ctrl_words = ("\\deff0"*16) + "\\fromhtml1"
        rtf = self.replace_from_header(template_path, ctrl_words)
        output = self.run_parsing(rtf)
        ctrl_wds = output._get_header_control_words_before_first_group()
        ctrl_wds =[i.value for i in ctrl_wds]
        correct_ctrl = ['\\rtf1', '\\ansi', '\\ansicpg1252', '\\deff0', '\\deff0', '\\deff0',
                        '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\deff0',
                        '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\deff0',
                        '\\deff0', '\\fromhtml1']
        self.assertEqual(ctrl_wds, correct_ctrl)

        # group comes before 20 control words
        ctrl_words = ("\\deff0"*5) + "\\fromhtml1 \\deff0" + '{\colortbl\red0\green0\blue0;\red5\green99\blue193;}'
        rtf = self.replace_from_header(template_path, ctrl_words)
        output = self.run_parsing(rtf)
        ctrl_wds = output._get_header_control_words_before_first_group()
        ctrl_wds = [i.value for i in ctrl_wds]
        correct_ctrl = ['\\rtf1', '\\ansi', '\\ansicpg1252', '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\deff0', '\\fromhtml1', '\\deff0']
        self.assertEqual(ctrl_wds, correct_ctrl)

        # fromhtml header parsing not affected by this function
        ctrl_words = '{\\colortbl\\red0\\green0\\blue0;\\red5\\green99\\blue193;}' + "\\fromhtml1 \\deff0"
        rtf = self.replace_from_header(template_path, ctrl_words)
        # The fromhtml header needs to be in the first 10 tokens. Tokens includes groups in this case. So this should succeed.
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="group before fromhtml in header")

    def test_codepage_num(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")

        # bad
        bad_charsets = ["\\ansicpg1234", "\\pccpg1252", "\\ansicpg"]
        for badchar in bad_charsets:
            rtf = self.replace_from_header(template_path, "\\fromhtml1")
            rtf = self.replace_from_header(None, badchar, rep_str="\\ansicpg1252", string=rtf)
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
            rtf = self.replace_from_header(template_path, "\\fromhtml1")
            good_codepage = "\\ansicpg{0}".format(goodpg)
            rtf = self.replace_from_header(None, good_codepage, rep_str="\\ansicpg1252", string=rtf)
            output = self.run_parsing(rtf)
            output._validate_encapsulation()
            codec = output._get_python_codec()
            self.assertIsInstance(codec, str)
            self.assertNotEqual(codec, 'utf8')

        # missing
        rtf = self.replace_from_header(template_path, "\\fromhtml1")
        rtf = self.replace_from_header(None, "", rep_str="\\ansicpg1252", string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="Missing codepage num")

    def test_charset_header(self):
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")

        # Bad charset
        bad_charsets = ["\\ANSI", "ansi", "\\PC", "\\osx"]
        for badchar in bad_charsets:
            rtf = self.replace_from_header(template_path, "\\fromhtml1")
            rtf = self.replace_from_header(None, badchar, rep_str="\\ansi", string=rtf)
            self.check_deencapsulate_validity(rtf,
                                              expect_error=MalformedRtf,
                                              name="bad charset keyword: {0}".format(badchar))

        # Good charset
        # included \\ after the charset keyword to ensure we don't capture the \\ansicpg
        good_charsets = ["\\ansi\\", "\\mac\\", "\\pc\\", "\\pac\\"]
        for goodchar in good_charsets:
            rtf = self.replace_from_header(template_path, "\\fromhtml1")
            rtf = self.replace_from_header(None, goodchar, rep_str="\\ansi\\", string=rtf)
            self.check_deencapsulate_validity(rtf,
                                              expect_error=None,
                                              name="Good charset keyword: {0}".format(goodchar))

        # group before charset
        new_front = '{\\rtf1{\\colortbl\\red0\\green0\\blue0;\\red5\\green99\\blue193;}'
        rtf = self.replace_from_header(template_path, "\\fromhtml1")
        rtf = new_front + rtf[6:] # Replaces `{\\rtf1`
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="no groups before charset")

        # Missing
        rtf = self.replace_from_header(template_path, "\\fromhtml1")
        rtf = self.replace_from_header(None, "\\", rep_str="\\ansi\\", string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="missing charset")
        # Test missing using default fallback to ansi
        output = self.run_parsing(rtf)
        output._validate_encapsulation()
        charset = output._get_charset(fallback_to_default=True)
        self.assertEqual("\\ansi", charset)

    def test_get_python_codec(self):
        """Test getting correct python codec."""
        template_path =  join(DATA_BASE_DIR,
                              "rtf_parsing",
                              "from_header_template.rtf")
        base = self.replace_from_header(template_path, "\\fromhtml1")
        # Big-5
        big5string = b'\xb3o\xacO\xa4@\xad\xd3\xa4\xe5\xa5\xbb\xa6r\xb2\xc5\xa6\xea\xa1C'
        rtf = self.replace_from_header(None,
                                       replacement="\\ansicpg10002",
                                       rep_str="\\ansicpg1252",
                                       string=base)

        output = self.run_parsing(rtf)
        output._validate_encapsulation()
        output.charset = output._get_charset()
        output.text_codec = output._get_python_codec()
        big5string.decode(output.text_codec)
        self.assertEqual(output.text_codec, "big5")
        self.assertEqual(big5string.decode(output.text_codec),
                         '這是一個文本字符串。')
        # Hebrew
        hebrew = b'\xe6\xe4\xe5 \xee\xe7\xf8\xe5\xe6\xfa \xe8\xf7\xf1\xe8.'
        rtf = self.replace_from_header(None,
                                       replacement="\\ansicpg10005",
                                       rep_str="\\ansicpg1252",
                                       string=base)
        output = self.run_parsing(rtf)
        output._validate_encapsulation()
        output.charset = output._get_charset()
        output.text_codec = output._get_python_codec()
        self.assertEqual(output.text_codec, "hebrew")
        self.assertEqual(hebrew.decode(output.text_codec), "זהו מחרוזת טקסט.")


    def test_from_header_html(self):
        """ check that a basic fromhtml header works."""
        from_html =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_from_header(from_html, "\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="working fromheaderhtml")


    def test_from_header_text(self):
        """Check that a basic fromtext header works."""
        from_text =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_from_header(from_text, "\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=None,
                                          name="working fromheader text")

    def test_missing_from_header(self):
        """Ensure that if a from header isn't present we don't parse the file."""
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_from_header(missing_from, "")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=NotEncapsulatedRtf,
                                          name="missing fromheader text")

        missing_but_one_in_body =  join(DATA_BASE_DIR,
                                     "rtf_parsing",
                                     "from_header_template.rtf")
        rtf = self.replace_from_header(missing_but_one_in_body, "")
        rtf = self.replace_from_header(None, "\\fromtext",
                                       rep_str="INSERT_BODY_TEXT_HERE",
                                       string=rtf)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=NotEncapsulatedRtf,
                                          name="Missing from header, but one far later.")

    def test_multiple_from_headers(self):
        """Test what happens when you have multiple FROM (fromhtml1 or fromtext) headers."""
        multiple_from_html =  join(DATA_BASE_DIR,
                                   "rtf_parsing",
                                   "from_header_template.rtf")
        rtf = self.replace_from_header(multiple_from_html, "\\fromhtml1\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        multiple_from_html_first =  join(DATA_BASE_DIR,
                                         "rtf_parsing",
                                         "from_header_template.rtf")
        rtf = self.replace_from_header(multiple_from_html_first, "\\fromhtml1\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        multiple_from_txt_first =  join(DATA_BASE_DIR,
                                        "rtf_parsing",
                                        "from_header_template.rtf")
        rtf = self.replace_from_header(multiple_from_txt_first, "\\fromtext\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

    def test_from_header_before_rtf(self):
        """Check that this fails. """
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_from_header(missing_from, "")
        # Append a new curly and the control word to the start of the rtf file
        rtf = "{\\fromhtml1" + rtf[1:]
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedRtf,
                                          name="from header before magic")

    def test_broken_magic(self):
        """Ensure that if a from header is before rtf1 that we fail."""
        missing_from =  join(DATA_BASE_DIR,
                             "rtf_parsing",
                             "from_header_template.rtf")
        rtf = self.replace_from_header(missing_from, "\\fromhtml1")
        # Append a new curly and broken rtf to the start of the rtf file
        rtf_no_one = "{\\rtf" + rtf[6:] # Removes `{\\rtf1`
        self.check_deencapsulate_validity(rtf_no_one,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")

        rtf_two = "{\\rtf2" + rtf[6:]
        self.check_deencapsulate_validity(rtf_two,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")
        RTF = "{\\RTF1" + rtf[6:]
        self.check_deencapsulate_validity(RTF,
                                          expect_error=MalformedRtf,
                                          name="malformed file magic")
        PiRTF = "{\\ARRRRRR-TEEE-FFF" + rtf[6:] # Because Pirates
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

        early_font_table = '{\\fonttbl\n{\\f0\\fswiss Arial;}\n{\\f1\\fmodern Courier New;}\n{\\f2\\fnil\\fcharset2 Symbol;}\n{\\f3\\fmodern\\fcharset0 Courier New;}}' + "\\fromhtml1 \\deff0"
        rtf = self.replace_from_header(template_path, early_font_table)
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="fonttable before fromhtml in header")

    def test_extracted_correct_from_header(self):
        """
        - correctly extract the header type
        - with multiple header vals (one in header and one string in body of)
        """
        template_data =  join(DATA_BASE_DIR,
                          "rtf_parsing",
                          "from_header_template.rtf")
        rtf = self.replace_from_header(template_data, "\\fromhtml1")
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        self.assertEqual('html', output.get_content_type())

        rtf = self.replace_from_header(template_data, "\\fromtext")
        output = DeEncapsulator(rtf)
        output.deencapsulate()
        self.assertEqual('text', output.get_content_type())

         # Try with them back to back. First should win.
        rtf = self.replace_from_header(template_data, "\\fromtext\\fromhtml1")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")

        rtf = self.replace_from_header(template_data, "\\fromhtml1\\fromtext")
        self.check_deencapsulate_validity(rtf,
                                          expect_error=MalformedEncapsulatedRtf,
                                          name="multiple FROM headers means malformed")


    def replace_from_header(self, path, replacement,
                            rep_str="REPLACE_FROM_HEADER_HERE",
                            string=None):
        if path is not None:
            with open(path, 'r') as fp:
                raw_rtf = fp.read()
        else:
            raw_rtf = string
        rep_rtf = raw_rtf.replace(rep_str, replacement)
        return rep_rtf

    def run_parsing(self, rtf):
        output = DeEncapsulator(rtf)
        output.stripped_rtf = output._strip_htmlrtf_sections()
        output.simplified_rtf = output._simplify_text_for_parsing()
        output.doc_tree = output._parse_rtf()
        return output

    def check_deencapsulate_validity(self, data, expect_error=None, name="test"):
        """Helper to check if a test input raises or doesn't raise an error."""
        found_error = None
        try:
            output = DeEncapsulator(data)
            output.deencapsulate()
        except Exception as _e:
            found_error = _e

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
