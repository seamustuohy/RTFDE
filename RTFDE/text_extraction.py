# -*- coding: utf-8 -*-
#
# This file is part of RTFDE, a RTF De-Encapsulator.
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

import codecs
import re
from collections import namedtuple
from typing import Union, Any, List, Tuple, Dict

from oletools.common import codepages

from lark.lexer import Token
from lark.tree import Tree

from RTFDE.exceptions import MalformedRtf
from RTFDE.utils import is_codeword_with_numeric_arg
from RTFDE.utils import flatten_tree_to_string_array
from RTFDE.utils import log_text_extraction, is_logger_on

import logging
log = logging.getLogger("RTFDE")

fontdef = namedtuple("fontdef", ["fnum", "codepage", "codec", "fontdef_tree"])


def get_font_table(tree: Tree) -> Tree:
    """Extract the font table group from the first 20 tokens of a .rtf document.

Args:
    tree (Tree): A .rtf document object parsed into a Tree object

Raises:
    ValueError: If no group with a `\\fonttbl` token as its first controlword is found.

Returns:
    {'\\f0': fontdef(fnum='\\f0', codepage=932, codec='cp932', fontdef_tree='{\\f0\\fswiss\\fcharset128 MS PGothic;}'),
    '\\f1': fontdef(fnum='\\f1', codepage=None, codec=None, fontdef_tree='{\\f1\\fmodern MS Gothic;}'),
    '\\f2': fontdef(fnum='\\f2', codepage=None, codec=None, fontdef_tree='{\\f2\\fnil\\fcharset2 Symbol;}'),
    '\\f3': fontdef(fnum='\\f3', codepage=1252, codec='cp1252', fontdef_tree='{\\f3\\fmodern\\fcharset0 Courier New;}'),
    '\\f4': fontdef(fnum='\\f4', codepage=932, codec='cp932', fontdef_tree='{\\f4\\fswiss\\fcharset128 "PMingLiU";}'),
    '\\f5': fontdef(fnum='\\f5', codepage=None, codec=None, fontdef_tree='{\\f5\\fswiss "Amnesty Trade Gothic";}'),
    '\\f6': fontdef(fnum='\\f6', codepage=None, codec=None, fontdef_tree='{\\f6\\fswiss "Arial";}')}
    """
    for item in tree.children[:20]:
        if isinstance(item, Tree):
            try:
                ctrl_value = item.children[1]
            except IndexError as _e:
                continue
            if isinstance(ctrl_value, Token):
                table_type = ctrl_value.value.strip()
                if table_type == b"\\fonttbl":
                    return item
    raise ValueError("No font table found in tree")


def is_font_number(token: Token) -> bool:
    """Checks if an object is a "font number".

Returns:
    True if an object is a "font number" controlword `\\fN`. False if not.

"""
    try:
        if is_codeword_with_numeric_arg(token, b'\\f'):
            return True
    except AttributeError: # pragma: no cover
        return False
    return False

