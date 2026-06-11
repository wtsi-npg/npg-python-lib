# -*- coding: utf-8 -*-
#
# Copyright © 2024, 2025, 2026 Genome Research Ltd. All rights reserved.
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
import logging
from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import pytest
from pytest import mark as m
from structlog.testing import capture_logs

from npg.conf import IniData, TomlData, config_class


@dataclass
class ConfigWithSecret:
    secret: str = field(repr=False)
    key1: str
    key2: Optional[str] = None


@dataclass
class ConfigWithBuiltinTypes:
    key1: int
    key2: float
    key3: bool


@dataclass
class ConfigWithOptionalBuiltinTypes:
    key1: Optional[int]
    key2: Optional[float]
    key3: Optional[bool]


@dataclass
class ConfigWithPathType:
    key1: Path


class NonDataclass:
    """An example non-dataclass for testing."""

    pass


class CustomValue:
    def __init__(self, val):
        self.val = val

    def __hash__(self):
        return hash(self.val)

    def __eq__(self, other):
        return self.val == other.val

    def __repr__(self):
        return f"<CustomValue '{self.val}'>"


@dataclass
class ConfigWithCustomValue:
    key1: CustomValue
    key2: str


class CustomValueIniData(IniData):
    def parse_ini_value(self, parser: ConfigParser, section: str, _field, hint) -> Any:
        if hint is CustomValue:
            return CustomValue(parser.get(section, _field.name))

        return super().parse_ini_value(parser, section, _field, hint)

    def parse_environment_value(self, val: str, hint) -> Any:
        if hint is CustomValue:
            return CustomValue(val)

        return super().parse_environment_value(val, hint)


class CustomValueTomlData(TomlData):
    def parse_toml_value(self, val: Any, _field, hint) -> Any:
        if hint is CustomValue:
            return CustomValue(val)

        return super().parse_toml_value(val, _field, hint)

    def parse_environment_value(self, val: str, hint) -> Any:
        if hint is CustomValue:
            return CustomValue(val)

        return super().parse_environment_value(val, hint)


