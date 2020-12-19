""" Test proper parsing of input formats.

Ensure that:
- Correct RTF data doesn't raise any errors.
- Garbage data fails verbosely.
- Likely common misuse of the library fails verbosely.
"""

import unittest
from os.path import join
from RTFDE.exceptions import MalformedRtf
from RTFDE.deencapsulate import DeEncapsulator
from tests.test_utils import DATA_BASE_DIR

class TestInputValidity(unittest.TestCase):
    """ Tests basic valid and invalid inputs."""

    def test_valid_rtf_string(self):
        """ Check that a valid encapsulated rtf string returns 0 exit status."""
        quote_printable_rtf_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.rtf")
        with open(quote_printable_rtf_path, 'r') as fp:
            raw_rtf = fp.read()
            self.check_deencapsulate_validity(raw_rtf,
                                              expect_error=None,
                                              name="quoted_printable_01.rtf")

    def test_valid_rtf_bytes(self):
        """ Check that a valid encapsulated rtf byte string returns 0 exit status."""
        quote_printable_rtf_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.rtf")
        with open(quote_printable_rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
            self.check_deencapsulate_validity(raw_rtf,
                                              expect_error=None,
                                              name="quoted_printable_01.rtf")

    def test_invalid_none(self):
        """ Check that passing nothing returns a non-zero exit status."""
        self.check_deencapsulate_validity("",
                                          expect_error=MalformedRtf,
                                          name="empty string")
        self.check_deencapsulate_validity(b"",
                                          expect_error=MalformedRtf,
                                          name="empty byte string")
        self.check_deencapsulate_validity(None,
                                          expect_error=TypeError,
                                          name="None/null object")

    def test_invalid_msg(self):
        """ Check that passing a msg file returns a non-zero exit status."""
        quote_printable_msg_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.msg")
        with open(quote_printable_msg_path, 'rb') as fp:
            raw_msg = fp.read()
            self.check_deencapsulate_validity(raw_msg,
                                              expect_error=TypeError,
                                              name="quoted_printable_01.msg")

    def test_invalid_file_pointer(self):
        """ Check that passing a file pointer to a valid rtf file returns a non-zero exit status."""
        quote_printable_rtf_path = join(DATA_BASE_DIR, "plain_text", "quoted_printable_01.rtf")
        with open(quote_printable_rtf_path, 'rb') as fp:
            self.check_deencapsulate_validity(fp,
                                              expect_error=TypeError,
                                              name="rtf file pointer")

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
                self.fail('Wrong kind of error {} from DeEncapsulator for {}, expected {}.'
                      .format(type(found_error), name, expect_error))


# just in case somebody calls this file as a script
if __name__ == '__main__':
    unittest.main()
