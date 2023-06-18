Module RTFDE.deencapsulate
==========================

Classes
-------

`DeEncapsulator(raw_rtf: ~AnyStr, grammar: Optional[str] = None)`
:   De-Encapsulating RTF converter of HTML/TEXT found in .msg files.
    
    De-encapsulation enables previously encapsulated HTML and plain text content to be extracted and rendered as HTML and plain text instead of the encapsulating RTF content. After de-encapsulation, the HTML and plain text should differ only minimally from the original HTML or plain text content.
    
    
    Parameters:
        raw_rtf: (str): It's the raw RTF string.
        grammar: (str): OPTIONAL - Lark parsing grammar which defines the RTF language. https://github.com/lark-parser/lark If you think my grammar is shoddy this is your chance to test out a better one and make a pull request.
    
    Attributes:
        content: The deencapsulated content no matter what format it is in. Populated by the `deencapsulate` function.
        html: The deencapsulated content IF it is HTML content. Populated by the `set_content` function.
        text: The deencapsulated content IF it is plain text content. Populated by the `set_content` function.
        content_type: The type of content encapsulated in .rtf data (html or text). Populated by the `get_content_type` function.
        full_tree: The full .rtf object parsed into an object Tree using the grammar. Populated by the `parse_rtf` function.
        doc_tree: The `document` portion of the .rtf full_tree object.
        raw_rtf: The raw encapsulated .rtf data in string format.
        grammar: The Lark parsing grammer used to parse the .rtf data.
        content_type_token: The .rtf header token identifying the content type. (\fromhtml1 OR \fromtext)
        parser: The lark parser. Should not need to be manipulated directly. But, useful for debugging and saving the parsed object.
        
    
    Load in the Encapsulated test and setup the grammar used to parse the encapsulated RTF.
    
    NOTE: This does not do the parsing in the init so that you can initiate the object and do the parsing step by step.
    
    Parameters:
            raw_rtf: (str): It's the raw RTF string.
            grammar: (str): OPTIONAL - Lark parsing grammar which defines the RTF language. https://github.com/lark-parser/lark If you think my grammar is shoddy this is your chance to test out a better one and make a pull request.
    
    Raises:
            TypeError: The raw_rtf data passed is not the correct type of data (string/byte string).

    ### Static methods

    `catch_common_validation_issues(raw_rtf: ~AnyStr)`
    :   Checks for likely common valid input mistakes that may occur when folks try to use this library and raises exceptions to try and help identify them.
        
        Args:
                raw_rtf: A raw .rtf string or byte-string.
        
        Raises:
                TypeError: The data passed is the wrong type of data.
                MalformedRtf: The data passed is not a correctly formatted .rtf string.

    `check_from_token(token: lark.lexer.Token, cw_found: dict) ‑> Tuple[Dict, Optional[None]]`
    :   Checks if fromhtml1 or fromtext tokens are in the proper place in the header based on the state passed to it by the validate_FROM_in_doc_header function.
        
        Args:
                token: The token to check for in the cw_found state dictionary.
                cw_found: The state dictionary which is used to track the position of the from token within the header.
        
                `cw_found = {"rtf1":<BOOL>, "from":<BOOL>, "fonttbl":<BOOL>, "malformed":<BOOL>}`
        
        
        Returns:
                cw_found: Updated state dictionary
                found_token: The content_type_token found in the header.

    `validate_rtf_doc_header(doc_tree: lark.tree.Tree)`
    :   Check if doc starts with a valid RTF header `\rtf1`.
        
                "Before the de-encapsulating RTF reader tries to recognize the encapsulation, the reader SHOULD ensure that the document has a valid RTF document heading according to [MSFT-RTF] (that is, it starts with the character sequence "{\rtf1")." - MS-OXRTFEX
        
        Raises:
                MalformedRtf: The .rtf headers do not include \rtf1.

    ### Methods

    `deencapsulate(self)`
    :   De-encapsulate the RTF content loaded into the De-Encapsulator.
        
        Once you have loaded in the raw rtf this function will set the properties containing the encapsulated content. The `content` property will store the content no matter what format it is in. The `html` and `text` properties will be populated based on the type of content that is extracted. (self.html will be populated if it is html and self.text if it is plain text.)

    `get_ansicpg_header(self) ‑> Optional[lark.lexer.Token]`
    :   Extract the ansicpg control word from the .rtf header.
        
        Returns:
                A lark CONTROLWORD Token with the `\ansicpg` value. Returns None if the `\ansicpg` control word is not included as this is only required if there is Unicode which needs to be converted to ANSI within a .rtf file.

    `get_content_type(self)`
    :   Provide the type of content encapsulated in RTF.
        
        NOTE: This function will only work after the header validation has completed. Header validation also extracts the content type of the encapsulated data.
        
        Raises:
                NotEncapsulatedRtf: The .rtf object is missing an encapsulated content type header. Which means that it is likely just a regular .rtf file.

    `get_doc_tree(self)`
    :   Extract the document portion of the .rtf full_tree object. Populates the classes doc_tree attribute.
        
        Raises:
                ValueError: The .rtf document object is missing or mis-located in the .rtf's full_tree object.

    `get_header_control_words_before_first_group(self) ‑> list`
    :   Extracts all the control words in the first 20 tokens of the document or all the tokens which occur before the first group (whichever comes first.)
        
        This is used to extract initial header values for validation functions.
        
        Returns:
                A list containing the header tokens in the .rtf data.

    `parse_rtf(self, rtf: str)`
    :   Parse RTF file's header and document and extract the objects within the RTF into a Tree. Populates the self.full_tree attribute.
        
        Args:
                rtf: The .rtf string to parse with the projects lark grammar.

    `set_content(self)`
    :   Populate the html or text content based on the content type. Populates self.html and/or self.text variables.

    `strip_htmlrtf_tokens(self) ‑> lark.tree.Tree`
    :   Strip tokens from with htmlrtf regions of the doc_tree as they were not part of the original HTML content.
        
        Returns:
                .rtf doc_tree stripped of all non-original tokens.

    `validate_FROM_in_doc_header(self)`
    :   Inspect the header to identify what type of content (html/plain text) is encapsulated within the document.
        
        NOTE: The de-encapsulating RTF reader inspects no more than the first 10 RTF tokens (that is, begin group marks and control words) in the input RTF document, in sequence, starting from the beginning of the RTF document. If one of the control words is the FROMHTML control word, the de-encapsulating RTF reader will conclude that the RTF document contains an encapsulated HTML document and stop further inspection. If one of the control words is the FROMTEXT control word, the de-encapsulating RTF reader concludes that the RTF document was produced from a plain text document and stops further inspection. - MS-OXRTFEX
        
        Raises:
                MalformedEncapsulatedRtf: The .rtf headers are malformed.
                NotEncapsulatedRtf: The .rtf object is missing an encapsulated content type header. Which means that it is likely just a regular .rtf file.

    `validate_charset(self, fallback_to_default: bool = False) ‑> str`
    :   Validate and return the RTF charset keyword from the RTF streams header.
        
        Args:
                fallback_to_default (bool): Allows you to force the use of the default charset "\ansi" if one is not found.
        
        Raises:
                MalformedRtf: RTF stream does not include charset control word.
        
        Returns:
                The RTF charset keyword from the RTF streams header.

    `validate_encapsulation(self)`
    :   Runs simple tests to validate that the file in question is an rtf document which contains encapsulation.