def get_codepage_num_from_fcharset(fcharsetN: int) -> Union[int,None]:
    """Return the codepage to use with a specific fcharsetN.

Args:
    fcharsetN (int): The numeric argument N for a \fcharsetN control word.

Returns:
    (int OR None) Returns the int for a codepage if known. Returns None for unknown charsets or charsets with no corresponding codepage (such as OEM or DEFAULT.)

    """
    # Charset table retrieved on 2022-08-19
    # https://web.archive.org/web/20220819215334/https://docs.microsoft.com/en-us/previous-versions/cc194829%28v=msdn.10%29?redirectedfrom=MSDN
    charsets: dict[int,dict[str,Any]] = {
        0:{"name":"ANSI_CHARSET","hex":"0x00","decimal":0,"id":1252},
        1:{"name":"DEFAULT_CHARSET","hex":"0x01","decimal":1,"id":None},
        2:{"name":"SYMBOL_CHARSET","hex":"0x02","decimal":2,"id":None},
        128:{"name":"SHIFTJIS_CHARSET","hex":"0x80","decimal":128,"id":932},
        129:{"name":"HANGUL_CHARSET","hex":"0x81","decimal":129,"id":949},
        134:{"name":"GB2312_CHARSET","hex":"0x86","decimal":134,"id":936},
        136:{"name":"CHINESEBIG5_CHARSET","hex":"0x88","decimal":136,"id":950},
        161:{"name":"GREEK_CHARSET","hex":"0xA1","decimal":161,"id":1253},
        162:{"name":"TURKISH_CHARSET","hex":"0xA2","decimal":162,"id":1254},
        177:{"name":"HEBREW_CHARSET","hex":"0xB1","decimal":177,"id":1255},
        178:{"name":"ARABIC_CHARSET","hex":"0xB2","decimal":178,"id":1256},
        186:{"name":"BALTIC_CHARSET","hex":"0xBA","decimal":186,"id":1257},
        204:{"name":"RUSSIAN_CHARSET","hex":"0xCC","decimal":204,"id":1251},
        222:{"name":"THAI_CHARSET","hex":"0xDE","decimal":222,"id":874},
        238:{"name":"EE_CHARSET","hex":"0xEE","decimal":238,"id":1250},
        255:{"name":"OEM_CHARSET","hex":"0xFF","decimal":255,"id":None},
}
    if is_logger_on("RTFDE.text_extraction") is True:
        log_text_extraction(f"Getting charset for {fcharsetN}")
    charset = charsets.get(fcharsetN, None)
    if charset is not None:
        charset_id = charset.get('id', None)
        return charset_id
    return None


def get_default_font(tree: Tree) -> Union[str,None]:
    """Extract the font number controlword default font if it exists.

If an RTF file uses a default font, the default font number is specified with the \\deffN control word, which must precede the font-table group.

Args:
    tree (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree object.

Returns:
    The default font control number if it exists from the first `\\deffN`. None if not found.
"""
    deff_gen = tree.scan_values(
        lambda v: is_codeword_with_numeric_arg(v, b'\\deff')
    )
    deff_options = list(deff_gen)
    try:
        # We just want the first \\deffN. It shouldn't be set multiple times.
        deff = deff_options[0]
        deff_num = deff.value[5:]
        return b'\\f' + deff_num
    except IndexError:
        return None

def parse_font_tree(font_tree: Tree) -> dict:
    """Create a font tree dictionary with appropriate codeces to decode text.

Args:
    font_tree (Tree): The .rtf font table object decoded as a tree.

Returns:
    A dictionary which maps font numbers to appropriate python codeces needed to decode text.
"""
    parsed_font_tree = {}
    for tree in font_tree.children:
        if isinstance(tree, Tree):
            fnum = None
            fcharset = None
            cpg_num = None
            for tok in tree.children:
                if is_codeword_with_numeric_arg(tok, b'\\f'):
                    fnum = tok.value
                elif is_codeword_with_numeric_arg(tok, b'\\fcharset'):
                    fchar_num = int(tok.value[9:])
                    fcharset = get_codepage_num_from_fcharset(fchar_num)
                elif is_codeword_with_numeric_arg(tok, b'\\cpg'):
                    cpg_num = int(tok.value[4:])
            if fnum is not None:
                # get the codepage
                codepage_num = None

                if fcharset is not None:
                    try:
                        codepage_num = check_codepage_num(fcharset)
                    except ValueError: # pragma: no cover
                        codepage_num = None
                # if both \\fcharset and \\cpg appear in the font table, \\cpg is ignored.
                if ((codepage_num is None) and (cpg_num is not None)):
                    try:
                        codepage_num = check_codepage_num(cpg_num)
                    except ValueError: # pragma: no cover
                        codepage_num = None
                # Get the appropriate codec
                if codepage_num is not None:
                    codec = get_python_codec(codepage_num)
                else:
                    codec = None
                # Only add if there is a font definition
                tree_str =  b"".join(list(flatten_tree_to_string_array(tree)))
                parsed_font_tree[fnum] = fontdef(fnum, codepage_num, codec, tree_str)
    return parsed_font_tree


