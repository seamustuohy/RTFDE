# -*- coding: utf-8 -*-
#
# codepages is a python module to map code pages (numbers) to Python codecs,
# in order to decode bytes to unicode.
# It also provides the name/description of code pages.
#
# Author: Philippe Lagadec - http://www.decalage.info
# License: BSD, see source code or documentation
#
# codepages is part of the python-oletools package:
# http://www.decalage.info/python/oletools
#
# === LICENSE ==================================================================
#
# codepages is copyright (c) 2018-2019 Philippe Lagadec (http://www.decalage.info)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Mapping from codepages to Python codecs, when 'cpXXX' does not work
# (inspired from http://stackoverflow.com/questions/1592925/decoding-mac-os-text-in-python)
# Copied from oletools.codepages

import codecs

CODEPAGE_TO_CODEC = {
    37: 'cp037',
    708: 'arabic', # not found: Arabic (ASMO 708) => arabic = iso-8859-6
    709: 'arabic', # not found: Arabic (ASMO-449+, BCON V4) => arabic = iso-8859-6
    710: 'arabic', # not found: Arabic - Transparent Arabic => arabic = iso-8859-6
    870: 'latin2', # IBM EBCDIC Multilingual/ROECE (Latin 2); IBM EBCDIC Multilingual Latin 2
    1047: 'latin1', # IBM EBCDIC Latin 1/Open System
    1141: 'cp273', # IBM EBCDIC Germany (20273 + Euro symbol); IBM EBCDIC (Germany-Euro)
    1200: 'utf_16_le', # Unicode UTF-16, little endian byte order (BMP of ISO 10646); available only to managed applications
    1201: 'utf_16_be', # Unicode UTF-16, big endian byte order; available only to managed applications

    10000: 'mac-roman',
    10001: 'shiftjis',  # not found: 'mac-shift-jis',
    10002: 'big5',      # not found: 'mac-big5',
    10003: 'ascii',     # nothing appropriate found: 'mac-hangul',
    10004: 'mac-arabic',
    10005: 'hebrew',    # not found: 'mac-hebrew',
    10006: 'mac-greek',
    #10007: 'ascii',     # nothing appropriate found: 'mac-russian',
    10007: 'mac_cyrillic',  # guess (from xlrd)
    10008: 'gb2312',    # not found: 'mac-gb2312',
    10021: 'thai',      # not found: mac-thai',
    #10029: 'maccentraleurope',  # not found: 'mac-east europe',
    10029: 'mac_latin2',  # guess (from xlrd)
    10079: 'mac_iceland',  # guess (from xlrd)
    10081: 'mac-turkish',

    12000: 'utf_32_le', # Unicode UTF-32, little endian byte order
    12001: 'utf_32_be', # Unicode UTF-32, big endian byte order

    20127: 'ascii',

    28591: 'latin1',
    28592: 'iso8859_2',
    28593: 'iso8859_3',
    28594: 'iso8859_4',
    28595: 'iso8859_5',
    28596: 'iso8859_6',
    28597: 'iso8859_7',
    28598: 'iso8859_8',
    28599: 'iso8859_9',
    28603: 'iso8859_13',
    28605: 'iso8859_15',

    32768: 'mac_roman', # from xlrd
    32769: 'cp1252', # from xlrd
    38598: 'iso8859_8',

    65000: 'utf7',
    65001: 'utf8',
}

def codepage2codec(codepage_num: int) -> str:
    """
    convert a codepage number to a Python codec.
    If the corresponding codec cannot be found, returns "utf8" by default.

    :param codepage: int, code page number
    :return: str, Python codec name
    """
    if codepage_num in CODEPAGE_TO_CODEC:
        codec = CODEPAGE_TO_CODEC[codepage_num]
    else:
        codec = 'cp%d' % codepage_num
    try:
        codecs.lookup(codec)
    except LookupError:
        #log.error('Codec not found for code page %d, using UTF-8 as fallback.' % codepage)
        codec = 'utf8'
    return codec
