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
from lark.tree import Tree
from lark.lexer import Token


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
        args = tree.children
        first_control = self._first_controlword(args)
        non_visible_control_words = ["\\context", "\\colortbl", "\\fonttbl"]
        if args == []:
            return ''
        # "Ignore all groups with the RTF ignore control symbol that are not used in RTF<->HTML conversions"
        # See:  https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxrtfex/752835a4-ad5e-49e3-acce-6b654b828de5
        if isinstance(args[1], Token) and args[1].value == "\\*":
            if not first_control.startswith("\\htmltag"):
                return ""
        # Currently deleting all groups that don't have an htmltag.
        elif args[1].type == "CONTROLWORD":
            if not first_control.startswith("\\htmltag"):
                return ""
        # Removing known non-visible objects
        # TODO: Add more based on research you haven't done yet
        elif first_control in non_visible_control_words:
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

    def group(self, args):
        """Join the strings in all groups."""
        return "".join(args)

    def document(self, args):
        """Join the final set of strings to make the final html string."""
        return "".join(args)

    def OPENPAREN(self, args):
        """Delete all open parens."""
        return ""

    def CLOSEPAREN(self, args):
        """Delete all closed parens."""
        return ""

    def CONTROLSYMBOL(self, args):
        """Convert encoded chars which are mis-categorized as control symbols into their respective chars. Delete all the other ones.
        """
        symbols = {
            '\\{': '\x7B',
            '\\}': '\x7D',
            '\\\\': '\x5C',
            '\\~': '\u00A0',
            '\\_': '\u00AD'
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

    def TEXT(self, args):
        """Converts escaped values in text and then return the text as a raw string."""
        escapes = {
            '\\par': '\n',
            '\\tab': '\t',
            '\\line': '\n',
            '\\lquote': '\u2018;',
            '\\rquote': '\u2019;',
            '\\ldblquote': '\u201C;',
            '\\rdblquote': '\u201D;',
            '\\bullet': '\u2022;',
            '\\endash': '\u2013;',
            '\\emdash': '\u2014;',
            '\\{': '\x7B',
            '\\}': '\x7D',
            '\\\\': '\x5C',
            '\\~': '\u00A0',
            '\\_': '\u00AD'
        }
        text = args.value
        for match,rep in escapes.items():
            text = text.replace(match, rep)
        return text
