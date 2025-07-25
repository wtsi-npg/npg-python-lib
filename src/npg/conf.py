# -*- coding: utf-8 -*-
#
# Copyright © 2024, 2025 Genome Research Ltd. All rights reserved.
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

import dataclasses
import os
from configparser import ConfigParser
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, Optional, TypeVar, get_type_hints

from structlog import get_logger

# The TypeVar isn't bound because dataclasses don't have a common base class. It's
# just here to illustrate that from_file returns an instance of the same dataclass
# that was passed to the constructor.
D = TypeVar("D")

log = get_logger(__name__)


class ParseError(Exception):
    """Raised when a configuration file cannot be parsed."""

    pass


class IniData:
    """A configuration class that reads values from an INI file to create an instance of
    a specified dataclass. Using a dataclass results in configuration that is easier
    to understand and more maintainable than using a bare dictionary because all its
    fields are explicitly defined. This means that they are readable, navigable and
    autocomplete-able in an IDE and can have default values and docstrings.

    E.g. given an INI file 'config.ini':

        [server]
        host = localhost
        port = 9000

    and a dataclass:

        @dataclass
        class ServerConfig:
            host: str
            port: str

    the following code will create a new instance obj of the dataclass where
    host='localhost' and port='9000':

       parser = IniData(ServerConfig)
       obj = parser.from_file("config.ini", "server")

    If the 'use_env' flag is set, the configuration will fall back to an environment
    variable if the INI file does not contain a value for that field. The default
    environment variable name is the field name in upper case. As the shell environment
    lacks the context of an enclosing dataclass, the default name may benefit from a
    prefix to make it more descriptive. This can be provided by using the 'env_prefix'
    argument.

    E.g. given an INI file 'config.ini':

        [server]
        host = localhost

    with an environment variable 'SERVER_PORT' set to '9001' and the same dataclass as
    above, the following code will create a new instance obj of the dataclass where
    host='localhost' and port='9001':

        parser = IniData(ServerConfig, use_env=True, env_prefix="SERVER_").
        obj = from_file("config.ini", "server")

    All values are treated as strings except where the dataclass declares its field
    types as int, float, bool or Path (or Optional versions of these), in which case
    the string is parsed into the appropriate type.

    The class provides INFO level logging of its actions to enable loading of
    configurations to be traced.

    If your dataclass includes sensitive information, you should take care to ensure
    that the fields are not logged. This can be done by declaring the field with
    metadata:

        @dataclass
        class ServerConfig:
            admin-token: str = field(repr=False)

    To extend this class to support additional field types, you can override the
    parse_ini_value and parse_environment_value methods. These handle values from the
    INI file and environment variables, respectively.
    """

    def __init__(self, cls: D, use_env: bool = False, env_prefix: str = ""):
        """Makes a new configuration instance which can create instances of the
        dataclass 'D'.

        Args:
            cls: A dataclass to bind to this configuration.
            use_env: If True, fall back to environment variables if a value is not found
                in an INI file. Defaults to False. The environment variable used to
                supply a missing field's value is the field name in upper case
                (prefixed with env_prefix, if provided).
            env_prefix: A prefix to add to the name of any environment variable used as
                a fallback. Defaults to "". The prefix is folded to upper case.
                Dataclass field names exist in the context of their class. However,
                environment variables exist in a global context and can benefit from a
                more descriptive name. The prefix can be used to provide that.
        """
        if dataclass is None:
            raise ValueError("A dataclass argument is required")
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"'{cls}' is not a dataclass")

        self.dataclass = cls
        self.use_env = use_env
        self.env_prefix = env_prefix

    def from_file(
        self,
        ini_file: PathLike | str,
        section: str,
    ) -> D:
        """Create a new dataclass instance from an INI file section.

        Args:
            ini_file: The INI file path.
            section: The section name containing the configuration.

        Returns:
            A new dataclass instance with values populated from the INI file.
        """
        p = Path(ini_file).resolve().absolute().as_posix()

        log.info(
            "Reading configuration from file",
            path=p,
            section=section,
            dataclass=self.dataclass,
        )

        parser = ConfigParser()
        if not parser.read(p):
            raise ParseError(f"Could not read '{p}'")

        hints = get_type_hints(self.dataclass)
        kwargs = {}
        for field in dataclasses.fields(self.dataclass):
            hint = hints.get(field.name, None)

            if parser.has_option(section, field.name):
                val = self.parse_ini_value(parser, section, field, hint)

                if val is None and self.use_env:
                    env_var = self.env_prefix.upper() + field.name.upper()
                    log.info(
                        "Absent field; using an environment variable",
                        path=p,
                        section=section,
                        field=field.name,
                        env_var=env_var,
                    )
                    val = self.parse_environment_value(os.environ.get(env_var), hint)

                kwargs[field.name] = val

            elif self.use_env:
                env_var = self.env_prefix.upper() + field.name.upper()

                log.debug(
                    "Absent INI section; using an environment variable",
                    path=p,
                    section=section,
                    field=field.name,
                    env_var=env_var,
                )

                kwargs[field.name] = self.parse_environment_value(
                    os.environ.get(env_var), hint
                )

        instance = self.dataclass(**kwargs)
        log.debug("Reading complete", instance=instance)

        return instance

    def parse_ini_value(self, parser: ConfigParser, section: str, field, hint) -> Any:
        """
        Parses the value of a field from a configuration file, converting it to its
        specified type or hint.

        Args:
            parser: Configuration parser object used to read values.
            section: The section in the configuration file where the field resides.
            field: The field object whose value is to be parsed and converted.
            hint: The expected type or hint of the field's value that determines the
                conversion.

        Returns:
            The parsed value converted to the type specified by the hint.
        """
        parsed_val = None

        val = parser.get(section, field.name)
        val = "" if val is None else val.strip()

        if hint is str:
            parsed_val = val
        elif bool(val):
            if hint is int:
                parsed_val = parser.getint(section, field.name)
            elif hint is float:
                parsed_val = parser.getfloat(section, field.name)
            elif hint is bool:
                parsed_val = parser.getboolean(section, field.name)
            elif hint is Path:
                parsed_val = Path(parser.get(section, field.name))
            elif hint is Optional[str]:
                parsed_val = parser.get(section, field.name)
            elif hint is Optional[int]:
                parsed_val = parser.getint(section, field.name)
            elif hint is Optional[float]:
                parsed_val = parser.getfloat(section, field.name)
            elif hint is Optional[bool]:
                parsed_val = parser.getboolean(section, field.name)
            elif hint is Optional[Path]:
                parsed_val = Path(parser.get(section, field.name))

        return parsed_val

    def parse_environment_value(self, val: str, hint) -> Any:
        """
        Parses an environment variable value and converts it to the specified type.

        This function takes a string value and a type hint, converting the string into
        the desired type. It supports the basic data types `str`, `int`, `float`, `bool`,
        and instances of `Path`. Optional types for these primitive or file path types
        are also supported. If an unsupported type is provided in the hint, a
        ValueError` is raised.

        Args:
            val: The string value to convert.
            hint: The expected type or hint of the field's value that determines the
                conversion.

        Returns:
            The parsed value, converted to the specified type.
        """
        if hint is str:
            return val
        elif hint is int:
            return int(val)
        elif hint is float:
            return float(val)
        elif hint is bool:
            return val.lower() == "true"
        elif hint is Path:
            return Path(val)
        elif hint is Optional[str]:
            return val
        elif hint is Optional[int]:
            return int(val) if val else None
        elif hint is Optional[float]:
            return float(val) if val else None
        elif hint is Optional[bool]:
            return val.lower() == "true" if val else None
        elif hint is Optional[Path]:
            return Path(val) if val else None
        else:
            raise ValueError(f"Unsupported type '{hint}'")
