# -*- coding: utf-8 -*-
#
# This file is part of RTFDE, a RTF De-Encapsulator.
# Copyright © 2020 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.


# TODO: Remove
HTMLRTF_GRAMMAR = """
start : obj+
obj : HTMLRTF | OTHER | WS
%import common.DIGIT
%import common.LETTER
%import common.WS
_SPACE_DELETE : " "
HTMLRTF : "\\htmlrtf" DIGIT~0..3
OTHER : /((?!\\\\htmlrtf).)+/s
"""


GRAMMAR = {
    "imports": r"""
%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.DIGIT
%import common.NEWLINE
%import common.LETTER""",
    "ignore": r"""%ignore NEWLINE""",
    "_LBRACE": r'"{"',
    "_RBRACE": r'"}"',
    "BACKSLASH": r'"\\"',
    "start": r"_LBRACE document _RBRACE",
    "document": r"""(CONTROLWORD
                    | control_symbol
                    | string
                    | group
                    | HTMLRTF
                    | hexarray
                    | _SPACE_DELETE
                    | SPACE_SAVE
                    | UNICODE)+""",
    "group": r"""_LBRACE (CONTROLWORD
                        | control_symbol
                        | string
                        | htmltag_group
                        | mhtmltag_group
                        | group
                        | SPACE_SAVE
                        | _SPACE_DELETE
                        | HTMLRTF
                        | UNICODE
                        | hexarray
                        | NEWLINE )* _RBRACE""",
    "htmltag_group": r"STAR_ESCAPE HTMLTAG ( string | group )*",
    "HTMLTAG": r'"\\htmltag" DIGIT~0..3 _SPACE_DELETE?',
    "MHTMLTAG": r'"\\mhtmltag" DIGIT~0..3 _SPACE_DELETE?',
    "mhtmltag_group": r"STAR_ESCAPE MHTMLTAG ( string | group )*",
    "NUMERICALDEL": r"SIGNED_NUMBER*",
    "_SPACE_DELETE": r'" "',
    "SPACE_SAVE": r'" "',
    "DELIMITER": r"NUMERICALDEL _SPACE_DELETE?",
    "ASCIILETTERSEQUENCE" : r"LETTER+",
    "CONTROLWORD": "BACKSLASH ASCIILETTERSEQUENCE~1..32 DELIMITER",
    "STAR_ESCAPE": r'BACKSLASH "*"',
    "NONBREAKING_HYPHEN": r'BACKSLASH "_"',
    "OPTIONAL_HYPHEN": r'BACKSLASH "-"',
    "NONBREAKING_SPACE": r'BACKSLASH "~"',
    "FORMULA_CHARACTER": r'BACKSLASH "|"',
    "INDEX_SUBENTRY": r'BACKSLASH ":"',
    "control_symbol": r"(STAR_ESCAPE | INDEX_SUBENTRY | FORMULA_CHARACTER | NONBREAKING_SPACE | OPTIONAL_HYPHEN | NONBREAKING_HYPHEN )",
    "STRING": r'/.+?/',
    "?string": r"STRING+ SPACE_SAVE?",
    "_QUESTION_MARK": r'"?"',
    "UNICODE" : r"""("\\u" /[-]*[0-9]+/)+""",
    "HEXENCODED": """("\\'" /[0-9A-Fa-f]/~2)""",
    "hexarray": "HEXENCODED+",
    "HTMLRTF": r'"\\htmlrtf" DIGIT~0..3 _SPACE_DELETE?',
   }


# // == Priority Levels ==
# This dictionary sets the priority level for each type of object in the lexer.
# Higher numbers give a greater priority.
# All must start with a period
# EXPLICIT IS BETTER THEN RELYING ON DEFAULTS
# // 0 = Raw String Matching // text should defer to everything else if conflicting
# // 1 = Generic undefined object (i.e. group, CONTROL_WORD, CONTROL_SYMBOL, etc.)
# // 2 = Specific instances of objects (i.e. HTMLTAG, MHTMLTAG, etc.)

PRIORITY_LEVELS = {
    "_LBRACE": ".2",
    "_RBRACE": ".2",
    "BACKSLASH" : ".1",
    "start" : ".1",
    "document": ".1",
    "group": ".1",
    "htmltag_group" : ".2",
    "HTMLRTF" : ".2",
    "HTMLTAG" : ".2",
    "MHTMLTAG" : ".2",
    "mhtmltag_group" : ".2",
    "NUMERICALDEL" : ".1",
    "_SPACE_DELETE" : ".1",
    "SPACE_SAVE" : ".1",
    "DELIMITER" : ".1",
    "ASCIILETTERSEQUENCE" : ".1",
    "CONTROLWORD": ".1",
    "STAR_ESCAPE": ".1",
    "NONBREAKING_HYPHEN": ".1",
    "OPTIONAL_HYPHEN": ".1",
    "NONBREAKING_SPACE": ".1",
    "FORMULA_CHARACTER": ".1",
    "INDEX_SUBENTRY": ".1",
    "control_symbol": ".1",
    "STRING" : ".0",
    "_QUESTION_MARK": ".1",
    "?string" : ".0",
    "UNICODE" : ".2",
    "HEXENCODED" : ".1",
    "hexarray" : ".2",
}

def make_concise_grammar():
    """Make a grammar string to use with the lexer.
    """
    grammar = r""""""
    for key, priority in PRIORITY_LEVELS.items():
        grammar += "{0}{1} : {2}\n".format(key,priority,GRAMMAR[key])
    grammar += GRAMMAR['imports'] + "\n"
    grammar += GRAMMAR['ignore'] + "\n"
    return (grammar)



