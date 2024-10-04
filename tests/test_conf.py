# -*- coding: utf-8 -*-
#
# Copyright © 2024 Genome Research Ltd. All rights reserved.
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


from dataclasses import dataclass
from typing import Optional

import pytest
from pytest import mark as m

from npg.conf import IniData, ParseError


@dataclass
class ExampleConfig:
    """An example dataclass for testing."""

    key1: str
    key2: Optional[str] = None


class NonDataclass:
    """A example non-dataclass for testing."""

    pass


@m.describe("IniData")
@m.context("When the INI file is missing")
@m.it("Raises a ParseError")
def test_missing_ini_file(tmp_path):
    ini_file = tmp_path / "missing.ini"

    parser = IniData(ExampleConfig)
    with pytest.raises(ParseError):
        parser.from_file(ini_file, "section")


@m.context("When the dataclass is missing")
@m.it("Raises a ValueError")
def test_invalid_dataclass():
    with pytest.raises(ValueError):
        IniData(None)


@m.context("When the dataclass is a non-dataclass")
@m.it("Raises a ValueError")
def test_non_dataclass():
    with pytest.raises(ValueError):
        IniData(NonDataclass)


@m.context("When the INI file is present")
@m.it("Populates a dataclass")
def test_populate_from_ini_file(tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val1 = "value1"
    val2 = "value2"
    ini_file.write_text(f"[{section}]\nkey1={val1}\nkey2={val2}\n")

    parser = IniData(ExampleConfig)
    assert parser.from_file(ini_file, section) == ExampleConfig(key1=val1, key2=val2)


@m.context("When a field required by the dataclass is absent")
@m.it("Raises a TypeError")
def test_missing_required_value(tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val2 = "value2"
    ini_file.write_text(f"[{section}]\nkey2={val2}\n")

    parser = IniData(ExampleConfig)
    with pytest.raises(TypeError):
        parser.from_file(ini_file, section)


@m.context("When an optional field is absent")
@m.it("Populates a dataclass")
def test_missing_non_required_value(tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val1 = "value1"
    ini_file.write_text(f"[{section}]\nkey1={val1}\n")

    parser = IniData(ExampleConfig)
    assert parser.from_file(ini_file, section) == ExampleConfig(key1=val1)


@m.context("When environment variables are not to be used")
@m.it("Does not fall back to environment variables when a field is absent")
def test_no_env_fallback(monkeypatch, tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val1 = "value1"
    ini_file.write_text(f"[{section}]\nkey1={val1}\n")

    env_val2 = "environment_value2"
    monkeypatch.setenv("KEY2", env_val2)

    parser = IniData(ExampleConfig, use_env=False)

    assert parser.from_file(ini_file, section) == ExampleConfig(key1=val1, key2=None)


@m.context("When environment variables are to be used")
@m.it("Falls back to environment variables when a field is absent")
def test_env_fallback(monkeypatch, tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val1 = "value1"
    ini_file.write_text(f"[{section}]\nkey1={val1}\n")

    env_val2 = "environment_value2"
    monkeypatch.setenv("KEY2", env_val2)

    parser = IniData(ExampleConfig, use_env=True)
    assert parser.from_file(ini_file, section) == ExampleConfig(
        key1=val1, key2=env_val2
    )


@m.context("When environment variables are to be used with a prefix")
@m.it("Falls back to environment variables with a prefix when a field is absent")
def test_env_fallback_with_prefix(monkeypatch, tmp_path):
    ini_file = tmp_path / "config.ini"
    section = "test"
    val1 = "value1"
    ini_file.write_text(f"[{section}]\nkey1={val1}\n")

    env_val2 = "environment_value2"
    monkeypatch.setenv("EXAMPLE_KEY2", env_val2)

    parser = IniData(ExampleConfig, use_env=True, env_prefix="EXAMPLE_")
    assert parser.from_file(ini_file, section) == ExampleConfig(
        key1=val1, key2=env_val2
    )
