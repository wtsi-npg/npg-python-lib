# -*- coding: utf-8 -*-
#
# Copyright © 2023 Genome Research Ltd. All rights reserved.
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

import json as json_parser
import logging.config

import structlog

"""This module provides utility functions for logging."""


def configure_structlog(
    config_file=None, debug=False, verbose=False, colour=False, json=False
):
    """Configure logging with a file, or individual parameters.

    Configures logging using a configuration file or by setting a log level.

    The structlog pipeline is mostly not configurable (only the "colour" and "json"
    keywords are available). The configuration file modifies the behaviour of
    standard logging, into which structlog sends pre-formatted messages.

    The configuration file must be JSON in the form of a standard logging configuration
    dictionary.

    See https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema

        Args:
            config_file: A file path. Optional. If provided, the debug and verbose
                keywords are ignored in favour of the settings in the file.
            debug: Set to True for DEBUG logging, Defaults to False and overrides
                verbose if set.
            verbose: Set to True for INFO logging. Defaults to False.
            colour: Set to True for colour logging. Defaults to False.
            json: Set to True for JSON structured logs. Defaults to False and
              overrides colour if set.

        Returns:
            Void
    """
    # The processor pipeline (and comments) are taken from the structlog
    # documentation "Rendering within structlog":
    #
    # "This is the simplest approach where structlog does all the heavy
    # lifting and passes a fully formatted string to logging."

    log_processors = [
        # If the log level is too low, abort pipeline and throw away log entry.
        structlog.stdlib.filter_by_level,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # UTC added by kdj
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If the "exc_info" key in the event dict is either true or a
        # sys.exc_info() tuple, remove "exc_info" and render the exception
        # with traceback into the "exception" key.
        structlog.processors.format_exc_info,
        # structlog.processors.dict_tracebacks,
        # If some value is in bytes, decode it to a Unicode str.
        structlog.processors.UnicodeDecoder(),
        # Add call site parameters.
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.THREAD_NAME,
            }
        ),
    ]

    if config_file is not None:
        with open(config_file, "rb") as f:
            conf = json_parser.load(f)
            logging.config.dictConfig(conf)
    else:
        level = logging.ERROR
        if debug:
            level = logging.DEBUG
        elif verbose:
            level = logging.INFO

        logging.basicConfig(level=level, encoding="utf-8")

    if json:
        log_processors.append(structlog.processors.JSONRenderer())
    else:
        log_processors.append(structlog.dev.ConsoleRenderer(colors=colour))

    structlog.configure(
        processors=log_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
