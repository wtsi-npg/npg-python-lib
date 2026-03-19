# -*- coding: utf-8 -*-
#
# Copyright © 2023, 2025, 2026 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, BinaryIO, Generator, TextIO

import dateutil.parser

"""This module provides utility functions for command line interfaces."""


def add_date_range_arguments(parser: ArgumentParser, begin_delta=14):
    """Add --begin-date and --end-date arguments to the argument parser.

    Args:
        parser: The parser to modify
        begin_delta: The time delta for the default begin date relative to the default
        end date (which is today). Defaults to 14 days i.e. --begin-date is 14 days ago.

    Returns:
        The parser.
    """

    parser.add_argument(
        "--begin-date",
        "--begin_date",
        help="Limit to after this date. Defaults to 14 days ago. The argument must "
        "be an ISO8601 UTC date or date and time "
        "e.g. 2022-01-30, 2022-01-30T11:11:03Z",
        type=parse_iso_date,
        default=datetime.now(timezone.utc) - timedelta(days=begin_delta),
    )
    parser.add_argument(
        "--end-date",
        "--end_date",
        help="Limit to before this date. Defaults to the current time. The argument "
        "must be an ISO8601 UTC date or date and time "
        "e.g. 2022-01-30, 2022-01-30T11:11:03Z",
        type=parse_iso_date,
        default=datetime.now(timezone.utc),
    )


def add_db_config_arguments(parser: ArgumentParser) -> ArgumentParser:
    """Adds a database configuration argument to a parser.

    - --db-config/--db_config/--database-config/--database_config

    Args:
        parser: An argument parser to modify.

    Returns:
        The parser
    """

    parser.add_argument(
        "--db-config",
        "--db_config",
        "--database-config",
        "--database_config",
        help="Configuration file for database connection",
        type=str,
        required=True,
    )

    return parser


def add_io_arguments(parser: ArgumentParser) -> ArgumentParser:
    """Adds standard input/output arguments to a parser. A literal ``-`` should be
    used to indicate STDIN/STDOUT.

    - --input
    - --output

    Args:
        parser: An argument parser to modify.

    Returns:
        The parser
    """

    parser.add_argument(
        "--input",
        help="Input file",
        type=str,
        default="-",
    )
    parser.add_argument(
        "--output",
        help="Output file",
        type=str,
        default="-",
    )

    return parser


def add_logging_arguments(parser: ArgumentParser) -> ArgumentParser:
    """Adds standard CLI logging arguments to a parser.

    - --log-config Use a log configuration file.
    - -d/--debug Enable DEBUG level logging to STDERR.
    - -v/--verbose Enable INFO level logging to STDERR.

    - --colour Use coloured log rendering to the console.
    - --log-json Use JSON log rendering.

    Args:
        parser: An argument parser to modify.

    Returns:
        The parser
    """

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument(
        "--log-config",
        "--log_config",
        help="A logging configuration file.",
        type=str,
    )
    group1.add_argument(
        "-d",
        "--debug",
        help="Enable DEBUG level logging to STDERR.",
        action="store_true",
    )
    group1.add_argument(
        "-v",
        "--verbose",
        help="Enable INFO level logging to STDERR.",
        action="store_true",
    )

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument(
        "--colour",
        help="Use coloured log rendering to the console.",
        action="store_true",
    )
    group2.add_argument(
        "--log-json",
        "--log_json",
        help="Use JSON log rendering.",
        action="store_true",
    )

    return parser


def parse_iso_date(date: str) -> datetime:
    """Custom argparse type for ISO8601 dates."""

    try:
        return dateutil.parser.isoparse(date)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Incorrect format {date}. Please use ISO8601 UTC e.g. 2022-01-30T11:11:03Z"
        )


def integer_in_range(minimum: int, maximum: int):
    """Custom argparse type for integers in a range."""

    def check_range(value: str) -> int:
        try:
            val = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Value {value} is not an integer")

        if val < minimum or val > maximum:
            raise argparse.ArgumentTypeError(
                f"Value {val} is not in range {minimum} to {maximum}"
            )
        return val

    return check_range


@contextmanager
def open_input(
    path: str | None, mode="rt", **kwargs
) -> Generator[BinaryIO | TextIO | Any, Any, None]:
    """Open a file for reading or use STDIN if the supplied path is '-' or None.


    Args:
        path: File path.
        mode: File open mode. Default is 'rt'.
        kwargs: Other keyword arguments passed to ``Path.open`` if STDIN is not used.

    This is meant to be used as a context manager together with ``add_io_arguments``.

    E.g.
        parser = add_io_arguments(parser)
        args = parser.parse_args()

        with open_input(args.input) as input:
            for line in input:
                print(line)
    """

    bin_mode = "b" in mode
    if path in (None, "-"):
        if bin_mode:
            yield sys.stdin.buffer
        else:
            yield sys.stdin
        return

    stream = Path(path).open(mode=mode, **kwargs)
    try:
        yield stream
    finally:
        stream.close()


@contextmanager
def open_output(
    path: str | None, mode="wt", **kwargs
) -> Generator[BinaryIO | TextIO | Any, Any, None]:
    """Open a file for writing or use STDOUT if the supplied path is '-' or None.

    Args:
        path: File path.
        mode: File open mode. Default is 'wt'.
        kwargs: Other keyword arguments passed to ``Path.open`` if STDOUT is not used.

    This is meant to be used as a context manager together with ``add_io_arguments``.

    E.g.
        parser = add_io_arguments(parser)
        args = parser.parse_args()

        with open_output(args.output) as output:
            print("Hello, world!", file=output)

    """

    bin_mode = "b" in mode
    if path in (None, "-"):
        if bin_mode:
            yield sys.stdout.buffer
        else:
            yield sys.stdout
        return

    stream = Path(path).open(mode=mode, **kwargs)
    try:
        yield stream
    finally:
        stream.close()
