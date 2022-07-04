#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of RTFDE, a RTF De-Encapsulator.
# Copyright © 2020 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

import re
from lark.visitors import Transformer, Visitor_Recursive, v_args
from lark.visitors import Visitor_Recursive, Discard
from lark.tree import Tree
from lark.lexer import Token

from lark.exceptions import VisitError

class StripControlWords(Transformer):
    """Visits each control word and strips the whitespace from around it.
    """

    def CONTROLWORD(self, token):
        """Strips the whitespace from around it the control word.
        """
        tok = token.update(value=token.value.strip())
        return tok

class RTFUnicodeDecoder(Visitor_Recursive):
    """Visits each Token in provided RTF Trees and decodes any/all unicode characters which it finds.
    """

    def __init__(self):
        """Create the initial \\ucN keyword stack with the default scope included."""
        # A default of 1 should be assumed if no \uc keyword has been seen in the current or outer scopes. - RTF Spec
        self.cur_uc = [1]

    def visit_topdown(self, tree:Tree) -> Tree:
        """Visit each Token in the RTF Tree to decode any/all unicode characters.

        This decoder starts at the root of the tree, and ends at the leaves (top-down) so it can track the state of the '\\ucN' keyword. The \\ucN keyword identifies when the count of bytes for how Unicode characters translate into ANSI character streams differ from the current Unicode Character Byte Count. When unicode encodings (\\uNNNN) are  encountered, the code has to ignore the first N bytes, where N corresponds to the last \\ucN value encountered. If that sounds overly complex to you then then we are in agreement.

        Parameters:
            tree: (Tree): An RTF Tree object which needs its values decoded.
        """
        self._call_userfunc(tree)
        cur_uc = None
        for child in tree.children:
            # The bytelen values (\ucN) are scoped like character properties. That is, a \ucN keyword applies only to text following the keyword, and within the same (or deeper) nested braces.
            # This is covered in more detail in the RTF spec. No matter how much detail it goes into doesn't make up for how much I hate this kludge they implemented.
            if isinstance(child, Token) and child.value.startswith('\\uc'):
                strip_int = re.compile('^[^0-9]+([0-9]+)$')
                cur_uc = int(strip_int.search(child.value).groups()[0])
                self.cur_uc.append(cur_uc)
            elif isinstance(child, Tree):
                self.visit_topdown(child)
            else:
                strip_u = re.compile(r'\\u[-]?[0-9]+[\s]?\??')
                rtfencoded = strip_u.findall(child.value)
                for enc_str in rtfencoded:
                    char_num = int(enc_str[2:].strip("?").strip())
                    if char_num < 0:
                        # RTF control words generally accept signed 16-bit numbers as arguments. For this reason, Unicode decimal values greater than 32767 must be expressed as negative numbers. For example, if Hexdecimal value is 1D703 then the decimal value (120579) is greater than 32767 so the negative Hex-decimal value (03B8) is used and its decimal code is 952
                        # The value of \ucN which appears before a \u-NNNN (a negative decimal unicode char) will tell us how many bytes the -NNNN value occupies when converted to a Unicode character.
                        # For instance, \uc1 would be one byte, thus while \u-3913 would convert to 0xF0B7 (U+F0B7 PRIVATE USE CHARACTER) if it were simply converted into unicode once only one byte (\uc1) is extracted it becomes 0xB7 (U+00B7 MIDDLE DOT) which is the correct character.
                        char = chr(bytearray(chr(65536+char_num).encode())[-self.cur_uc[-1]])
                    else:
                        char = chr(char_num)
                    child.value = child.value.replace(enc_str, char)
        # On exiting the group, the previous \uc value is restored. When leaving an RTF group which specified a \uc value, the reader must revert to the previous value.
        # If we captured a unicode bytelen in this scope we get rid of it when we exit the scope.
        if cur_uc is not None:
            self.cur_uc.pop()
        return tree


class StripNonVisibleRTFGroups(Transformer):
    """Visits each Token in provided RTF Trees and strips out any RTF groups which are non-visible when de-encapsulated into HTML.
    """

    @v_args(tree=True)
    def group(self, tree):
        """Transformer which aggressively seeks out possible non-visible RTF groups and replaces them with empty strings.

        NOTE: Currently deleting all groups that don't have an htmltag. Please file an issue if you find one that should be included in de-encapsulated HTML. I will refine what gets deleted and what is converted based on identified needs for greater functionality or specific issues which need to be addressed.

        Parameters:
            tree: (Tree): An RTF Tree object which needs its values decoded.
        """
        children = tree.children
        first_child = children[0]

        known_control_groups = ["htmltag_group"]
        if isinstance(first_child, Tree):
            if first_child.data in known_control_groups:
                return tree
        known_non_visible_control_groups = ["mhtmltag_group"]
        if isinstance(first_child, Tree):
            if first_child.data in known_non_visible_control_groups:
                return ""

        # process known non-visible groups
        non_visible_control_words = ["\\context", "\\colortbl", "\\fonttbl"]
        first_control = self._first_controlword(children)
        if first_control in non_visible_control_words:
            return ""

        # Process star escaped groups
        # NOTE: `understood_commands` is where we can include commands we decide to actively process during deencapsulation in the future.
        understood_commands = []
        is_star_escaped = None
        if isinstance(first_child, Tree):
            first_item = first_child.children[0]
            if isinstance(first_item, Token):
                if first_item.type == "STAR_ESCAPE":
                    is_star_escaped = True
        control_word = None
        if is_star_escaped is True:
            first_token = children[1]
            if isinstance(first_token, Token):
                if first_token.type == "CONTROLWORD":
                    control_word = first_token
                    if control_word in understood_commands:
                        return tree
                    else:
                        return ""
        return tree

    @staticmethod
    def _first_controlword(children) -> str:
        """Extracts the first control word from a group to make identifying groups easier.
        """
        for i in children:
            try:
                if i.type == "CONTROLWORD":
                    return i.value
            except AttributeError:
                continue