def get_python_codec(codepage_num: int) -> str:
    """Returns the python codec needed to decode bytes to unicode.

Args:
    codepage_num (int): A codepage number.

Returns:
    The name of the codec in the Python codec registry. Used as the name for enacoding/decoding.
"""
    text_codec = codepages.codepage2codec(codepage_num)
    log.debug('Found python codec corresponding to code page {0}: {1}'.format(codepage_num, text_codec))
    return text_codec

def check_codepage_num(codepage_num: int) -> int:
    """Provide the codepage number back to you if it is valid.

Args:
    codepage_num (int): A possible codepage number.

Returns:
    The codepage number IF it is a valid codepage number

Raises:
    ValueError: The codepage_num provided isn't a valid codepage number.

"""
    # This keyword should be emitted in the RTF header section right after the \ansi, \mac, \pc or \pca keyword. But, various document tags like \fbids often are thrown all over the header so we have to check the first group of headers for it.
    # Code page names from https://docs.microsoft.com/en-gb/windows/desktop/Intl/code-page-identifiers
    # Retrieved on 2020-12-18
    allowed_codepage_nums = set([37, 437, 500, 708, 709, 710, 720, 737, 775, 850, 852, 855, 857, 858, 860, 861, 862, 863, 864, 865, 866, 869, 870, 874, 875, 932, 936, 949, 950, 1026, 1047, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1200, 1201, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1361, 10000, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10010, 10017, 10021, 10029, 10079, 10081, 10082, 12000, 12001, 20000, 20001, 20002, 20003, 20004, 20005, 20105, 20106, 20107, 20108, 20127, 20261, 20269, 20273, 20277, 20278, 20280, 20284, 20285, 20290, 20297, 20420, 20423, 20424, 20833, 20838, 20866, 20871, 20880, 20905, 20924, 20932, 20936, 20949, 21025, 21027, 21866, 28591, 28592, 28593, 28594, 28595, 28596, 28597, 28598, 28599, 28603, 28605, 29001, 38598, 50220, 50221, 50222, 50225, 50227, 50229, 50930, 50931, 50933, 50935, 50936, 50937, 50939, 51932, 51936, 51949, 51950, 52936, 54936, 57002, 57003, 57004, 57005, 57006, 57007, 57008, 57009, 57010, 57011, 65000, 65001])
    if codepage_num in allowed_codepage_nums:
        return codepage_num
    # Note: If support for a specific codepage ever becomes an issue we can look at add support using the actual code-pages.
    # Conversion tables for codepages can be retrieved from here: https://www.unicode.org/Public/MAPPINGS/VENDORS/MICSFT/
    raise ValueError(f"Unsupported unicode codepage number `{codepage_num}` found in the header")


def validate_ansi_cpg(header: str) -> None:
    """Check an '\\ansicpgNNNN' string to see if the number NNNN is an actual codepage.

Args:
    header (str): The value from the lark `\\ansicpg` CONTROLWORD Token.

Raises:
    MalformedRtf: If the value passed is not a valid ansi codepage.
"""
    try:
        possible_cpg_num = int(header.strip()[8:])
        check_codepage_num(possible_cpg_num)
    except ValueError as _e:
        raise MalformedRtf(f"Unsupported unicode codepage number `{header}` found in the header") from _e


# UNICODE CHARS
def unicode_escape_to_chr(item: bytes) -> str:
    """Convert unicode char from it's decimal to its unicode character representation. From "\\u[-]NNNNN" to the string representing the character whose Unicode code point that decimal represents.

Args:
    item (str): A RTF Escape in the format \\u[-]NNNNN.

Returns:
    The unicode character representation of the identified character

Raises:
    ValueError: The escaped unicode character is not valid.
"""
    try:
        prefix = b'\\u'
        if item.startswith(prefix):
            nnnn = item[len(prefix):]
        else:
            nnnn = item
        nnnn = int(nnnn) # raises ValueError if not int.
    except ValueError as _e:
        raise ValueError(f"`{item}` is not a valid escaped unicode character.") from _e
    if nnnn < 0: # § -NNNNN is a negative integer expressed in decimal digits
        ncr = 65536 + nnnn
    else: # § NNNNN is a positive integer expressed in decimal digits
        ncr = nnnn
    # § HHHH is the hexadecimal equivalent of NNNNN or -NNNNN
    return chr(ncr)

