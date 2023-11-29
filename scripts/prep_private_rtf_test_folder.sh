#!/usr/bin/env bash
#
# This file is part of RTFDE.
# Copyright © Symbol’s function definition is void: end-of-file) seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

# =============
# INSTRUCTIONS
# =============

# Run this script to extract .rtf msg bodies from .msg files. Can be run in multiple ways.
#
# 1) extract the .rtf bodies from a folder of .msg files into another folder.
#> ./prep_private_rtf_test_folder.sh -i /tmp/msg_files/ -o /tmp/extracted_rtf/
#
# 2) exract the .rtf body from a single .msg file into a folder
#> ./prep_private_rtf_test_folder.sh -i /tmp/msg_files/email.msg -o /tmp/extracted_rtf/
#
# 2) exract the .rtf body from a single .msg file to a specific filename
#> ./prep_private_rtf_test_folder.sh -i /tmp/msg_files/email.msg -o /tmp/extracted_rtf/extracted_msg.rtf
#

# Setup
#Bash should terminate in case a command or chain of command finishes with a non-zero exit status.
#Terminate the script in case an uninitialized variable is accessed.
#See: https://github.com/azet/community_bash_style_guide#style-conventions
set -e
set -u

readonly PROG_DIR=$(readlink -m $(dirname $0))

while getopts "i:o:" option; do
    case "${option}" in
        i)  INPATH="${OPTARG}"
            ;;
        o)  OUTPATH="${OPTARG}"
            ;;
    esac
done

main() {
    if [[ -d "${INPATH}" ]] && [[ -d "${OUTPATH}" ]];
    then
        convert_folder
    else
        convert_file
    fi
}

convert_folder() {
    echo "Extracting RTF from a folder full of .msg files"
    for i in "${INPATH}"/*.msg; do
        python3 "${PROG_DIR}/extract_rtf_from_msg.py" -r \
                -f "${i}" \
                -o "${OUTPATH}/$(basename ${i/%msg/rtf}).rtf"
    done
}

convert_file() {
    echo "Extracting RTF from a single .msg file"
    if [[ -d "${OUTPATH}" ]];
    then
        extract_location="${OUTPATH}/${INPATH/%msg/rtf}"
    else
        extract_location="${OUTPATH/%msg/rtf}"
    fi
    python3 "${PROG_DIR}/extract_rtf_from_msg.py" -r \
            -f "${INPATH}" \
            -o "${extract_location}"
}

main