@m.describe("IniData")
class TestIniData:
    @m.context("When the INI file is missing")
    @m.it("Raises a FileNotFoundError")
    def test_missing_ini_file(self, tmp_path):
        ini_file = tmp_path / "missing.ini"

        parser = IniData(ConfigWithSecret)
        with pytest.raises(FileNotFoundError):
            parser.from_file(ini_file, "section")

    @m.context("When the dataclass is missing")
    @m.it("Raises a ValueError")
    def test_invalid_dataclass(self):
        with pytest.raises(ValueError):
            IniData(None)

    @m.context("When the dataclass is a non-dataclass")
    @m.it("Raises a ValueError")
    def test_non_dataclass(self):
        with pytest.raises(ValueError):
            IniData(NonDataclass)

    @m.context("When the INI file is present")
    @m.it("Populates a dataclass")
    def test_populate_from_ini_file(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        val2 = "value2"
        ini_file.write_text(f"[{section}]\nsecret={secret}\nkey1={val1}\nkey2={val2}\n")

        parser = IniData(ConfigWithSecret)
        assert parser.from_file(ini_file, section) == ConfigWithSecret(
            key1=val1, key2=val2, secret=secret
        )

    @m.context("When a field required by the dataclass is absent")
    @m.it("Raises a TypeError")
    def test_missing_required_value(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val2 = "value2"
        ini_file.write_text(f"[{section}]\nkey2={val2}\n")

        parser = IniData(ConfigWithSecret)
        with pytest.raises(TypeError):
            parser.from_file(ini_file, section)

    @m.context("When an optional field is absent")
    @m.it("Populates a dataclass")
    def test_missing_non_required_value(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        ini_file.write_text(f"[{section}]\nsecret={secret}\nkey1={val1}\n")

        parser = IniData(ConfigWithSecret)
        assert parser.from_file(ini_file, section) == ConfigWithSecret(
            key1=val1, secret=secret
        )

    @m.context("When environment variables are not to be used")
    @m.it("Does not fall back to environment variables when a field is absent")
    def test_no_env_fallback(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = "value1"
        secret = "SECRET_VALUE"
        ini_file.write_text(f"[{section}]\nsecret={secret}\nkey1={val1}\n")

        env_val2 = "environment_value2"
        with patch.dict("os.environ", {"KEY2": env_val2}):
            parser = IniData(ConfigWithSecret, use_env=False)
            assert parser.from_file(ini_file, section) == ConfigWithSecret(
                secret=secret, key1=val1, key2=None
            )

    @m.context("When environment variables are to be used")
    @m.it("Falls back to environment variables when a field is absent")
    def test_env_fallback(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = "value1"
        ini_file.write_text(f"[{section}]\nsecret=SECRET_VALUE\nkey1={val1}\n")

        env_val2 = "environment_value2"
        with patch.dict("os.environ", {"KEY2": env_val2}):
            parser = IniData(ConfigWithSecret, use_env=True)
            assert parser.from_file(ini_file, section) == ConfigWithSecret(
                key1=val1, key2=env_val2, secret="SECRET_VALUE"
            )

    @m.context("When environment variables are to be used with a prefix")
    @m.it("Falls back to environment variables with a prefix when a field is absent")
    def test_env_fallback_with_prefix(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        ini_file.write_text(f"[{section}]\nsecret={secret}\nkey1={val1}\n")

        env_val2 = "environment_value2"

        with patch.dict("os.environ", {"EXAMPLE_KEY2": env_val2}):
            parser = IniData(ConfigWithSecret, use_env=True, env_prefix="EXAMPLE_")
            assert parser.from_file(ini_file, section) == ConfigWithSecret(
                key1=val1, key2=env_val2, secret=secret
            )

    @m.context("When the config class includes a secret field")
    @m.it("Does not include the secret field in the representation")
    def test_secret_repr(self):
        assert (
            repr(ConfigWithSecret(secret="SECRET_VALUE", key1="value1"))
            == "ConfigWithSecret(key1='value1', key2=None)"
        )

    @m.context("When the config class includes a secret field")
    @m.it("Does not include the secret field in the debug log")
    def test_secret_debug(self, tmp_path, caplog):
        ini_file = tmp_path / "config.ini"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        ini_file.write_text(f"[{section}]\nsecret={secret}\nkey1={val1}\n")

        with caplog.at_level(logging.DEBUG):
            with capture_logs() as cap_logs:
                IniData(ConfigWithSecret).from_file(ini_file, section)

                found_log = False
                found_secret = False

                for log in cap_logs:
                    if "event" in log and log["event"] == "Reading complete":
                        found_log = True
                        if str(log).find(secret) >= 0:
                            found_secret = True

                assert found_log
                assert not found_secret

    @m.context("When the config class includes an int, float or bool field")
    @m.it("Converts the value to the declared type")
    def test_typed_fields_file(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = 1
        val2 = 1.0
        val3 = True
        ini_file.write_text(f"[{section}]\nkey1={val1}\nkey2={val2}\nkey3={val3}\n")

        parser = IniData(ConfigWithBuiltinTypes)
        assert parser.from_file(ini_file, section) == ConfigWithBuiltinTypes(
            key1=val1, key2=val2, key3=val3
        )

    @m.context("When the config class includes an Optional int, float or bool field")
    @m.it("Converts the value to the declared type")
    def test_optional_typed_fields_file(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = ""
        val2 = ""
        val3 = ""
        ini_file.write_text(f"[{section}]\nkey1={val1}\nkey2={val2}\nkey3={val3}\n")

        parser = IniData(ConfigWithOptionalBuiltinTypes)
        assert parser.from_file(ini_file, section) == ConfigWithOptionalBuiltinTypes(
            None, None, None
        )

    @m.context("When the configuration class includes a Path field")
    @m.it("Converts the value to a Path object")
    def test_path_field_file(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = "/usr/bin"
        ini_file.write_text(f"[{section}]\nkey1={val1}\n")

        parser = IniData(ConfigWithPathType)
        assert parser.from_file(ini_file, section) == ConfigWithPathType(
            key1=Path(val1)
        )

    @m.context("When environment variables populate int, float or bool fields")
    @m.it("Converts the value to the expected type")
    def test_typed_fields_env(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = ""
        val2 = ""
        val3 = ""
        ini_file.write_text(f"[{section}]\nkey1={val1}\nkey2={val2}\nkey3={val3}\n")

        env_val1 = "1"
        env_val2 = "1.0"
        env_val3 = "true"
        with patch.dict(
            "os.environ", {"KEY1": env_val1, "KEY2": env_val2, "KEY3": env_val3}
        ):
            parser = IniData(ConfigWithBuiltinTypes, use_env=True)
            assert parser.from_file(ini_file, section) == ConfigWithBuiltinTypes(
                1, 1.0, True
            )

    @m.context("When the config class includes a custom value")
    @m.it("Converts the custom value to the declared type")
    def test_custom_value_file(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val1 = "value1"
        val2 = "value2"
        ini_file.write_text(f"[{section}]\nkey1={val1}\nkey2={val2}\n")

        parser = CustomValueIniData(ConfigWithCustomValue)
        assert parser.from_file(ini_file, section) == ConfigWithCustomValue(
            key1=CustomValue(val1), key2=val2
        )

    @m.context("When environment variables populate custom values")
    @m.it("Converts the custom value to the declared type")
    def test_custom_value_env(self, tmp_path):
        ini_file = tmp_path / "config.ini"
        section = "test"
        val2 = "value2"
        ini_file.write_text(f"[{section}]\nkey2={val2}\n")

        env_val1 = "valueX"
        with patch.dict("os.environ", {"KEY1": env_val1}):
            parser = CustomValueIniData(ConfigWithCustomValue, use_env=True)
            assert parser.from_file(ini_file, section) == ConfigWithCustomValue(
                key1=CustomValue(env_val1), key2=val2
            )


@m.describe("TomlData")
class TestTomlData:
    @m.context("When the TOML file is missing")
    @m.it("Raises a FileNotFoundError")
    def test_missing_toml_file(self, tmp_path):
        toml_file = tmp_path / "missing.toml"

        parser = TomlData(ConfigWithSecret)
        with pytest.raises(FileNotFoundError):
            parser.from_file(toml_file, "section")

    @m.context("When the dataclass is missing")
    @m.it("Raises a ValueError")
    def test_invalid_dataclass(self):
        with pytest.raises(ValueError):
            TomlData(None)

    @m.context("When the dataclass is a non-dataclass")
    @m.it("Raises a ValueError")
    def test_non_dataclass(self):
        with pytest.raises(ValueError):
            TomlData(NonDataclass)

    @m.context("When the TOML file is present")
    @m.it("Populates a dataclass")
    def test_populate_from_toml_file(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        val2 = "value2"
        toml_file.write_text(
            f'[{section}]\nsecret = "{secret}"\nkey1 = "{val1}"\nkey2 = "{val2}"\n'
        )

        parser = TomlData(ConfigWithSecret)
        assert parser.from_file(toml_file, section) == ConfigWithSecret(
            key1=val1, key2=val2, secret=secret
        )

    @m.context("When a field required by the dataclass is absent")
    @m.it("Raises a TypeError")
    def test_missing_required_value(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val2 = "value2"
        toml_file.write_text(f'[{section}]\nkey2 = "{val2}"\n')

        parser = TomlData(ConfigWithSecret)
        with pytest.raises(TypeError):
            parser.from_file(toml_file, section)

    @m.context("When an optional field is absent")
    @m.it("Populates a dataclass")
    def test_missing_non_required_value(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        toml_file.write_text(f'[{section}]\nsecret = "{secret}"\nkey1 = "{val1}"\n')

        parser = TomlData(ConfigWithSecret)
        assert parser.from_file(toml_file, section) == ConfigWithSecret(
            key1=val1, secret=secret
        )

    @m.context("When environment variables are not to be used")
    @m.it("Does not fall back to environment variables when a field is absent")
    def test_no_env_fallback(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = "value1"
        secret = "SECRET_VALUE"
        toml_file.write_text(f'[{section}]\nsecret = "{secret}"\nkey1 = "{val1}"\n')

        env_val2 = "environment_value2"
        with patch.dict("os.environ", {"KEY2": env_val2}):
            parser = TomlData(ConfigWithSecret, use_env=False)
            assert parser.from_file(toml_file, section) == ConfigWithSecret(
                secret=secret, key1=val1, key2=None
            )

    @m.context("When environment variables are to be used")
    @m.it("Falls back to environment variables when a field is absent")
    def test_env_fallback(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = "value1"
        toml_file.write_text(f'[{section}]\nsecret = "SECRET_VALUE"\nkey1 = "{val1}"\n')

        env_val2 = "environment_value2"
        with patch.dict("os.environ", {"KEY2": env_val2}):
            parser = TomlData(ConfigWithSecret, use_env=True)
            assert parser.from_file(toml_file, section) == ConfigWithSecret(
                key1=val1, key2=env_val2, secret="SECRET_VALUE"
            )

    @m.context("When environment variables are to be used with a prefix")
    @m.it("Falls back to environment variables with a prefix when a field is absent")
    def test_env_fallback_with_prefix(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        toml_file.write_text(f'[{section}]\nsecret = "{secret}"\nkey1 = "{val1}"\n')

        env_val2 = "environment_value2"

        with patch.dict("os.environ", {"EXAMPLE_KEY2": env_val2}):
            parser = TomlData(ConfigWithSecret, use_env=True, env_prefix="EXAMPLE_")
            assert parser.from_file(toml_file, section) == ConfigWithSecret(
                key1=val1, key2=env_val2, secret=secret
            )

    @m.context("When the config class includes a secret field")
    @m.it("Does not include the secret field in the representation")
    def test_secret_repr(self):
        assert (
            repr(ConfigWithSecret(secret="SECRET_VALUE", key1="value1"))
            == "ConfigWithSecret(key1='value1', key2=None)"
        )

    @m.context("When the config class includes a secret field")
    @m.it("Does not include the secret field in the debug log")
    def test_secret_debug(self, tmp_path, caplog):
        toml_file = tmp_path / "config.toml"
        section = "test"
        secret = "SECRET_VALUE"
        val1 = "value1"
        toml_file.write_text(f'[{section}]\nsecret = "{secret}"\nkey1 = "{val1}"\n')

        with caplog.at_level(logging.DEBUG):
            with capture_logs() as cap_logs:
                TomlData(ConfigWithSecret).from_file(toml_file, section)

                found_log = False
                found_secret = False

                for log in cap_logs:
                    if "event" in log and log["event"] == "Reading complete":
                        found_log = True
                        if str(log).find(secret) >= 0:
                            found_secret = True

                assert found_log
                assert not found_secret

    @m.context("When the config class includes an int, float or bool field")
    @m.it("Converts the value to the declared type")
    def test_typed_fields_file(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = 1
        val2 = 1.0
        val3 = True
        toml_file.write_text(
            f"[{section}]\nkey1 = {val1}\nkey2 = {val2}\nkey3 = {str(val3).lower()}\n"
        )

        parser = TomlData(ConfigWithBuiltinTypes)
        assert parser.from_file(toml_file, section) == ConfigWithBuiltinTypes(
            key1=val1, key2=val2, key3=val3
        )

    @m.context("When the config class includes an Optional int, float or bool field")
    @m.it("Converts the value to the declared type")
    def test_optional_typed_fields_file(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = ""
        val2 = ""
        val3 = ""
        toml_file.write_text(
            f'[{section}]\nkey1 = "{val1}"\nkey2 = "{val2}"\nkey3 = "{val3}"\n'
        )

        parser = TomlData(ConfigWithOptionalBuiltinTypes)
        assert parser.from_file(toml_file, section) == ConfigWithOptionalBuiltinTypes(
            None, None, None
        )

    @m.context("When the configuration class includes a Path field")
    @m.it("Converts the value to a Path object")
    def test_path_field_file(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = "/usr/bin"
        toml_file.write_text(f'[{section}]\nkey1 = "{val1}"\n')

        parser = TomlData(ConfigWithPathType)
        assert parser.from_file(toml_file, section) == ConfigWithPathType(
            key1=Path(val1)
        )

    @m.context("When environment variables populate int, float or bool fields")
    @m.it("Converts the value to the expected type")
    def test_typed_fields_env(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        toml_file.write_text(f"[{section}]\n")

        env_val1 = "1"
        env_val2 = "1.0"
        env_val3 = "true"
        with patch.dict(
            "os.environ", {"KEY1": env_val1, "KEY2": env_val2, "KEY3": env_val3}
        ):
            parser = TomlData(ConfigWithBuiltinTypes, use_env=True)
            assert parser.from_file(toml_file, section) == ConfigWithBuiltinTypes(
                1, 1.0, True
            )

    @m.context("When the config class includes a custom value")
    @m.it("Converts the custom value to the declared type")
    def test_custom_value_file(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val1 = "value1"
        val2 = "value2"
        toml_file.write_text(f'[{section}]\nkey1 = "{val1}"\nkey2 = "{val2}"\n')

        parser = CustomValueTomlData(ConfigWithCustomValue)
        assert parser.from_file(toml_file, section) == ConfigWithCustomValue(
            key1=CustomValue(val1), key2=val2
        )

    @m.context("When environment variables populate custom values")
    @m.it("Converts the custom value to the declared type")
    def test_custom_value_env(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        section = "test"
        val2 = "value2"
        toml_file.write_text(f'[{section}]\nkey2 = "{val2}"\n')

        env_val1 = "valueX"
        with patch.dict("os.environ", {"KEY1": env_val1}):
            parser = CustomValueTomlData(ConfigWithCustomValue, use_env=True)
            assert parser.from_file(toml_file, section) == ConfigWithCustomValue(
                key1=CustomValue(env_val1), key2=val2
            )


@config_class
class ConfigWithFieldVariations:
    auto_hidden: str  # A field we want to be automatically hidden i.e. a secret
    explicit_visible: str = field(repr=True)  # A field we explicitly specify visible
    explicit_hidden: str = field(repr=False)  # A field we explicitly specify hidden
    non_repr: str = field(
        default="non_repr"
    )  # A field where we've configured a non-repr property
    class_default: str = "class_default"  # A field with a class default
    attribute = "attribute"  # An attribute that's not a dataclass field


@m.describe("config_class")
class TestConfig:
    @m.context(
        "When a field is specified with type annotation and no default value or field call"
    )
    @m.it("Does not include the field in string representation")
    def test_auto_hidden(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "auto_hidden" not in str(config)
        assert "auto_hidden" not in repr(config)

    @m.context("When a field is explicitly specified visible")
    @m.it("Includes the field in string representation")
    def test_explicit_visible(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "explicit_visible" in str(config)
        assert "explicit_visible" in repr(config)

    @m.context("When a field is explicitly specified hidden")
    @m.it("Does not include the field in string representation")
    def test_explicit_hidden(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "explicit_hidden" not in str(config)
        assert "explicit_hidden" not in repr(config)

    @m.context("When field used without specifying repr")
    @m.it("Includes the field in string representation")
    def test_non_repr(self):
        # Test documents accepted limitation
        # When someone uses field without specifying get the repr=True default
        # There isn't a way within decorator to distinguish between someone having
        # explicitly specified repr=True or used the default
        # There are alternatives like providing a config_field with different defaults
        # and forcing use within config_class but decided against

        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "non_repr" in str(config)
        assert "non_repr" in repr(config)

    @m.context("When a field has a class default")
    @m.it("Does not include the field in string representation")
    def test_class_default(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "class_default" not in str(config)
        assert "class_default" not in repr(config)
        assert config.class_default == "class_default"

        # Whilst we create an intermediary field, we still end up with same end point
        # of class attribute containing default value
        # https://docs.python.org/3/library/dataclasses.html#dataclasses.field
        assert ConfigWithFieldVariations.class_default == "class_default"

    @m.context("When a field has an attribute that's not a dataclass field")
    @m.it("Does not include the field in string representation")
    def test_attribute(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "attribute" not in str(config)
        assert "attribute" not in repr(config)
        assert config.attribute == "attribute"

    @m.it("Prevents modifying fields")
    def test_modifying_fields(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            config.auto_hidden = "modified"
        assert config.auto_hidden == "auto_hidden"

        # Accepted limitation
        # Could set slots=True but solution becomes harder to understand
        config.__dict__["auto_hidden"] = "modified"
        assert config.auto_hidden == "modified"

    @m.it("Prevents adding fields")
    def test_adding_fields(self):
        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            config.another_secret = "another_secret"
        assert not hasattr(config, "another_secret")

        # Could set slots=True but solution becomes harder to understand
        config.__dict__["another_secret"] = "another_secret"
        assert config.another_secret == "another_secret"

    @m.context("When interact with as dict")
    @m.it("Includes hidden fields in string representation")
    def test_accepted_limitations(self):
        # Test documents accepted limitation
        # Could mitigate with custom Secret class

        config = ConfigWithFieldVariations(
            "auto_hidden", "explicit_visible", "explicit_hidden"
        )

        assert "auto_hidden" in str(dataclasses.asdict(config))
        assert "auto_hidden" in str(config.__dict__)


@m.describe("IniData and config_class")
class TestIniDataConfigClass:
    @m.context("When IniData used with @config_class")
    @m.it("Populates fields and doesn't log hidden fields")
    def test_ini_data_config_class(self, tmp_path, caplog):
        ini_file = tmp_path / "config.ini"
        section = "section"
        ini_file.write_text(
            f"[{section}]\nauto_hidden=auto_hidden\nexplicit_visible=explicit_visible\nexplicit_hidden=explicit_hidden\nattribute=should_ignore\n"
        )

        with caplog.at_level(logging.DEBUG):
            with capture_logs() as cap_logs:
                config = IniData(ConfigWithFieldVariations).from_file(ini_file, section)

                assert config == ConfigWithFieldVariations(
                    "auto_hidden", "explicit_visible", "explicit_hidden"
                )
                all_logs = str(cap_logs)
                assert "auto_hidden" not in all_logs
                assert "explicit_hidden" not in all_logs
                assert "class_default" not in all_logs
                assert "attribute" not in all_logs
                assert "explicit_visible" in all_logs
                assert "non_repr" in all_logs, "Accepted limitation"


@m.describe("TomlData and config_class")
class TestTomlDataConfigClass:
    @m.context("When TomlData used with @config_class")
    @m.it("Populates fields and doesn't log hidden fields")
    def test_toml_data_config_class(self, tmp_path, caplog):
        toml_file = tmp_path / "config.ini"
        section = "section"
        toml_file.write_text(
            f'[{section}]\nauto_hidden = "auto_hidden"\nexplicit_visible = "explicit_visible"\nexplicit_hidden = "explicit_hidden"\nattribute = "should_ignore"\n'
        )

        with caplog.at_level(logging.DEBUG):
            with capture_logs() as cap_logs:
                config = TomlData(ConfigWithFieldVariations).from_file(
                    toml_file, section
                )

                assert config == ConfigWithFieldVariations(
                    "auto_hidden", "explicit_visible", "explicit_hidden"
                )
                all_logs = str(cap_logs)
                assert "auto_hidden" not in all_logs
                assert "explicit_hidden" not in all_logs
                assert "class_default" not in all_logs
                assert "attribute" not in all_logs
                assert "explicit_visible" in all_logs
                assert "non_repr" in all_logs, "Accepted limitation"