def is_hex_encoded(item: Token) -> bool:
    """Identify if a token contains a HEXENCODED token.
Args:
    item (token): A token to check if it is HEXENCODED.

Return:
    True if HEXENCODED. False if not.
    """
    if isinstance(item, Token):
        if item.type == "HEXENCODED":
            return True
    return False

def is_valid_ANSI_representation_char(item: Token) -> bool:
    """Is token contain a valid ANSI representation string for a Unicode char.

Args:
    item (token): A token to check if it is a valid ANSI representation.

Return:
    True if token is an ansi representation of a unicode char. False if not.
"""
    if isinstance(item, Token):
        # print(f"found TOKEN posssible ansi {repr(item)}")
        if is_hex_encoded(item):
            # print(f"found hex posssible ansi {repr(item)}")
            return True
        if item.type == 'STRING':
            # print(f"found STRING posssible ansi {repr(item)}")
            if not item.value.isspace(): # whitespace doesn't count.
                # print(f"found posssible ansi {repr(item)}")
                return True
            # else:
            #     print(f"found SPACE posssible ansi {repr(item)}")
    # print(f"found NON TOKEN posssible ansi {repr(item)}")
    return False

def is_unicode_encoded(item: Token) -> bool:
    """Is token contain a unicode char.

Args:
    item (token): A token to check if contains a unicode char.

Return:
    True if token contains a unicode char. False if not.
"""
    if isinstance(item, Token):
        if item.type == "UNICODE":
            return True
    return False

def includes_unicode_chars(children: List[Token]) -> bool:
    """Does a list include Tokens which contain unicode characters. Not recursive.

Args:
    children (list): A Tree.children list to check to see if it includes unicode characters.

Returns:
    True if list includes tokens which contain unicode chars. False if not.
"""
    for child in children:
        if is_unicode_encoded(child):
            return True
    return False


