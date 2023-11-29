#!/usr/bin/env python3
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

import os, sys
sys.path.append('/home/s2e/code/RTFDE')


import argparse
from RTFDE.deencapsulate import DeEncapsulator
import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)
from os import walk
import os


try:
    import extract_msg
except ModuleNotFoundError as _e:
    log.error("You need to install `extract_msg` to use this script. If installing from pip following the `Install with optional dependencies` instructions in INSTALL.md with the term `msg_parse` or visit  https://github.com/TeamMsgExtractor/msg-extractor to install it directly\n")
    raise _e

def main():
    args = parse_arguments()
    set_logging(args.verbose, args.debug)
    if args.show_folder_msg_stats is not None:
        show_folder_msg_stats(args.show_folder_msg_stats)
        return
    msg_path = args.msg_path
    with extract_msg.openMsg(msg_path) as msg:
        attachments = None
        try:
            attachments = get_attachments(msg)
        except KeyError as _e:
            log.debug("Msg does not have attachments embedded. Likely you used a low quality eml -> msg converter for testing and it provided somewhat broken msg files. Or at least that's when this pops off the most for me.")
        if attachments is None:
            log.debug("No attachments found in msg.")
        else:
            log.debug("{0} attachments found in msg.".format(len(attachments)))
        raw_rtf = msg.rtfBody
        # print(raw_rtf.decode())
        if args.extract_raw is True:
            if args.outfile:
                with open(args.outfile, 'wb') as fp:
                    fp.write(raw_rtf)
                with open(args.outfile + ".compressed", 'wb') as fp:
                    fp.write(msg.compressedRtf)
            else:
                print(raw_rtf.decode())
            if args.extract_all is True:
                # Get the raw HTML and text body (don't de-encapsulate RTF if it exists)
                _html_body = msg._ensureSet('_htmlBody', '__substg1.0_10130102', False)
                _text_body = msg._ensureSet('_body', '__substg1.0_1000')
                others = {"html":_html_body,
                          "txt": _text_body}
                for item_type, item in others.items():
                    if item is not None:
                        if args.outfile:
                            outname = "{0}.{1}".format(args.outfile, item_type)
                            with open(outname, 'wb') as fp:
                                if item_type == "txt":
                                    item = item.encode()
                                fp.write(item)
                        else:
                            print(item)
        else:
            rtf_obj = DeEncapsulator(raw_rtf.decode())
            rtf_obj.deencapsulate()
            if rtf_obj.content_type == 'html':
                print(rtf_obj.html)
            else:
                print(rtf_obj.text)

def show_folder_msg_stats(folder_path):
    for (dirpath, dirnames, filenames) in walk(folder_path):
        for f in filenames:
            print("processing {0}".format(f))
            if not f.endswith('.msg'):
                continue
            else:
                abf = os.path.join(os.path.abspath(dirpath), f)
                parts = get_body_parts(abf)
                for k,v in parts.items():
                    if v:
                        print(k,"True")
                    else:
                        print(k,"False")

def get_body_parts(msg_path):
    parts = {}
    with extract_msg.openMsg(msg_path) as msg:
        parts["html"] = msg._ensureSet('_htmlBody', '__substg1.0_10130102', False)
        parts["plain"] = msg._ensureSet('_body', '__substg1.0_1000')
        parts["rtf"] = msg._ensureSet('_compressedRtf', '__substg1.0_10090102', False)
    return parts


def get_attachments(msg):
    """
    Gets all attachments from a MSG file which will be embedded in the encapsulated RTF body.

    - The PidTagAttachmentHidden property ([MS-OXPROPS] section 2.599) is set to TRUE (0x01) if an Attachment object is hidden from the end user.
      - https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxprops/282fe6b2-3086-4d35-b496-5834a290f4cb

    - The PidTagRenderingPosition property ([MS-OXPROPS] section 2.914) represents an offset, in rendered characters, to use when rendering an attachment within the main message text. The value 0xFFFFFFFF indicates a hidden attachment that is not to be rendered in the main text.
      - https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxprops/2d785055-a410-4bea-8e85-55b05845254d

    MS-OXCMSG: https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxcmsg
    MS-OXRTFEX: https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxrtfex
    MS-OXPROPS:https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxprops
    """
    RTF_Attachments = None
    for attachment in msg.attachments:
        PidTagAttachmentHidden = attachment.props.get('7FFE000B')

        if PidTagAttachmentHidden.value is False or None:
            PidTagRenderingPosition = attachment.props.get('370B0003')
            if PidTagRenderingPosition != 0xFFFFFFFF:
                if RTF_Attachments is None:
                    RTF_Attachments = {}
                RTF_Attachments[PidTagRenderingPosition.value] = attachment
    return RTF_Attachments

# Command Line Functions below this point

def set_logging(verbose=False, debug=False):
    if debug == True:
        log.setLevel("DEBUG")
    elif verbose == True:
        log.setLevel("INFO")

def parse_arguments():
    parser = argparse.ArgumentParser("RTFDE")
    parser.add_argument("--verbose", "-v",
                        help="Turn verbosity on",
                        action='store_true')
    parser.add_argument("--debug", "-d",
                        help="Turn debugging on",
                        action='store_true')
    parser.add_argument("--msg_path", "-f",
                        help="Path to msg file to extract from.",
                        required=True)
    parser.add_argument("--extract_raw", "-r",
                        help="Only extract raw rtf encapsulated HTML file from msg.",
                        action='store_true')
    parser.add_argument("--extract_all", "-a",
                        help="Extract HTML and Plain Text alongside RTF from msg.",
                        action='store_true')
    parser.add_argument("--outfile", "-o",
                        help="Write the output instead of piping it out.")
    parser.add_argument("--show_folder_msg_stats", "-S",
                        help="Process a folder of msg items printing which ones have different elements.")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
