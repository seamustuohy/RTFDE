# -*- coding: utf-8 -*-
#
# This file is part of package name, a package description short.
# Copyright © 2022 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

import difflib
import sys
import re
from typing import Union, AnyStr, Any
#  from Python 3.9 typing.Generator is deprecated in favour of collections.abc.Generator
from collections.abc import Generator
from lark.lexer import Token
from lark.tree import Tree
from lark import Lark


import logging
log = logging.getLogger("RTFDE")

def get_control_parameter_as_hex_strings(control_parameter: Union[str,int]) -> str:
    """Returns the hex encoded value of a .rtf control parameter.

Args:
    control_parameter: (int/str) Int or a string which represents an int.

Returns:
    Zero padded 6 char long hexedecimal string.
"""
    try:
        return f"{control_parameter:#06x}"
    except ValueError:
        # If passed as string convert first
        control_parameter = int(control_parameter)
        return f"{control_parameter:#06x}"

def print_to_tmp_file(data: Union[AnyStr,bytes,bytearray], path: str):
    """Prints binary object to a dump file for quick debugging.

Warning: Not for normal use. Only use when debugging.

Args:
    data (bytes|str): Data to write to path
    path (str): The file path to write data to
    """
    # Be able to print binary objects easily
    if isinstance(data, (bytes, bytearray)) is True:
        open_as = 'wb+'
    else:
        open_as = 'w+'
    with open(path, open_as) as fp:
        original_stdout = sys.stdout
        sys.stdout = fp
        print(data)
        sys.stdout = original_stdout

def encode_escaped_control_chars(raw_text: bytes) -> bytes:
    """Replaces escaped control chars within the text with their RTF encoded versions \\'HH.

Args:
    raw_text (str): string which needs escape characters encoded

Returns:
    A string with escaped control chars
    """
    cleaned = raw_text.replace(b'\\\\', b"\\'5c")
    cleaned = cleaned.replace(b'\\{', b"\\'7b")
    cleaned = cleaned.replace(b'\\}', b"\\'7d")
    return cleaned

def is_codeword_with_numeric_arg(token: Union[Token,Any], codeword: bytes) -> bool:
    """Checks if a Token is a codeword with a numeric argument.

Returns:
    True if a Token is a codeword with a numeric argument. False if not.
"""
    try:
        val = token.value.strip()
        # print(val, codeword)
        if (val.startswith(codeword) and
            val[len(codeword):].isdigit()):
            return True
    except AttributeError:
        return False
    return False

def print_lark_parser_evaluated_grammar(parser):
    """Prints the final evaluated grammar.

Can be useful for debugging possible errors in grammar evaluation.

Args:
    parser (Lark obj): Lark object to extract grammar from.
    """
    if not isinstance(parser, Lark):
        raise ValueError("Requires a Lark object.")
    eq = "="*15
    eq = " " + eq + " "
    print(eq + "RULES" + eq + "\n")
    for i in parser.rules:
        print("    " + i)
    print(eq + "TERMINALS" + eq + "\n")
    for i in parser.terminals:
        print("    " + i)
    print(eq + "IGNORED TOKENS" + eq + "\n")
    for i in parser.ignore_tokens:
        print("    " + i)

def log_validators(data):
    """Log validator logging only if RTFDE.validation_logger set to debug.
    """
    logger = logging.getLogger("RTFDE.validation_logger")
    if logger.level == logging.DEBUG:
        logger.debug(data)

def log_transformations(data):
    """Log transform logging only if RTFDE.transform_logger set to debug.
    """
    logger = logging.getLogger("RTFDE.transform_logger")
    if logger.level == logging.DEBUG:
        logger.debug(data)

def is_logger_on(logger_name, level=logging.DEBUG):
    """Check if a logger is enabled and on debug.
    """
    logger = logging.getLogger(logger_name)
    if logger.level == level:
        return True
    return False

def log_text_extraction(data):
    """Log additional text decoding/encoding logging only if RTFDE.text_extraction set to debug.
    """
    logger = logging.getLogger("RTFDE.text_extraction")
    if logger.level == logging.DEBUG:
        logger.debug(data)