def make_literate_grammar():
    """Create a VERBOSE grammar string which can be used to understand the grammar.

    This SHOULD be updated to include and changes to the grammar.
    This is valuable when debugging and/or otherwise trying to understand the grammar.
    """
    grammar = r"""

// ===== Precedence =========
// Literals are matched according to the following precedence:
// 1. Highest priority first (priority is specified as: TERM.number: …)
// 2. Length of match (for regexps, the longest theoretical match is used)
// 3. Length of literal / pattern definition
// 4. Name
//
// == Priority Levels ==
// WARNING: Priority Levels are not shown in this literate grammar.
// NOTE: Look at PRIORITY_LEVELS for the prioritized levels used in production.
// 0 = Raw String Matching // text should defer to everything else if conflicting
// 1 = Generic undefined object (i.e. group, CONTROL_WORD, CONTROL_SYMBOL, etc.)
// 2 = Specific instances of objects (i.e. HTMLTAG, MHTMLTAG, etc.)

// ====== GRAMMAR OBJECT IMPORTS FROM LARK COMMONS ======
// https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark
{imports}


// ====== Ignore Newlines ======
// The real carriage returns are stored in \par or \line tags.
{ignore}

// ====== SIMPLE GRAMMAR OBJECTS USED THROUGHOUT ======
// RTF is braces all the way down
// We don't have to worry about escaped braces since we are pre-processing out escaped braces already
_LBRACE: {_LBRACE}
_RBRACE: {_RBRACE}

// We don't have to worry about escaped backslashes since we are pre-processing out escaped braces already
BACKSLASH: {BACKSLASH}

// RTF control words are made up of ASCII alphabetical characters (a through z and A through Z)
ASCIILETTERSEQUENCE: {ASCIILETTERSEQUENCE}

// A space that should be deleted (See Delimiters below)
_SPACE_DELETE: {_SPACE_DELETE}

// But, we want to save spaces within strings. So, we have a special space for that.
SPACE_SAVE : {SPACE_SAVE}

// ====== UNMATCHED RAW TEXT ======
// In order to split out everything that is simply plain text and not a special RTF object I've had to match all raw text characters individually. This allows us to store them all in their own rule branch (string) for tranformation later on.

STRING : {STRING}

// We use the ? char to inline this rule to remove the branch and replace it with its children if it has one match. This will make it easier to parse later and remove uneccesary matches of it.
?string: {?string}




// ====== HIGH LEVEL DOCUMENT PARSING ======

// The start object is the top level object in the tree
// An RTF file has the following syntax: '{{' <header & document> '}}'
start: {start}

// Parse <header & document>
document: {document}

// A group consists of text and control words or control symbols enclosed in braces ({{}}).
// The opening brace ({{ ) indicates the start of the group and the closing brace ( }}) indicates the end of the group.
group: {group}


// ====== CONTROL WORD(s) ======

// A control word is defined by: \<ASCII Letter Sequence><Delimiter>
// A control word’s name cannot be longer than 32 letters.
CONTROLWORD: {CONTROLWORD}

// === Delimiter ==

DELIMITER: {DELIMITER}

// The <Delimiter> can be one of the following:
// 1. A numeric digit or an ASCII minus sign (-), which indicates that a numeric parameter is associated with the control word.
NUMERICALDEL: {NUMERICALDEL}
// 2. A space: When a space is used as a the delimiter, it is discarded. This means that it’s not included in subsequent processing. So, we are using a discarded terminal (by putting a underscore in front of the name) to ensure it is tossed.
// See: "_SPACE_DELETE" under SIMPLE GRAMMAR OBJECTS

// 3. Any character other than a letter or a digit. In this case, the delimiting character terminates the control word and is not part of the control word. So, it's not included in the grammar here.


// ====== CONTROL SYMBOLS(s) ======

// A control symbol consists of a backslash followed by a single, nonalphabetic character.
// For example, \~ represents a nonbreaking space.

// The STAR_ESCAPE special construct means that if the program understands the \command, it takes this to mean {\command ...}, but if it doesn’t understand \command, the program ignores not just \command (as it would anyway) but everything in this group.
STAR_ESCAPE: {STAR_ESCAPE}
NONBREAKING_HYPHEN: {NONBREAKING_HYPHEN}
OPTIONAL_HYPHEN: {OPTIONAL_HYPHEN}
NONBREAKING_SPACE: {NONBREAKING_SPACE}
FORMULA_CHARACTER: {FORMULA_CHARACTER}
INDEX_SUBENTRY: {INDEX_SUBENTRY}

// Control symbols take no delimiters.
control_symbol: {control_symbol}





// ====== SPECIAL CONTROL WORD(s) ======

// ====== HEADER OBJECTS ======

// The FROMHTML control word specifies that the RTF document contains encapsulated HTML text.
// This control word MUST be \fromhtml1. Any other form, such as \fromhtml or \fromhtml0, will not be considered encapsulated
// FROMTEXT: {FROMTEXT}

//The FROMHTML control word specifies that the RTF document contains encapsulated HTML text.
// This control word MUST be \fromhtml1. Any other form, such as \fromhtml or \fromhtml0, will not be considered encapsulated.
//FROMHTML : {FROMHTML}


// ====== SPECIFIC CONTROL WORD OBJECTS ======

// HTMLRTF Toggle Control Word
// The HTMLRTF control word identifies fragments of RTF that were not in the original HTML content
// If the flag is "\htmlrtf" or "\htmlrtf1" then do not process anything else until you encounter "\htmlrtf0" which will toggle this off again.
// A de-encapsulating RTF reader MUST support the HTMLRTF control word within nested groups. The state of the HTMLRTF control word MUST transfer when entering groups and be restored when exiting groups.
// This means that you can only turn this off on it's own level (turning it off in an object nested within it does nothing). And, if the object it's in ends then it doesn't transfer up the tree to objects that contain it. So, if you don't find a closing "\htmlrtf0" you can delete from the opening "\htmlrtf" all the way until the end of the current object, but not above.
HTMLRTF : {HTMLRTF}

// The HTMLTAG destination group encapsulates HTML fragments that cannot be directly represented in RTF
htmltag_group: {htmltag_group}

// The "DIGIT~0..3" in the following definition is the HTMLTagParameter from the spec.
    // A space MUST be used to separate the CONTENT HTML fragment from the HTMLTagParameter HTML fragment if the text starts with a DIGIT, or if the HTMLTagParameter HTML fragment is omitted. As such, we throw away this space by using _SPACE_DELETE if we encounter one.
HTMLTAG: {HTMLTAG}



content : {content}

// \*\mhtmltag[HTMLTagParameter] [CONTENT]
// The values and format of the numeric parameter are identical to the numeric parameter in the HTMLTAG destination group.
// This RTF control word SHOULD be skipped on de-encapsulation and SHOULD NOT be written when encapsulating.
# TODO: https://datatracker.ietf.org/doc/html/draft-ietf-mhtml-cid-00#section-1
// NOTE: mhtmltag's contain original URL which has been replaced in the corresponding  htmltag with the CID of an object. As such, it contains possibly useful URI data that, while not useful for the direct output, should be saved.
MHTMLTAG : {MHTMLTAG}
mhtmltag_group: {mhtmltag_group}


// TODO: Check if really neeeded
// Increased priority of escape chars to make unescaping easier
// Multiple char acceptance is important here because if you just catch one escape at a time you mess up multi-byte values.
_QUESTION_MARK: {_QUESTION_MARK}

// TODO Define these objects

// RTFESCAPE no longer used
// RTFESCAPE : {RTFESCAPE}

// UNICODE unicode chars
UNICODE : {UNICODE}

// Hex chars [HEXENCODED] are stored in an array [hexarray]
// We often need to parse hex chars as a set so this is the easiest way
HEXENCODED : {HEXENCODED}
hexarray : {hexarray}

    """.format(**GRAMMAR)
    return grammar


if __name__ == '__main__':
    # print(make_literate_grammar())
    print(make_concise_grammar())
