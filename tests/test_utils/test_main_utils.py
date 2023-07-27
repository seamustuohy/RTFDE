"""Test Utilities
"""

import unittest
import logging
from contextlib import contextmanager
from io import StringIO

from RTFDE.deencapsulate import DeEncapsulator
from RTFDE.utils import log_validators, log_transformations
from RTFDE.utils import encode_escaped_control_chars
from tests.test_utils import DATA_BASE_DIR
from RTFDE.utils import get_tree_diff, log_string_diff
from os.path import join

@contextmanager
def capture_log(logger):
    for i in logger.handlers:
        logger.removeHandler(i)
    stream = StringIO()
    strm_handler = logging.StreamHandler(stream)
    f = '%(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(f)
    strm_handler.setFormatter(formatter)
    logger.addHandler(strm_handler)
    logger.propagate = False
    yield stream

def get_logger_defaults(logger):
    defaults = {}
    defaults.setdefault('level', logger.level)
    defaults.setdefault('handlers', logger.handlers)
    defaults.setdefault('propagate', logger.propagate)
    return defaults

def set_logger_defaults(logger, defaults):
    defaults = {}
    logger.level = defaults.get('level', logging.NOTSET)
    logger.handlers = defaults.get('handlers', [])
    logger.propagate = defaults.get('propagate', True)


class TestLogging(unittest.TestCase):
    """Test that custom logging is working
    """

    def test_validators(self):
        logger = logging.getLogger("RTFDE.validation_logger")
        defaults = get_logger_defaults(logger)
        data = "we will check validators"

        with capture_log(logger) as log:
            log_validators(data)
        log = log.getvalue()
        self.assertNotIn("RTFDE.transform_logger", log)
        self.assertNotIn("check transformations", log)
        self.assertNotIn("DEBUG", log)

        logger.setLevel(logging.DEBUG)
        with capture_log(logger) as log:
            log_validators(data)
        log = log.getvalue()
        self.assertIn("RTFDE.validation_logger", log)
        self.assertIn("check validators", log)
        self.assertIn("DEBUG", log)
        # Cleaning back up for future tests
        set_logger_defaults(logger, defaults)

    def test_transformations(self):
        logger = logging.getLogger("RTFDE.transform_logger")
        defaults = get_logger_defaults(logger)
        data = "we will check transformations"

        with capture_log(logger) as log:
            log_transformations(data)
        self.assertNotIn("RTFDE.transform_logger", log)
        self.assertNotIn("check transformations", log)
        self.assertNotIn("DEBUG", log)

        logger.setLevel(logging.DEBUG)
        with capture_log(logger) as log:
            log_transformations(data)

        log = log.getvalue()
        self.assertIn("RTFDE.transform_logger", log)
        self.assertIn("check transformations", log)
        self.assertIn("DEBUG", log)
        # Cleaning back up for future tests
        set_logger_defaults(logger, defaults)

    def test_string_diff(self):
        logger = logging.getLogger("RTFDE")
        logger.setLevel(logging.DEBUG)
        rtf_path = join(DATA_BASE_DIR, "plain_text", "test_data.rtf")
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
        mod_rtf = raw_rtf
        mod_rtf = mod_rtf.replace(b'\\fswiss ', b'\\things ')
        mod_rtf = mod_rtf.replace(b'\\blue255', b'\\notblueothernumber')
        # log_string_diff(raw_rtf, mod_rtf)
        print("===========================sep========================")
        with capture_log(logger) as log:
            log_string_diff(raw_rtf, mod_rtf, sep=b'\\{|\\}')
        log = log.getvalue()
        self.assertIn(r"! \f0\fswiss Arial;", log)
        self.assertIn(r"! \f0\things Arial;", log)
        self.assertIn(r"! \colortbl\red0\green0\blue0;\red0\green0\blue255;", log)
        self.assertIn(r"! \colortbl\red0\green0\blue0;\red0\green0\notblueothernumber;", log)


    def test_tree_diff(self):
        rtf_path = join(DATA_BASE_DIR, "plain_text", "test_data.rtf")
        with open(rtf_path, 'rb') as fp:
            raw_rtf = fp.read()
        mod_rtf = raw_rtf
        mod_rtf = mod_rtf.replace(b'\\fswiss ', b'\\things ')
        mod_rtf = mod_rtf.replace(b'\\blue255', b'\\notblueothernumber')
        # Create Trees
        rtf_obj = DeEncapsulator(raw_rtf)
        rtf_obj.deencapsulate()
        mod_rtf_obj = DeEncapsulator(mod_rtf)
        mod_rtf_obj.deencapsulate()
        log = get_tree_diff(rtf_obj.full_tree,
                          mod_rtf_obj.full_tree)
        self.assertIn(r"! Token('CONTROLWORD', b'\\fswiss ')", log)
        self.assertIn(r"! Token('CONTROLWORD', b'\\things ')", log)
        self.assertIn(r"! Token('CONTROLWORD', b'\\blue255')", log)
        self.assertIn(r"! Token('CONTROLWORD', b'\\notblueothernumber')", log)

class TestUtilities(unittest.TestCase):
    """Test that important utilities are working
    """

    def test_encode_escape_chars(self):
        raw_text = r"test\\thing\{stuff\}test".encode()
        converted = encode_escaped_control_chars(raw_text)
        self.assertIn(b"\\'5c", converted)
        self.assertIn(b"\\'7b", converted)
        self.assertIn(b"\\'7d", converted)


def embed():
    import os
    import readline
    import rlcompleter
    import code
    import inspect
    import traceback

    history = os.path.join(os.path.expanduser('~'), '.python_history')
    if os.path.isfile(history):
        readline.read_history_file(history)

    frame = inspect.currentframe().f_back
    namespace = frame.f_locals.copy()
    namespace.update(frame.f_globals)

    readline.set_completer(rlcompleter.Completer(namespace).complete)
    readline.parse_and_bind("tab: complete")

    file = frame.f_code.co_filename
    line = frame.f_lineno
    function = frame.f_code.co_name

    stack = ''.join(traceback.format_stack()[:-1])
    print(stack)
    banner = f" [ {os.path.basename(file)}:{line} in {function}() ]"
    banner += "\n Entering interactive mode (Ctrl-D to exit) ..."
    try:
        code.interact(banner=banner, local=namespace)
    finally:
        readline.write_history_file(history)
