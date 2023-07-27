Module RTFDE.exceptions
=======================

Classes
-------

`MalformedEncapsulatedRtf(*args, **kwargs)`
:   An exception which signifies that the data being provided in not a valid RTF encapsulation.
    
    You might have passed us a RTF file with no HTML/RTF encapsulation or it may simply be that the tool which did the encapsulation didn't follow the spec so the encapsulation is incorrect. We'll give more information in the error message, but we're not going to try to de-encapsulate it.

    ### Ancestors (in MRO)

    * builtins.TypeError
    * builtins.Exception
    * builtins.BaseException

`MalformedRtf(*args, **kwargs)`
:   An exception which signifies that the data being provided in not a valid RTF.
    
    You might have passed us a new variation of RTF lazily created by someone who only read the spec in passing; it's possibly some polyglot file; a RTF file that is intended to be malicious; or even somthing that only looks like RTF in passing. We'll give more information in the error message, but we're not going to try to de-encapsulate it.

    ### Ancestors (in MRO)

    * builtins.TypeError
    * builtins.Exception
    * builtins.BaseException

`NotEncapsulatedRtf(*args, **kwargs)`
:   An exception which signifies that the data being provided in not a valid RTF encapsulation.
    
    You might have passed us a RTF file with no HTML/RTF encapsulation or it may simply be that the tool which did the encapsulation didn't follow the spec so the encapsulation is incorrect. We'll give more information in the error message, but we're not going to try to de-encapsulate it.

    ### Ancestors (in MRO)

    * builtins.TypeError
    * builtins.Exception
    * builtins.BaseException

`UnsupportedRTFFormat(*args, **kwargs)`
:   An exception which signifies that the file might be a totally valid RTF encapsulation. But, that it is unsupported at this time.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException