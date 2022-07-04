#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of package name, a package description short.
# Copyright © 2022 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

import argparse

import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


def main():
    args = parse_arguments()
    set_logging(args.verbose, args.debug)


def get_control_parameter_as_hex_string(control_parameter):
    """Returns the hex encoded value of a control parameter.

    control_parameter: (int/str) Integer either as an integer or a string which represents an int.
    """
    try:
        return "{0:#06x}".format(control_parameter)
    except ValueError:
        # If passed as string convert first
        return "{0:#06x}".format(int(control_parameter))

def print_to_tmp_file(data, path):
    """Debugging function
    """
    # Be able to print binary objects easily
    if isinstance(data, (bytes, bytearray)) is True:
        open_as = 'wb+'
    else:
        open_as = 'w+'
    with open(path, open_as) as fp:
        import sys
        original_stdout = sys.stdout
        sys.stdout = fp
        print(data)
        sys.stdout = original_stdout

def encode_escaped_control_chars(raw_text):
    """Replaces escaped control chars within the text with their RTF encoded versions \\'HH.
    """
    cleaned = raw_text.replace('\\\\', "\\'5c")
    cleaned = cleaned.replace('\\{', "\\'7b")
    cleaned = cleaned.replace('\\}', "\\'7d")
    return cleaned


# Command Line Functions below this point

def set_logging(verbose=False, debug=False):
    if debug == True:
        log.setLevel("DEBUG")
    elif verbose == True:
        log.setLevel("INFO")

def parse_arguments():
    parser = argparse.ArgumentParser("package name")
    parser.add_argument("--verbose", "-v",
                        help="Turn verbosity on",
                        action='store_true')
    parser.add_argument("--debug", "-d",
                        help="Turn debugging on",
                        action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