def log_htmlrtf_stripping(data: Token):
    """Log HTMLRTF Stripping logging only if RTFDE.HTMLRTF_Stripping_logger set to debug.

Raises:
    AttributeError: Will occur if you pass this something that is not a token.
"""
    logger = logging.getLogger("RTFDE.HTMLRTF_Stripping_logger")
    if logger.level == logging.DEBUG:
        if not isinstance(data, Token):
            raise AttributeError("HTMLRTF Stripping logger only logs Tokens")
        tok_desc = "HTMLRTF Removed: {value}, {line}, {end_line}, {start_pos}, {end_pos}"
        log_msg = tok_desc.format(value=data.value,
                                  line=data.line,
                                  end_line=data.end_line,
                                  start_pos=data.start_pos,
                                  end_pos = data.end_pos)
        logger.debug(log_msg)

def log_string_diff(original: bytes, revised: bytes, sep: Union[bytes,None] = None):
    """Log diff of two strings. Defaults to splitting by newlines and keeping the ends.

Logs the result in the main RTFDE logger as a debug log. Warning: Only use when debugging as this is too verbose to be used in regular logging.

Args:
    original: The original string
    revised: The changed version of the string
    sep (string): A pattern to split the string by. Uses re.split under the hood. NOTE: Deletes all empty strings before diffing to make the diff more concise.
"""
    log.debug(get_string_diff(original, revised, sep))

def get_string_diff(original: bytes, revised: bytes, sep: Union[bytes,None] = None):
    """Get the diff of two strings. Defaults to splitting by newlines and keeping the ends.

Args:
    original: The original string
    revised: The changed version of the string
    sep (string): A pattern to split the string by. Uses re.split under the hood. NOTE: Deletes all empty strings before diffing to make the diff more concise.

Returns:
    A string object representing the diff of the two strings provided.
"""
    if sep is None:
        orig_split = original.decode().splitlines(keepends=True)
        revised_split = revised.decode().splitlines(keepends=True)
    else:
        original = original.replace(b'\n',b'')
        revised = revised.replace(b'\n',b'')
        orig_split = [i.decode() for i in re.split(sep, original) if i != b'']
        revised_split = [i.decode() for i in re.split(sep, revised) if i != b'']
    return "\n".join(list(difflib.context_diff(orig_split,
                                               revised_split)))

def get_tree_diff(original: Tree, revised: Tree):
    """Get the diff of two trees.

Args:
    original (lark Tree): A lark tree before transformation
    revised (lark Tree): A lark tree after transformation

Returns:
    A string object representing the diff of the two Trees provided.

Example:
    rtf_obj = DeEncapsulator(raw_rtf)
    rtf_obj.deencapsulate()
    transformed_tree = SomeTransformer.transform(rtf_obj.full_tree)
    get_tree_diff(rtf_obj.full_tree, transformed_tree)

    """
    log = logging.getLogger("RTFDE")
    flat_original  = list(flatten_tree(original))
    flat_revised  = list(flatten_tree(revised))
    return "\n".join(list(difflib.context_diff(flat_original,
                                               flat_revised)))
def flatten_tree(tree: Tree) -> Generator:
    """Flatten a lark Tree into a list of repr's of tree objects.

Args:
    tree (lark Tree): A lark tree
"""
    yield f"Tree('{tree.data}')"
    for child in tree.children:
        if isinstance(child, Token):
            yield repr(child)
        elif isinstance(child, Tree):
            for i in flatten_tree(child):
                yield i
        else:
            yield repr(child)

def flatten_tree_to_string_array(tree: Tree) -> Generator:
    """Flatten a lark Tree into a list of repr's of tree objects.

Args:
    tree (lark Tree): A lark tree
"""
    for child in tree.children:
        if isinstance(child, Tree):
            for i in flatten_tree_to_string_array(child):
                yield i
        elif isinstance(child, Token):
            yield child.value
        else:
            yield child

def make_token_replacement(ttype, value, example):
    if isinstance(example, Token):
        fake_tok = Token(ttype,
                        value,
                        start_pos=example.start_pos,
                        end_pos=example.end_pos,
                        line=example.line,
                        end_line=example.end_line,
                        column=example.column,
                        end_column=example.end_column)
    elif isinstance(example, Tree):
        fake_tok = Token(ttype,
                         value,
                         start_pos=example.meta.start_pos,
                         end_pos=example.meta.end_pos,
                         line=example.meta.line,
                         end_line=example.meta.end_line,
                         column=example.meta.column,
                         end_column=example.meta.end_column)

    return fake_tok


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
