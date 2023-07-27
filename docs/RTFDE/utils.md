Module RTFDE.utils
==================

Functions
---------

    
`embed()`
:   

    
`encode_escaped_control_chars(raw_text: bytes) ‑> bytes`
:   Replaces escaped control chars within the text with their RTF encoded versions \'HH.
    
    Args:
        raw_text (str): string which needs escape characters encoded
    
    Returns:
        A string with escaped control chars

    
`flatten_tree(tree: lark.tree.Tree) ‑> collections.abc.Generator`
:   Flatten a lark Tree into a list of repr's of tree objects.
    
    Args:
        tree (lark Tree): A lark tree

    
`flatten_tree_to_string_array(tree: lark.tree.Tree) ‑> collections.abc.Generator`
:   Flatten a lark Tree into a list of repr's of tree objects.
    
    Args:
        tree (lark Tree): A lark tree

    
`get_control_parameter_as_hex_strings(control_parameter: Union[str, int]) ‑> str`
:   Returns the hex encoded value of a .rtf control parameter.
    
    Args:
        control_parameter: (int/str) Int or a string which represents an int.
    
    Returns:
        Zero padded 6 char long hexedecimal string.

    
`get_string_diff(original: bytes, revised: bytes, sep: Optional[bytes] = None)`
:   Get the diff of two strings. Defaults to splitting by newlines and keeping the ends.
    
    Args:
        original: The original string
        revised: The changed version of the string
        sep (string): A pattern to split the string by. Uses re.split under the hood. NOTE: Deletes all empty strings before diffing to make the diff more concise.
    
    Returns:
        A string object representing the diff of the two strings provided.

    
`get_tree_diff(original: lark.tree.Tree, revised: lark.tree.Tree)`
:   Get the diff of two trees.
    
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

    
`is_codeword_with_numeric_arg(token: Union[lark.lexer.Token, Any], codeword: bytes) ‑> bool`
:   Checks if a Token is a codeword with a numeric argument.
    
    Returns:
        True if a Token is a codeword with a numeric argument. False if not.

    
`log_htmlrtf_stripping(data: lark.lexer.Token)`
:   Log HTMLRTF Stripping logging only if RTFDE.HTMLRTF_Stripping_logger set to debug.
    
    Raises:
        AttributeError: Will occur if you pass this something that is not a token.

    
`log_string_diff(original: bytes, revised: bytes, sep: Optional[bytes] = None)`
:   Log diff of two strings. Defaults to splitting by newlines and keeping the ends.
    
    Logs the result in the main RTFDE logger as a debug log. Warning: Only use when debugging as this is too verbose to be used in regular logging.
    
    Args:
        original: The original string
        revised: The changed version of the string
        sep (string): A pattern to split the string by. Uses re.split under the hood. NOTE: Deletes all empty strings before diffing to make the diff more concise.

    
`log_text_extraction(data)`
:   Log additional text decoding/encoding logging only if RTFDE.text_extraction set to debug.

    
`log_transformations(data)`
:   Log transform logging only if RTFDE.transform_logger set to debug.

    
`log_validators(data)`
:   Log validator logging only if RTFDE.validation_logger set to debug.

    
`make_token_replacement(ttype, value, example)`
:   

    
`print_lark_parser_evaluated_grammar(parser)`
:   Prints the final evaluated grammar.
    
    Can be useful for debugging possible errors in grammar evaluation.
    
    Args:
        parser (Lark obj): Lark object to extract grammar from.

    
`print_to_tmp_file(data: Union[~AnyStr, bytes, bytearray], path: str)`
:   Prints binary object to a dump file for quick debugging.
    
    Warning: Not for normal use. Only use when debugging.
    
    Args:
        data (bytes|str): Data to write to path
        path (str): The file path to write data to