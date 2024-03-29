Module RTFDE.transformers
=========================

Functions
---------

    
`get_stripped_HTMLRTF_values(tree: lark.tree.Tree, current_state: Optional[bool] = None) ‑> collections.abc.Generator`
:   Get a list of Tokens which should be suppressed by HTMLRTF control words.
    
    
        NOTE: This de-encapsulation supports the HTMLRTF control word within nested groups. The state of the HTMLRTF control word transfers when entering groups and is restored when exiting groups, as specified in [MSFT-RTF].
    
    Returns:
        A list of Tokens which should be suppressed by HTMLRTF control words.

    
`strip_binary_objects(raw_rtf: bytes) ‑> tuple`
:   Extracts binary objects from a rtf file.
    
    Parameters:
        raw_rtf: (bytes): It's the raw RTF file as bytes.
    
    Returns:
        A tuple containing (new_raw, found_bytes)
            new_raw: (bytes) A bytes object where any binary data has been removed.
            found_bytes: (list) List of dictionaries containing binary data extracted from the rtf file. Each dictionary includes the data extracted, where it was extracted from in the original rtf file and where it can be inserted back into the stripped output.
    
        Description of found_bytes dictionaries:
    
            "bytes": (bytes) The binary data contained which was extracted.
            "ctrl_char": (tuple) Tuple containing the binary control word and its numeric parameter
            "start_pos": (int) The position (in the original raw rtf data) where the binary control word started.
            "bin_start_pos": (int) The position (in the original raw rtf data) where the binary data starts.
            "end_pos": (int) The position (in the original raw rtf data) where the binary data ends.
    
        Here is an example of what this looks like (by displaying the printable representation so you can see the bytes and then splitting the dict keys on new lines to make it readable.)
            >> print(repr(found_bytes))
    
            "{'bytes': b'\xf4UP\x13\xdb\xe4\xe6CO\xa8\x16\x10\x8b\n\xfbA\x9d\xc5\xd1C',
              'ctrl_char': (b'\\bin', b'20'),
              'start_pos': 56,
              'end_pos': 83,
              'bin_start_pos': 63}"

    
`toggle_htmlrtf(child: Union[lark.lexer.Token, str]) ‑> Optional[bool]`
:   Identify if htmlrtf is being turned on or off.
    
    Returns:
        Bool representing if htmlrtf is being enabled or disabled. None if object is not an HTMLRTF token.

Classes
-------

`DeleteTokensFromTree(tokens_to_delete: List[lark.lexer.Token])`
:   Removes a series of tokens from a Tree.
    
    Parameters:
        tokens_to_delete: A list of tokens to delete from the Tree object. (sets self.to_delete)
    
    Attributes:
        to_delete: A list of tokens to delete from the Tree object.
        delete_start_pos: The starting position for all the identified tokens. Used to identify which tokens to delete.
    
    Setup attributes including token start_pos tracking.
    
    Args:
        tokens_to_delete: A list of tokens to delete from the Tree object. (sets self.to_delete)

    ### Ancestors (in MRO)

    * lark.visitors.Transformer
    * lark.visitors._Decoratable
    * abc.ABC
    * typing.Generic

