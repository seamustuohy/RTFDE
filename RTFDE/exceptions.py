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

class UnsupportedRTFFormat(Exception):
    """An exception which signifies that the file might be a totally valid RTF encapsulation. But, that it is unsupported at this time."""

class NotEncapsulatedRtf(TypeError):
    """An exception which signifies that the data being provided in not a valid RTF encapsulation.

    You might have passed us a RTF file with no HTML/RTF encapsulation or it may simply be that the tool which did the encapsulation didn't follow the spec so the encapsulation is incorrect. We'll give more information in the error message, but we're not going to try to de-encapsulate it.
    """

class MalformedEncapsulatedRtf(TypeError):
    """An exception which signifies that the data being provided in not a valid RTF encapsulation.

    You might have passed us a RTF file with no HTML/RTF encapsulation or it may simply be that the tool which did the encapsulation didn't follow the spec so the encapsulation is incorrect. We'll give more information in the error message, but we're not going to try to de-encapsulate it.
    """

class MalformedRtf(TypeError):
    """An exception which signifies that the data being provided in not a valid RTF.

    You might have passed us a new variation of RTF lazily created by someone who only read the spec in passing; it's possibly some polyglot file; a RTF file that is intended to be malicious; or even somthing that only looks like RTF in passing. We'll give more information in the error message, but we're not going to try to de-encapsulate it.
    """