def remove_unicode_replacements(children: List[Token],
                                return_ascii_map: bool = True,
                                byte_count: int = 1) -> Union[
                                    Tuple[List[Token], Dict[Token,List[Token]]],
                                    List[Token]]:
    """Remove all unicode replacement characters from a list of Tokens.

Args:
    children (list): A Tree.children list to remove unicode replacement characters from.
    return_ascii_map (bool): On True, have this function return a map of the ASCII token that were removed.
    byte_count (int): The number of bytes corresponding to a given \\uN Unicode character.  A default of 1 should be assumed if no \\uc keyword has been seen in the current or outer scopes.

Returns:
    new_children (list): The list of Tokens with all unicode replacement characters removed.
    ascii_map (dict): All the Tokens which were removed from the provided children list keyed by

"""
    byte_count = 1
    ascii_map: Dict[Token,List[Token]]  = {}
    new_children = []
    removal_map: List[Token] = []
    if is_logger_on("RTFDE.text_extraction") is True:
        log_text_extraction(f"Removing unicode replacements on {repr(children)}")
    for child in children:
        if len(removal_map) > 0:
            if isinstance(child, Token):
                # Delete all spaces between a unicode char and the last ANSI representation
                # print(f"FOUND SPACE STRING with RM: {removal_map}")
                if child.value.isspace():
                    ascii_map.setdefault(removal_map[0], []).append(child)
                    continue
            if is_valid_ANSI_representation_char(child):
                # Found an ansi representation removing unicode char from removal map.
                # print(f"FOUND ASCII STRING {child} to RM with RM: {removal_map}")
                ascii_map.setdefault(removal_map.pop(), []).append(child)
                continue
            elif isinstance(child, Tree) and (
                    (child.data == "string") or (child.data == "hexarray")):
                # print(f"FOUND ASCII STRING {child} with RM: {removal_map}")
                ansi_children = child.children
                new_ansi_children = []
                for aci,ac in enumerate(ansi_children):
                    # print(f"AC CHILD {repr(ac)}")
                    if is_valid_ANSI_representation_char(ac):
                        # print(f"AC CHILD VALID {repr(ac)}")
                        if len(removal_map) > 0:
                            # print(f"AC CHILD MAP >0 {repr(ac)}")
                            # print(f"Popping removal for {repr(ac)}")
                            ascii_map.setdefault(removal_map.pop(), []).append(ac)
                        else:
                            # print(f"AC CHILD MAP < 0 {repr(ac)}")
                            new_ansi_children.append(ac)
                    else:
                        # print(f"AC CHILD NOT VALID {repr(ac)}")
                        new_ansi_children.append(ac)
                # print(f"NEW Children = {new_ansi_children}")
                if new_ansi_children == []:
                    from RTFDE.utils import make_token_replacement
                    # from RTFDE.utils import embed
                    # embed()
                    child = make_token_replacement("STRING", b"", child)
                else:
                    child.children = new_ansi_children
                # print(f"NEW Tree = {child}")
            # else:
                # print(f"FOUND ASCII STRING {child} with RM: {removal_map}")
                # print(f"{repr(child)} not a valid ANSI representation? with RM: {removal_map}")
        # Modify char byte count if we encounter it.
        if is_unicode_char_byte_count(child):
            byte_count = get_unicode_char_byte_count(child)
            # print(f"Changing byte count because {child} to {byte_count}")
        if is_unicode_encoded(child):
            # print(f"Found unicode {child}")
            for j in range(byte_count):
                # Add the unicode key to the removal map once per byte
                # This ensures we remove the right number of ANSI representation chars
                removal_map.append(child)
        new_children.append(child)
    if return_ascii_map is True:
        return new_children, ascii_map
    return new_children


# UNICODE SURROGATE CHARACTERS
def is_surrogate_high_char(item: bytes) -> bool:
    """Check's if chr is a is in the high-surrogate code point rage. "High-surrogate code point: A Unicode code point in the range U+D800 to U+DBFF." High-surrogate also sometimes known as the leading surrogate.

        item (bytes): A bytes representation of a string representing a unicode character. "\\u-10179"
    """
    if item.startswith(b"\\u"):
        item = item[2:]
    if 0xD800 <= ord(chr(65536+int(item))) <= 0xDBFF:
        return True
    # In case unicode is NOT using the 16 bit signed integer
    elif 0xD800 <= int(item) <= 0xDBFF:
        return True
    return False

def is_surrogate_low_char(item: bytes) -> bool:
    """Check's if chr is a is in the low-surrogate code point rage. "Low-surrogate code point: A Unicode code point in the range U+DC00 to U+DFFF."  Low-surrogate also sometimes known as following surrogates.

        item (bytes): A bytes representation of a string representing a unicode character.
    """
    if item.startswith(b"\\u"):
        item = item[2:]
    if 0xDC00 <= ord(chr(65536+int(item))) <= 0xDFFF:
        return True
    # In case unicode is NOT using the 16 bit signed integer
    elif 0xDC00 <= int(item) <= 0xDFFF:
        return True
    return False

def is_surrogate_16bit(item: bytes, cp_range) -> bool:
    """Checks if a unicode char is 16 bit signed integer or the raw unicode char. This should first check if it is a surrogate code using the is_surrogate_XXXX_char functions.

Args:
    item (bytes): A bytes representation of a string representing a unicode character.
    cp_range (str): ['low' OR 'high'] The code point range (low-surrogate or high-surrogate).
    """
    if cp_range == 'low':
        if 0xDC00 <= ord(chr(65536+int(item))) <= 0xDFFF:
            return True
    elif cp_range == 'high':
        if 0xD800 <= ord(chr(65536+int(item))) <= 0xDBFF:
            return True
    else:
        raise ValueError("cp_range must be either 'low' or 'high'")
    return False


def is_surrogate_pair(first: bytes, second: bytes) -> bool:
    """Check if a pair of unicode characters are a surrogate pair. Must be passed in the correct order.

Args:
    first (bytes): A bytes representation of a string representing the high-order byte in a surrogate char.
    second (bytes): A bytes representation of a string representing the low-order byte in a surrogate char.
    """
    if is_surrogate_high_char(first):
        if is_surrogate_low_char(second):
            return True
        else:
            log.info("RTFDE encountered a standalone high-surrogate point without a corresponding low-surrogate. Standalone surrogate code points have either a high surrogate without an adjacent low surrogate, or vice versa. These code points are invalid and are not supported. Their behavior is undefined. Codepoints encountered: {0}, {1}".format(first, second))
    return False

def decode_surrogate_pair(high: bytes, low: bytes, encoding: str ='utf-16-le') -> bytes:
    """ Convert a pair of surrogate chars into the corresponding utf-16 encoded text string they should represent.

Args:
        high (bytes): the high-surrogate code point
        low (bytes): the low-surrogate code point
        encoding (str): The encoding to apply to the final value. Defaults to 'utf-16-le' because:  Microsoft uses UTF-16, little endian byte order. ( https://learn.microsoft.com/en-us/windows/win32/intl/using-byte-order-marks ) The Msg format is a Microsoft standard. Therefore, man is mortal.
    """
    # Equation for turning surrogate pairs into a unicode scalar value which be used with utl-16 can ONLY found in Unicode 3.0.0 standard.
    # Unicode scalar value means the same thing as "code position" or "code point"
     # https://www.unicode.org/versions/Unicode3.0.0/
     # section 3.7 https://www.unicode.org/versions/Unicode3.0.0/ch03.pdf#page=9
    if high.startswith(b"\\u"):
        high = high[2:]
    if low.startswith(b"\\u"):
        low = low[2:]
    if is_surrogate_16bit(high, "high"):
        char_high = chr(65536+int(high))
    else:
        char_high = chr(int(high))
    if is_surrogate_16bit(low, "low"):
        char_low = chr(65536+int(low))
    else:
        char_low = chr(int(low))
    unicode_scalar_value = ((ord(char_high) - 0xD800) * 0x400) + (ord(char_low) - 0xDC00) + 0x10000
    unicode_bytes = chr(unicode_scalar_value).encode(encoding)
    return unicode_bytes.decode(encoding).encode()

def merge_surrogate_chars(children,
                          ascii_map,
                          use_ASCII_alternatives_on_unicode_decode_failure = False):
    """


Raises:
    ValueError:  A Standalone high-surrogate was found. High surrogate followed by a illegal low-surrogate character.
    """
    surrogate_start = None
    surrogate_high = None
    for i,c in enumerate(children):
        if isinstance(c, Tree):
            continue
        if is_unicode_encoded(c):
            if is_surrogate_high_char(c.value):
                surrogate_start = i
                surrogate_high = c
            elif surrogate_start is not None:
                if is_surrogate_low_char(c.value):
                    surrogate_low = c
                    try:
                        surrogate_value = decode_surrogate_pair(surrogate_high.value,
                                                                surrogate_low.value)
                        # Convert into STRING token
                        surrogate_tok = Token('STRING',
                                              surrogate_value,
                                              start_pos=surrogate_high.start_pos,
                                              end_pos=surrogate_low.end_pos,
                                              line=surrogate_high.line,
                                              end_line=surrogate_low.end_line,
                                              column=surrogate_high.column,
                                              end_column=surrogate_low.end_column)
                        children[surrogate_start] = surrogate_tok
                        blank_tok = Token('STRING',
                                          b"",
                                          start_pos=surrogate_high.start_pos+1,
                                          end_pos=surrogate_low.end_pos+1,
                                          line=surrogate_high.line,
                                          end_line=surrogate_low.end_line,
                                          column=surrogate_high.column,
                                          end_column=surrogate_low.end_column)
                        children[i] = blank_tok
                        surrogate_start = None
                        surrogate_high = None
                    except UnicodeDecodeError as _e:
                        if use_ASCII_alternatives_on_unicode_decode_failure is True:
                            children[surrogate_start] = b"".join([i.value for i in ascii_map[surrogate_high]])
                            children[i] = b"".join([i.value for i in ascii_map[surrogate_low]])
                        else:
                            raise _e
                else:
                    log.info("RTFDE encountered a standalone high-surrogate point without a corresponding low-surrogate. Standalone surrogate code points have either a high surrogate without an adjacent low surrogate, or vice versa. These code points are invalid and are not supported. Their behavior is undefined. Codepoints encountered: {0}, {1}".format(surrogate_high, surrogate_low))
                    if use_ASCII_alternatives_on_unicode_decode_failure is True:
                        children[surrogate_start] = b"".join([i.value for i in ascii_map[surrogate_high]])
                    else:
                        raise ValueError("Standalone high-surrogate found. High surrogate followed by a illegal low-surrogate character.")
    return children