class RTFCleaner(Transformer):
    """Visits each Token in provided RTF Trees. Converts all tokens that need converting. Deletes all tokens that shouldn't be visible. And, joins all strings that are left into one final string.
    """

    def __init__(self, rtf_codec=None):
        """Setup the RTF codec.

        Parameters:
            rtf_codec: (str): The python codec to use when decoding strings.
        """
        if rtf_codec is None:
            self.rtf_codec = 'CP1252'
        else:
            self.rtf_codec = rtf_codec

    def start(self, args):
        return "".join(args)

    def string(self, strings):
        """
        Join the strings in all groups.
        """
        return "".join(strings)

    def STRING(self, string):
        """Convert all objects with strings into strings
        """
        if string.value is not None:
            return string.value
        else:
            return ""

    def group(self, grp):
        """
        Join the strings in all groups.
        """
        _new_children = []
        for i in grp:
            if isinstance(i, type(Discard)):
                pass
            else:
                _new_children.append(i)
        return "".join(_new_children)

    def document(self, args):
        """Join the final set of strings to make the final html string."""
        return "".join(args)

    def OPENPAREN(self, args):
        """Delete all open parens."""
        return ""

    def CLOSEPAREN(self, args):
        """Delete all closed parens."""
        return ""

    def mhtmltag_group(self, tree):
        """Process MHTMLTAG groups

        Currently discarding because they don't need to be processed.
        """
        return Discard

    def htmltag_group(self, strings):
        """HTMLTAG processing.

        Takes any string values within an HTMLTAG and returns them.
        """
        return "".join(strings)

    def HTMLTAG(self, tag):
        return ""

    def STAR_ESCAPE(self, char):
        # '\\*': ''
        return ""

    def control_symbol(self, symbols):
        return "".join(symbols)

    def NONBREAKING_SPACE(self, args):
        # '\\~': '\u00A0',
        return u'\u00A0'

    def NONBREAKING_HYPHEN(self, args):
        # '\\_': '\u00AD'
        return u'\u00AD'

    def OPTIONAL_HYPHEN(self, args):
        # '\\-': '\u2027'
        return u'\u2027'

    def FORMULA_CHARACTER(self, args):
        """Convert a formula character into an empty string.

        If we are encountering formula characters the scope has grown too inclusive. This was only used by Word 5.1 for the Macintosh as the beginning delimiter for a string of formula typesetting commands.
        """
        return ""

    def INDEX_SUBENTRY(self, args):
        """Process index subentry items

        Discard index sub-entries. Because, we don't care about indexes when de-encapsulating at this time.
        """
        return ""

    def CONTROLSYMBOL(self, args):
        """Convert encoded chars which are mis-categorized as control symbols into their respective chars. Delete all the other ones.
        """
        symbols = {
            '\\{': '\x7B',
            '\\}': '\x7D',
            '\\\\': '\x5C',
        }
        replacement = symbols.get(args.value, None)
        # If this is simply a character to replace then return the value
        if replacement is not None:
            return replacement
        else:
            return ""

    def CONTROLWORD(self, args):
        """Convert encoded chars which are mis-categorized as control words into their respective chars. Delete all the other ones.
        """
        words = {
            '\\par': '\n',
            '\\tab': '\t',
            '\\line': '\n',
            '\\lquote': '\u2018',
            '\\rquote': '\u2019',
            '\\ldblquote': '\u201C',
            '\\rdblquote': '\u201D',
            '\\bullet': '\u2022',
            '\\endash': '\u2013',
            '\\emdash': '\u2014'
        }
        replacement = words.get(args.value, None)
        # If this is simply a character to replace then return the value as a string
        if replacement is not None:
            return replacement
        return ""

    def RTFESCAPE(self, args):
        """Decode hex encoded chars using the codec provided. Insert unicode chars directly since we already decoded those earlier.
        """
        if args.value.startswith("\\'"):
            hexstring = args.value.replace("\\'", "")
            hex_bytes = bytes.fromhex(hexstring)
            decoded = hex_bytes.decode(self.rtf_codec)
            return decoded
        # \\u RTFEscapes need to have the \ucN value identified in order to do byte manipulation before being converted. So, we converted those previously in RTFUnicodeDecoder.
        else:
            # We should have handled all escaped chars by here
            # We can simply insert the values from \u RTF Escapes now
            return args.value
