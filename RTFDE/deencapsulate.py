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

from typing import Union, AnyStr, Tuple, Dict, Any
from io import BufferedReader

from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from lark.exceptions import UnexpectedInput

from RTFDE.transformers import RTFCleaner, StripControlWords
from RTFDE.transformers import StripNonVisibleRTFGroups
from RTFDE.transformers import StripUnusedSpecialCharacters
from RTFDE.utils import encode_escaped_control_chars
from RTFDE.utils import log_validators, log_transformations, is_logger_on
from RTFDE.transformers import get_stripped_HTMLRTF_values, DeleteTokensFromTree, strip_binary_objects
from RTFDE.grammar import make_concise_grammar
from RTFDE.text_extraction import TextDecoder
from RTFDE.text_extraction import validate_ansi_cpg

# For catching exceptions
from RTFDE.exceptions import NotEncapsulatedRtf, MalformedEncapsulatedRtf, MalformedRtf

import logging
log = logging.getLogger("RTFDE")

class DeEncapsulator():
    """De-Encapsulating RTF converter of HTML/TEXT found in .msg files.

De-encapsulation enables previously encapsulated HTML and plain text content to be extracted and rendered as HTML and plain text instead of the encapsulating RTF content. After de-encapsulation, the HTML and plain text should differ only minimally from the original HTML or plain text content.


Parameters:
    raw_rtf: (bytes): It's the raw RTF file as bytes.
    grammar: (str): OPTIONAL - Lark parsing grammar which defines the RTF language. https://github.com/lark-parser/lark If you think my grammar is shoddy this is your chance to test out a better one and make a pull request.

Attributes:
    content: (bytes) The deencapsulated content no matter what format it is in. Populated by the `deencapsulate` function.
    html: (bytes) The deencapsulated content IF it is HTML content. Populated by the `set_content` function.
    text: (bytes) The deencapsulated content IF it is plain text content. Populated by the `set_content` function.
    found_binary: List of dictionaries containing binary data extracted from the rtf file.
    content_type: The type of content encapsulated in .rtf data (html or text). Populated by the `get_content_type` function.
    full_tree: The full .rtf object parsed into an object Tree using the grammar. Populated by the `parse_rtf` function.
    doc_tree: The `document` portion of the .rtf full_tree object.
    raw_rtf: The raw encapsulated .rtf data in byte format.
    grammar: The Lark parsing grammer used to parse the .rtf data.
    content_type_token: The .rtf header token identifying the content type. (\\fromhtml1 OR \\fromtext)
    parser: The lark parser. Should not need to be manipulated directly. But, useful for debugging and saving the parsed object.
    """

    def __init__(self, raw_rtf:bytes, grammar: Union[str,None] = None):
        """Load in the Encapsulated test and setup the grammar used to parse the encapsulated RTF.

NOTE: This does not do the parsing in the init so that you can initiate the object and do the parsing step by step.

Parameters:
        raw_rtf: (bytes): It's the raw RTF string.
        grammar: (str): OPTIONAL - Lark parsing grammar which defines the RTF language. https://github.com/lark-parser/lark If you think my grammar is shoddy this is your chance to test out a better one and make a pull request.

Raises:
        TypeError: The raw_rtf data passed is not the correct type of data (string/byte string).
"""
        self.content: str
        self.content_type: str
        self.content_type_token: str
        self.parser: Any

        self.html: str
        self.text: str
        self.found_binary: list
        self.full_tree: Tree
        self.doc_tree: Tree
        self.catch_common_validation_issues(raw_rtf)
        if isinstance(raw_rtf, bytes):
            raw_rtf_bytes = raw_rtf
        else:
            raise TypeError("DeEncapssulator only accepts RTF files in string or byte-string formats")
        raw_rtf_bytes = raw_rtf_bytes.rstrip(b'\x00')
        raw_rtf_bytes = raw_rtf_bytes.replace(b'\r\n',b'\n')
        raw_rtf_bytes = raw_rtf_bytes.replace(b'\r',b'\n')
        self.raw_rtf: bytes = raw_rtf_bytes
        if grammar is not None:
            self.grammar: str = grammar
        else:
            self.grammar = make_concise_grammar()

    def deencapsulate(self):
        """De-encapsulate the RTF content loaded into the De-Encapsulator.

Once you have loaded in the raw rtf this function will set the properties containing the encapsulated content. The `content` property will store the content no matter what format it is in. The `html` and `text` properties will be populated based on the type of content that is extracted. (self.html will be populated if it is html and self.text if it is plain text.)
        """
        stripped_data = strip_binary_objects(self.raw_rtf)
        non_binary_rtf = stripped_data[0]
        found_binary = stripped_data[1]
        if len(found_binary) > 0:
            self.found_binary = found_binary
            log.info("Binary data found and extracted from rtf file.")
        escaped_rtf = encode_escaped_control_chars(non_binary_rtf)
        if is_logger_on("RTFDE.transform_logger") is True:
            log_transformations(escaped_rtf)
        try:
            self.parse_rtf(escaped_rtf)
        except UnexpectedInput as _e:
            raise MalformedEncapsulatedRtf(f"Malformed encapsulated RTF discovered:") from _e
        Decoder = TextDecoder()
        Decoder.update_children(self.full_tree)
        self.get_doc_tree()
        self.validate_encapsulation()

        # remove htmlrtf escaped values
        htmlrtf_stripped = self.strip_htmlrtf_tokens()
        # Strips whitespace from control words
        control_stripped = StripControlWords().transform(htmlrtf_stripped)
        # Strip unused control chars
        special_stripper = StripUnusedSpecialCharacters()
        non_special_tree = special_stripper.transform(control_stripped)
        # Strip out non-visible RTF groups
        stripper = StripNonVisibleRTFGroups()
        stripped_tree = stripper.transform(non_special_tree)
        # Converts any remaining tokens
        cleaner = RTFCleaner(visit_tokens=True)
        cleaned_text = cleaner.transform(stripped_tree)

        self.content = cleaned_text
        self.set_content() # Populates self.html || self.text

    def validate_charset(self, fallback_to_default:bool =False) -> bytes:
        """Validate and return the RTF charset keyword from the RTF streams header.

Args:
        fallback_to_default (bool): Allows you to force the use of the default charset "\\ansi" if one is not found.

Raises:
        MalformedRtf: RTF stream does not include charset control word.

Returns:
        The RTF charset keyword from the RTF streams header.
"""
        main_headers = self.get_header_control_words_before_first_group()

        for token in main_headers:
            if token.value in [b'\\ansi', b'\\mac', b'\\pc', b'\\pca']:
                return token

        log.debug("Acceptable charset not found as the second token in the RTF stream. The control word for the character set must precede any plain text or any table control words. So, if this stream doesn't have one it is malformed or corrupted.")
        if fallback_to_default is False:
            raise MalformedRtf("RTF stream does not include charset control word.")

        log.warning("The fallback_to_default option on _get_charset is considered DANGEROUS if used on possibly malicious samples. Make sure you know what you are doing before using it.")
        log.info("Attempting to decode RTF using the default charset ansi. This is not recommended and could have unforeseen consequences for the resulting file and your systems security.")
        log.debug("You have a malformed RTF stream. Are you sure you really want to be parsing it? It might not just be corrupted. It could be maliciously constructed.")
        return b"\\ansi"

    def set_content(self):
        """Populate the html or text content based on the content type. Populates self.html and/or self.text variables."""
        self.content_type = self.get_content_type()
        if self.content_type == 'html':
            self.html = self.content
        else:
            self.text = self.content

    def get_doc_tree(self):
        """Extract the document portion of the .rtf full_tree object. Populates the classes doc_tree attribute.

Raises:
        ValueError: The .rtf document object is missing or mis-located in the .rtf's full_tree object.
"""
        if self.full_tree.children[1].data == "document":
            self.doc_tree = self.full_tree.children[1]
        else:
            raise ValueError("Document object in the wrong place after parsing.")

    def get_content_type(self):
        """Provide the type of content encapsulated in RTF.

NOTE: This function will only work after the header validation has completed. Header validation also extracts the content type of the encapsulated data.

Raises:
        NotEncapsulatedRtf: The .rtf object is missing an encapsulated content type header. Which means that it is likely just a regular .rtf file.
"""
        if self.content_type_token is None:
            self.validate_FROM_in_doc_header()
        elif self.content_type_token == b'\\fromhtml1':
            return 'html'
        elif self.content_type_token == b'\\fromtext':
            return "text"

        raise NotEncapsulatedRtf("Data is missing encapsulated content type header (the FROM header).")

    def validate_encapsulation(self):
        """Runs simple tests to validate that the file in question is an rtf document which contains encapsulation."""
        self.validate_rtf_doc_header(self.doc_tree)
        self.validate_charset()
        self.validate_FROM_in_doc_header()
        ansicpg = self.get_ansicpg_header()
        if ansicpg is not None: # ansicpg is not manditory
            validate_ansi_cpg(ansicpg.value)

    def get_ansicpg_header(self) -> Union[Token,None]:
        """Extract the ansicpg control word from the .rtf header.

Returns:
        A lark CONTROLWORD Token with the `\\ansicpg` value. Returns None if the `\\ansicpg` control word is not included as this is only required if there is Unicode which needs to be converted to ANSI within a .rtf file.
"""
        headers = self.get_header_control_words_before_first_group()
        for item in headers:
            if item.value.startswith(b'\\ansicpg'):
                return item
        return None

    def parse_rtf(self, rtf: str):
        """Parse RTF file's header and document and extract the objects within the RTF into a Tree. Populates the self.full_tree attribute.

Args:
        rtf: The .rtf string to parse with the projects lark grammar.
"""
        # Uncomment Lark debug argument if you want to enable logging.
        # Note, this not enable ALL lark debug logging.
        # To do that we would not be able to use the Lark convinence class which we are using here.
        self.parser = Lark(self.grammar,
                           parser='lalr',
                           keep_all_tokens=True,
                           use_bytes=True,
                           # debug=True,
                           propagate_positions=True)
        self.full_tree = self.parser.parse(rtf)
        if is_logger_on("RTFDE.transform_logger") is True:
            log_transformations(self.full_tree)


    def strip_htmlrtf_tokens(self) -> Tree:
        """Strip tokens from with htmlrtf regions of the doc_tree as they were not part of the original HTML content.

Returns:
        .rtf doc_tree stripped of all non-original tokens.
"""
        # remove htmlrtf escaped values
        delete_generator = get_stripped_HTMLRTF_values(self.doc_tree)
        tokens_to_delete = list(delete_generator)
        deleter = DeleteTokensFromTree(tokens_to_delete)
        htmlrtf_cleaned_tree = deleter.transform(self.doc_tree)
        return htmlrtf_cleaned_tree


    def get_header_control_words_before_first_group(self) -> list:
        """Extracts all the control words in the first 20 tokens of the document or all the tokens which occur before the first group (whichever comes first.)

This is used to extract initial header values for validation functions.

Returns:
        A list containing the header tokens in the .rtf data.
        """
        initial_control_words = []
        for token in self.doc_tree.children[:20]:
            if isinstance(token, Token):
                initial_control_words.append(token)
            else:
                return initial_control_words
        return initial_control_words


    def validate_FROM_in_doc_header(self):
        """Inspect the header to identify what type of content (html/plain text) is encapsulated within the document.

NOTE: The de-encapsulating RTF reader inspects no more than the first 10 RTF tokens (that is, begin group marks and control words) in the input RTF document, in sequence, starting from the beginning of the RTF document. If one of the control words is the FROMHTML control word, the de-encapsulating RTF reader will conclude that the RTF document contains an encapsulated HTML document and stop further inspection. If one of the control words is the FROMTEXT control word, the de-encapsulating RTF reader concludes that the RTF document was produced from a plain text document and stops further inspection. - MS-OXRTFEX

Raises:
        MalformedEncapsulatedRtf: The .rtf headers are malformed.
        NotEncapsulatedRtf: The .rtf object is missing an encapsulated content type header. Which means that it is likely just a regular .rtf file.
        """
        cw_found = {"rtf1":False,
                    "from":False,
                    "fonttbl":False,
                    "malformed":False}
        # The de-encapsulating RTF reader SHOULD inspect no more than the first 10 RTF tokens (that is, begin group marks and control words) in the input RTF document, in sequence, starting from the beginning of the RTF document. This means more than just control words.
        decoded_tree = StripControlWords().transform(self.doc_tree)
        first_ten_tokens = decoded_tree.children[:10]
        operating_tokens = []
        found_token = None
        for token in first_ten_tokens:
            if isinstance(token, Token):
                operating_tokens.append(token)
            else:
                operating_tokens += list(token.scan_values(lambda t: t.type == 'CONTROLWORD'))
        if is_logger_on("RTFDE.validation_logger") is True:
            log_validators(f"Header tokens being evaluated: {operating_tokens}")

        for token in operating_tokens:
            cw_found,found_token = self.check_from_token(token=token, cw_found=cw_found)
            if cw_found['from'] is True and cw_found["malformed"] is True:
                raise MalformedEncapsulatedRtf("RTF file looks like is was supposed to be encapsulated HTML/TEXT but the headers are malformed. Turn on debugging to see specific information")
            # Save content type token available for id-ing type of content later
            if found_token is not None:
                self.content_type_token = found_token

        if cw_found['from'] is False:
            log.debug("FROMHTML/TEXT control word not found in first 10 RTF tokens. This is not an HTML/TEXT encapsulated RTF document.")
            raise NotEncapsulatedRtf("FROMHTML/TEXT control word not found.")

    @staticmethod
    def check_from_token(token:Token, cw_found:dict) -> Tuple[Dict,Union[None,str]] :
        """Checks if fromhtml1 or fromtext tokens are in the proper place in the header based on the state passed to it by the validate_FROM_in_doc_header function.

Args:
        token: The token to check for in the cw_found state dictionary.
        cw_found: The state dictionary which is used to track the position of the from token within the header.

        `cw_found = {"rtf1":<BOOL>, "from":<BOOL>, "fonttbl":<BOOL>, "malformed":<BOOL>}`


Returns:
        cw_found: Updated state dictionary
        found_token: The content_type_token found in the header.

        """
        from_cws = [b'\\fromhtml1', b'\\fromtext']
        # This control word MUST appear before the \fonttbl control word and after the \rtf1 control word, as specified in [MSFT-RTF].
        rtf1_cw = b"\\rtf1"
        found_token = None
        fonttbl_cw = b"\\fonttbl"
        if token.type == "CONTROLWORD":
            if token.value.strip() in from_cws:
                if cw_found['from'] is True:
                    cw_found["malformed"] = True
                    log.debug("Multiple FROM HTML/TXT tokens found in the header. This encapsulated RTF is malformed.")
                if cw_found['rtf1'] is True:
                    cw_found['from'] = True
                    found_token = token.value
                else:
                    log.debug("FROMHTML/TEXT control word found before rtf1 control word. That's not allowed in the RTF spec.")
                    cw_found['from'] = True
                    cw_found["malformed"] = True
            elif token.value.strip() == rtf1_cw:
                cw_found['rtf1'] = True
            elif token.value.strip() == fonttbl_cw:
                cw_found['fonttbl'] = True
                if cw_found['from'] is not True:
                    log.debug("\\fonttbl code word found before FROMTML/TEXT was defined. This is not allowed for encapsulated HTML/TEXT. So... this is not encapsulated HTML/TEXT or it was badly encapsulated.")
                    cw_found["malformed"] = True
        return cw_found, found_token


    @staticmethod
    def validate_rtf_doc_header(doc_tree: Tree):
        """Check if doc starts with a valid RTF header `\\rtf1`.

        "Before the de-encapsulating RTF reader tries to recognize the encapsulation, the reader SHOULD ensure that the document has a valid RTF document heading according to [MSFT-RTF] (that is, it starts with the character sequence "{\\rtf1")." - MS-OXRTFEX

Raises:
        MalformedRtf: The .rtf headers do not include \\rtf1.
"""
        first_token = doc_tree.children[0].value
        if first_token != b"\\rtf1":
            log.debug("RTF stream does not contain valid valid RTF document heading. The file must start with \"{\\rtf1\"")
            if is_logger_on("RTFDE.validation_logger") is True:
                log_validators(f"First child object in document tree is: {first_token!r}")
            raise MalformedRtf("RTF stream does not start with {\\rtf1")

    @staticmethod
    def catch_common_validation_issues(raw_rtf: AnyStr):
        """Checks for likely common valid input mistakes that may occur when folks try to use this library and raises exceptions to try and help identify them.

Args:
        raw_rtf: A raw .rtf string or byte-string.

Raises:
        TypeError: The data passed is the wrong type of data.
        MalformedRtf: The data passed is not a correctly formatted .rtf string.
"""
        if isinstance(raw_rtf, BufferedReader):
            raise TypeError("Data passed as file pointer. DeEncapsulator only accepts byte objects.")
        if raw_rtf is None:
            raise TypeError("Data passed as raw RTF file is a null object `None` keyword.")
        if raw_rtf[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise TypeError("Data passed is a full MSG object. You must extract the encapsulated RTF body first.")
        if raw_rtf in (b'', ''):
            raise MalformedRtf("Data passed as raw RTF file is an empty string.")