`RTFCleaner(visit_tokens: bool = True)`
:   Visits each Token in provided RTF Trees. Converts all tokens that need converting. Deletes all tokens that shouldn't be visible. And, joins all strings that are left into one final string.

    ### Ancestors (in MRO)

    * lark.visitors.Transformer
    * lark.visitors._Decoratable
    * abc.ABC
    * typing.Generic

    ### Methods

    `CLOSEPAREN(self, args: lark.lexer.Token) ‑> bytes`
    :   Delete all closed parens.

    `CONTROLSYMBOL(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert encoded chars which are mis-categorized as control symbols into their respective chars. Delete all the other ones.

    `CONTROLWORD(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert encoded chars which are mis-categorized as control words into their respective chars. Delete all the other ones.

    `FORMULA_CHARACTER(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert a formula character into an empty string.
        
        If we are attempting to represent formula characters the scope for this library has grown too inclusive. This was only used by Word 5.1 for the Macintosh as the beginning delimiter for a string of formula typesetting commands.

    `HTMLTAG(self, htmltag: lark.lexer.Token) ‑> bytes`
    :   Delete all HTMLTAG objects

    `INDEX_SUBENTRY(self, args: lark.lexer.Token) ‑> bytes`
    :   Process index subentry items
        
        Discard index sub-entries. Because, we don't care about indexes when de-encapsulating at this time.

    `NONBREAKING_HYPHEN(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert non-breaking hyphens into visible representation.

    `NONBREAKING_SPACE(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert non-breaking spaces into visible representation.

    `OPENPAREN(self, args: lark.lexer.Token) ‑> bytes`
    :   Delete all open parens.

    `OPTIONAL_HYPHEN(self, args: lark.lexer.Token) ‑> bytes`
    :   Convert hyphen control char into visible representation.

    `SPACE_SAVE(self, string: lark.lexer.Token) ‑> bytes`
    :

    `STAR_ESCAPE(self, char: lark.lexer.Token) ‑> bytes`
    :   Delete all star escape objects

    `STRING(self, string: lark.lexer.Token) ‑> bytes`
    :   Convert a string object into a raw string.

    `control_symbol(self, symbols: List) ‑> bytes`
    :   Join all visible symbols from in control symbol groups.

    `document(self, args: List) ‑> bytes`
    :   Join the all the strings in an .rtf object into a single string representation of the document.

    `group(self, grp: List) ‑> bytes`
    :   Join the strings in all group objects.

    `htmltag_group(self, strings: List) ‑> bytes`
    :   HTMLTAG processing.
        
        Takes any string values within an HTMLTAG and returns them.

    `mhtmltag_group(self, args: List)`
    :   Process MHTMLTAG groups
        
                Currently discarding because they don't need to be processed.
        
        Returns:
                Always returns a discard object.

    `start(self, args: List) ‑> bytes`
    :   Joins the .rtf object's string representations together at highest level object `start`.
        
        This is the final string combination.

    `string(self, strings: List) ‑> bytes`
    :   Convert all string objects withing a string group into a single string.

`StripControlWords(visit_tokens: bool = True)`
:   Visits each control word and strips the whitespace from around it.

    ### Ancestors (in MRO)

    * lark.visitors.Transformer
    * lark.visitors._Decoratable
    * abc.ABC
    * typing.Generic

    ### Methods

    `CONTROLWORD(self, token: lark.lexer.Token)`
    :   Strips the whitespace from around a provided control word.
        
        Args:
                token: A CONTROLWORD token to strip whitespace from.

`StripNonVisibleRTFGroups(visit_tokens: bool = True)`
:   Visits each Token in provided RTF Trees and strips out any RTF groups which are non-visible when de-encapsulated into HTML.

    ### Ancestors (in MRO)

    * lark.visitors.Transformer
    * lark.visitors._Decoratable
    * abc.ABC
    * typing.Generic

    ### Static methods

    `get_first_controlword(children: List) ‑> Optional[str]`
    :   Extracts the first control word from a .rtf group.
        
        Args:
                children: A list of child objects within a .rtf group
        
        Returns:
                The first controlword found in a group. Returns None if no controls words are found.

    ### Methods

    `group(self, tree: lark.tree.Tree)`
    :   Transformer which aggressively seeks out possible non-visible RTF groups and replaces them with empty strings.
        
        NOTE: Currently deleting all groups that don't have an htmltag. Please file an issue if you find one that should be included in de-encapsulated HTML. I will refine what gets deleted and what is converted based on identified needs for greater functionality or specific issues which need to be addressed.
        
        Args:
                tree: A .rtf group (Tree object) which needs its contents decoded.

`StripUnusedSpecialCharacters(visit_tokens: bool = True)`
:   Strip all unused tokens which lark has extracted from the RTF.
    
    These tokens are largely artifacts of the RTF format.
    
    We have to do this because we use the "keep_all_tokens" option in our lark parser. It's better to be explicit then to allow for ambiguity because of the grammar.

    ### Ancestors (in MRO)

    * lark.visitors.Transformer
    * lark.visitors._Decoratable
    * abc.ABC
    * typing.Generic