Module RTFDE.text_extraction
============================

Functions
---------

    
`check_codepage_num(codepage_num: int) ‑> int`
:   Provide the codepage number back to you if it is valid.
    
    Args:
        codepage_num (int): A possible codepage number.
    
    Returns:
        The codepage number IF it is a valid codepage number
    
    Raises:
        ValueError: The codepage_num provided isn't a valid codepage number.

    
`decode_hex_char(item, codec)`
:   Decode a bytes object using a specified codec.
    
    item (bytes): A bytes object.
    codec (str): The name of the codec to use to decode the bytes

    
`decode_surrogate_pair(high: bytes, low: bytes, encoding: str = 'utf-16-le') ‑> bytes`
:   Convert a pair of surrogate chars into the corresponding utf-16 encoded text string they should represent.
    
    Args:
            high (bytes): the high-surrogate code point
            low (bytes): the low-surrogate code point
            encoding (str): The encoding to apply to the final value. Defaults to 'utf-16-le' because:  Microsoft uses UTF-16, little endian byte order. ( https://learn.microsoft.com/en-us/windows/win32/intl/using-byte-order-marks ) The Msg format is a Microsoft standard. Therefore, man is mortal.

    
`get_bytes_from_hex_encoded(item)`
:   Convert hex encoded string to bytes.
    
    item (str): a hex encoded string in format \'XX

    
`get_codepage_num_from_fcharset(fcharsetN: int) ‑> Optional[int]`
:   Return the codepage to use with a specific fcharsetN.
    
    Args:
        fcharsetN (int): The numeric argument N for a charsetN control word.
    
    Returns:
        (int OR None) Returns the int for a codepage if known. Returns None for unknown charsets or charsets with no corresponding codepage (such as OEM or DEFAULT.)

    
`get_default_font(tree: lark.tree.Tree) ‑> Optional[str]`
:   Extract the font number controlword default font if it exists.
    
    If an RTF file uses a default font, the default font number is specified with the \deffN control word, which must precede the font-table group.
    
    Args:
        tree (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree object.
    
    Returns:
        The default font control number if it exists from the first `\deffN`. None if not found.

    
`get_font_table(tree: lark.tree.Tree) ‑> lark.tree.Tree`
:   Extract the font table group from the first 20 tokens of a .rtf document.
    
    Args:
        tree (Tree): A .rtf document object parsed into a Tree object
    
    Raises:
        ValueError: If no group with a `\fonttbl` token as its first controlword is found.
    
    Returns:
        {'\f0': fontdef(fnum='\f0', codepage=932, codec='cp932', fontdef_tree='{\f0\fswiss\fcharset128 MS PGothic;}'),
        '\f1': fontdef(fnum='\f1', codepage=None, codec=None, fontdef_tree='{\f1\fmodern MS Gothic;}'),
        '\f2': fontdef(fnum='\f2', codepage=None, codec=None, fontdef_tree='{\f2\fnil\fcharset2 Symbol;}'),
        '\f3': fontdef(fnum='\f3', codepage=1252, codec='cp1252', fontdef_tree='{\f3\fmodern\fcharset0 Courier New;}'),
        '\f4': fontdef(fnum='\f4', codepage=932, codec='cp932', fontdef_tree='{\f4\fswiss\fcharset128 "PMingLiU";}'),
        '\f5': fontdef(fnum='\f5', codepage=None, codec=None, fontdef_tree='{\f5\fswiss "Amnesty Trade Gothic";}'),
        '\f6': fontdef(fnum='\f6', codepage=None, codec=None, fontdef_tree='{\f6\fswiss "Arial";}')}

    
`get_python_codec(codepage_num: int) ‑> str`
:   Returns the python codec needed to decode bytes to unicode.
    
    Args:
        codepage_num (int): A codepage number.
    
    Returns:
        The name of the codec in the Python codec registry. Used as the name for enacoding/decoding.

    
`get_unicode_char_byte_count(item: lark.lexer.Token) ‑> int`
:   

    
`has_hexarray(children: List[Union[lark.lexer.Token, lark.tree.Tree]]) ‑> bool`
:   Checks if an tree's children includes a hexarray tree.
    
    children (array): the children object from a tree.

    
`includes_unicode_chars(children: List[lark.lexer.Token]) ‑> bool`
:   Does a list include Tokens which contain unicode characters. Not recursive.
    
    Args:
        children (list): A Tree.children list to check to see if it includes unicode characters.
    
    Returns:
        True if list includes tokens which contain unicode chars. False if not.

    
`is_font_number(token: lark.lexer.Token) ‑> bool`
:   Checks if an object is a "font number".
    
    Returns:
        True if an object is a "font number" controlword `\fN`. False if not.

    
`is_hex_encoded(item: lark.lexer.Token) ‑> bool`
:   Identify if a token contains a HEXENCODED token.
    Args:
        item (token): A token to check if it is HEXENCODED.
    
    Return:
        True if HEXENCODED. False if not.

    
`is_hexarray(item)`
:   Checks if an item is a hexarray tree.
    
    item (Tree or Token): an item to check to see if its a hex array

    
`is_surrogate_16bit(item: bytes, cp_range) ‑> bool`
:   Checks if a unicode char is 16 bit signed integer or the raw unicode char. This should first check if it is a surrogate code using the is_surrogate_XXXX_char functions.
    
    Args:
        item (bytes): A bytes representation of a string representing a unicode character.
        cp_range (str): ['low' OR 'high'] The code point range (low-surrogate or high-surrogate).

    
`is_surrogate_high_char(item: bytes) ‑> bool`
:   Check's if chr is a is in the high-surrogate code point rage. "High-surrogate code point: A Unicode code point in the range U+D800 to U+DBFF." High-surrogate also sometimes known as the leading surrogate.
    
    item (bytes): A bytes representation of a string representing a unicode character. "\u-10179"

    
`is_surrogate_low_char(item: bytes) ‑> bool`
:   Check's if chr is a is in the low-surrogate code point rage. "Low-surrogate code point: A Unicode code point in the range U+DC00 to U+DFFF."  Low-surrogate also sometimes known as following surrogates.
    
    item (bytes): A bytes representation of a string representing a unicode character.

    
`is_surrogate_pair(first: bytes, second: bytes) ‑> bool`
:   Check if a pair of unicode characters are a surrogate pair. Must be passed in the correct order.
    
    Args:
        first (bytes): A bytes representation of a string representing the high-order byte in a surrogate char.
        second (bytes): A bytes representation of a string representing the low-order byte in a surrogate char.

    
`is_unicode_char_byte_count(item: lark.lexer.Token) ‑> bool`
:   

    
`is_unicode_encoded(item: lark.lexer.Token) ‑> bool`
:   Is token contain a unicode char.
    
    Args:
        item (token): A token to check if contains a unicode char.
    
    Return:
        True if token contains a unicode char. False if not.

    
`is_valid_ANSI_representation_char(item: lark.lexer.Token) ‑> bool`
:   Is token contain a valid ANSI representation string for a Unicode char.
    
    Args:
        item (token): A token to check if it is a valid ANSI representation.
    
    Return:
        True if token is an ansi representation of a unicode char. False if not.

    
`merge_surrogate_chars(children, ascii_map, use_ASCII_alternatives_on_unicode_decode_failure=False)`
:   Raises:
        ValueError:  A Standalone high-surrogate was found. High surrogate followed by a illegal low-surrogate character.

    
`parse_font_tree(font_tree: lark.tree.Tree) ‑> dict`
:   Create a font tree dictionary with appropriate codeces to decode text.
    
    Args:
        font_tree (Tree): The .rtf font table object decoded as a tree.
    
    Returns:
        A dictionary which maps font numbers to appropriate python codeces needed to decode text.

    
`remove_unicode_replacements(children: List[lark.lexer.Token], return_ascii_map: bool = True, byte_count: int = 1) ‑> Union[Tuple[List[lark.lexer.Token], Dict[lark.lexer.Token, List[lark.lexer.Token]]], List[lark.lexer.Token]]`
:   Remove all unicode replacement characters from a list of Tokens.
    
    Args:
        children (list): A Tree.children list to remove unicode replacement characters from.
        return_ascii_map (bool): On True, have this function return a map of the ASCII token that were removed.
        byte_count (int): The number of bytes corresponding to a given \uN Unicode character.  A default of 1 should be assumed if no \uc keyword has been seen in the current or outer scopes.
    
    Returns:
        new_children (list): The list of Tokens with all unicode replacement characters removed.
        ascii_map (dict): All the Tokens which were removed from the provided children list keyed by

    
`unicode_escape_to_chr(item: bytes) ‑> str`
:   Convert unicode char from it's decimal to its unicode character representation. From "\u[-]NNNNN" to the string representing the character whose Unicode code point that decimal represents.
    
    Args:
        item (str): A RTF Escape in the format \u[-]NNNNN.
    
    Returns:
        The unicode character representation of the identified character
    
    Raises:
        ValueError: The escaped unicode character is not valid.

    
`validate_ansi_cpg(header: str) ‑> None`
:   Check an '\ansicpgNNNN' string to see if the number NNNN is an actual codepage.
    
    Args:
        header (str): The value from the lark `\ansicpg` CONTROLWORD Token.
    
    Raises:
        MalformedRtf: If the value passed is not a valid ansi codepage.

Classes
-------

`TextDecoder(keep_fontdef=False, initial_byte_count=None, use_ASCII_alternatives_on_unicode_decode_failure=False)`
:   keep_fontdef: (bool) If False (default), will remove fontdef's from object tree once they are processed.
    initial_byte_count: (int) The initial Unicode Character Byte Count. Does not need to be set unless you are only providing a RTF snippet which does not contain the RTF header which sets the  information.
    use_ASCII_alternatives_on_unicode_decode_failure: (bool) If we encounter errors when decoding unicode chars we will use the ASCII alternative since that's what they are included for.

    ### Methods

    `iterate_on_children(self, children)`
    :

    `prep_unicode(self, children: List[lark.lexer.Token])`
    :

    `set_font_info(self, obj: lark.tree.Tree)`
    :   obj (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree.

    `update_children(self, obj: lark.tree.Tree)`
    :   obj (Tree): A lark Tree object. Should be the DeEncapsulator.full_tree.

`fontdef(fnum, codepage, codec, fontdef_tree)`
:   fontdef(fnum, codepage, codec, fontdef_tree)

    ### Ancestors (in MRO)

    * builtins.tuple

    ### Instance variables

    `codec`
    :   Alias for field number 2

    `codepage`
    :   Alias for field number 1

    `fnum`
    :   Alias for field number 0

    `fontdef_tree`
    :   Alias for field number 3