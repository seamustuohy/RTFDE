#!/usr/bin/env bash
#
# This file is part of RTFDE.
# Copyright © 2022 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

# Setup

#Bash should terminate in case a command or chain of command finishes with a non-zero exit status.
#Terminate the script in case an uninitialized variable is accessed.
#See: https://github.com/azet/community_bash_style_guide#style-conventions
set -e
set -u
# set -x

MYPY="false"
COVERAGE="false"
DEBUG="false"
while getopts "mcd" option; do
    case "${option}" in
        m)  MYPY="true"
            ;;
        c)  COVERAGE="true"
            ;;
        d)  DEBUG="true"
            ;;
    esac
done

main() {
    if [[ "$COVERAGE" == "true" ]]; then
        coverage run -m unittest discover -v
        coverage report -m
    elif [[ "$DEBUG" == "true" ]]; then
        python3 -m unittest discover -v --locals
    else
        python3 -m unittest discover -v
    fi

    if [[ "$MYPY" == "true" ]]; then
        mypy --ignore-missing-imports RTFDE/utils.py
    fi
}

cleanup() {
    # put cleanup needs here
    exit 0
}
trap 'cleanup' EXIT

main