def is_unicode_char_byte_count(item: Token) -> bool:
    if isinstance(item, Token):
        if item.type == "CONTROLWORD":
            if item.value.startswith(b'\\uc'):
                return True
    return False

def get_unicode_char_byte_count(item: Token) -> int:
    item = item.value.decode()
    cur_uc = int(item[3:])
    return cur_uc


# Hex Encoded Chars
def has_hexarray(children: List[Union[Token, Tree]]) -> bool:
    """Checks if an tree's children includes a hexarray tree.

    children (array): the children object from a tree.
    """
    for item in children:
        if is_hexarray(item):
            return True
    return False

def is_hexarray(item):
    """Checks if an item is a hexarray tree.

    item (Tree or Token): an item to check to see if its a hex array
    """
    if isinstance(item, Tree):
        if item.data.value == 'hexarray':
            return True
    return False

def get_bytes_from_hex_encoded(item):
    """Convert hex encoded string to bytes.

    item (str): a hex encoded string in format \\'XX
    """
    hexstring = item.replace(b"\\'", b"")
    hex_bytes = bytes.fromhex(hexstring.decode())
    return hex_bytes

def decode_hex_char(item, codec):
    """Decode a bytes object using a specified codec.

    item (bytes): A bytes object.
    codec (str): The name of the codec to use to decode the bytes
    """
    if is_logger_on("RTFDE.text_extraction") is True:
        log_text_extraction("decoding char {0} with font {1}".format(item, codec))
    if codec is None:
        # Default to U.S. Windows default codepage
        codec = 'CP1252'
    decoded = item.decode(codec)
    decoded = decoded.encode()
    if is_logger_on("RTFDE.text_extraction") is True:
        log_text_extraction("char {0} decoded into {1} using codec {2}".format(item, decoded, codec))
    return decoded


class TextDecoder:

    def __init__(self, keep_fontdef=False,
               initial_byte_count=None, use_ASCII_alternatives_on_unicode_decode_failure=False):
        """
        keep_fontdef: (bool) If False (default), will remove fontdef's from object tree once they are processed.
        initial_byte_count: (int) The initial Unicode Character Byte Count. Does not need to be set unless you are only providing a RTF snippet which does not contain the RTF header which sets the  information.
        use_ASCII_alternatives_on_unicode_decode_failure: (bool) If we encounter errors when decoding unicode chars we will use the ASCII alternative since that's what they are included for.

        """
        self.keep_fontdef = keep_fontdef
        self.ucbc = initial_byte_count
        self.use_ASCII_alternatives_on_unicode_decode_failure = use_ASCII_alternatives_on_unicode_decode_failure

        # Font table values set set_font_info
        self.default_font = None
        self.font_stack = []
        self.font_table = {}


    def set_font_info(self, obj: Tree):
        """

        obj (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree.
        """
        self.default_font = get_default_font(obj)
        self.font_stack = [self.default_font]
        raw_fonttbl = get_font_table(obj.children[1])
        self.font_table = parse_font_tree(raw_fonttbl)
        if is_logger_on("RTFDE.text_extraction") is True:
            log_text_extraction(f"FONT TABLE FOUND: {raw_fonttbl}")


    def update_children(self, obj: Tree):
        """

        obj (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree.
        """
        # Reset font info
        self.set_font_info(obj)
        children = obj.children
        obj.children = [i for i in self.iterate_on_children(children)]

    def prep_unicode(self, children: List[Token]):
        if includes_unicode_chars(children):
            # Clean out all replacement chars
            # log_text_extraction("Prepping Unicode Chars:" + repr(children))
            children, ascii_map = remove_unicode_replacements(children,
                                                              byte_count=self.ucbc)
            # print("===\nCHILD:" + repr(children))
            # print("===\nASCII:" + repr(ascii_map))
            # Merge all surrogate pairs
            children = merge_surrogate_chars(children,
                                             ascii_map,
                                             self.use_ASCII_alternatives_on_unicode_decode_failure)
            # print("FINAL CHILDREN")
            # log_text_extraction("Replaced Unicode Chars With: " + repr(children))
        return children

    def iterate_on_children(self, children): # Children should be 'List[Union[Token,Tree]]' but lark's Tree typing is defined badly.
        set_fonts = []
        if is_logger_on("RTFDE.text_extraction") is True:
            log_text_extraction("Starting to iterate on text extraction children...")
            log_text_extraction("PREP-BEFORE: "+repr(children))
        children = self.prep_unicode(children)
        if is_logger_on("RTFDE.text_extraction") is True:
            log_text_extraction("PREP-AFTER: "+repr(children))

        for item in children:
            if is_font_number(item): # Font Definitions
                self.font_stack.append(item.value.strip())
                set_fonts.append(item.value)
                if self.keep_fontdef is True:
                    yield item
            elif is_unicode_char_byte_count(item):
                bc = get_unicode_char_byte_count(item)
            elif is_unicode_encoded(item): # Unicode Chars
                decoded = unicode_escape_to_chr(item.value).encode()
                # Convert into STRING token
                decoded_tok = Token('STRING',
                                    decoded,
                                    start_pos=item.start_pos,
                                    end_pos=item.end_pos,
                                    line=item.line,
                                    end_line=item.end_line,
                                    column=item.column,
                                    end_column=item.end_column)
                if is_logger_on("RTFDE.text_extraction") is True:
                    log_text_extraction(f"UNICODE TOKEN {item}: {decoded_tok}")
                yield decoded_tok
            # Decode a hex array
            elif is_hexarray(item):
                # print("IS Hex?? {0}".format(item))
                base_bytes = None
                for hexchild in item.children:
                    if base_bytes is None:
                        base_bytes = get_bytes_from_hex_encoded(hexchild.value)
                    else:
                        base_bytes += get_bytes_from_hex_encoded(hexchild.value)
                current_fontdef = self.font_table[self.font_stack[-1]]
                current_codec = current_fontdef.codec
                decoded_hex = decode_hex_char(base_bytes, current_codec)
                # We are replacing a Tree. So, need item.data to access it's info token
                decoded_hex_tok = Token('STRING',
                                        decoded_hex,
                                        start_pos=item.data.start_pos,
                                        end_pos=item.data.end_pos,
                                        line=item.data.line,
                                        end_line=item.data.end_line,
                                        column=item.data.column,
                                        end_column=item.data.end_column)
                yield decoded_hex_tok
            elif isinstance(item, Tree):
                # Run this same function recursively on nested trees
                item.children = [i for i in self.iterate_on_children(item.children)]
                yield item
            else:
                yield item
        for i in set_fonts:
            # Remove all fonts defined while in this group
            self.font_stack.pop()
