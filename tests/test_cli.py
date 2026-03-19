# -*- coding: utf-8 -*-
#
# Copyright © 2025, 2026 Genome Research Ltd. All rights reserved.
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

import pytest
from pytest import mark as m

from npg.cli import add_logging_arguments, open_input, open_output


@m.describe("CLI argument parsing")
class TestArgParser:
    @m.context("When logging options are mutually exclusive")
    @m.it(
        "Rejects mixing --log-config with --debug/--verbose and --debug with --verbose"
    )
    def test_logging_args_config_group(self):
        p1 = argparse.ArgumentParser()
        add_logging_arguments(p1)
        with pytest.raises(SystemExit):
            p1.parse_args(["--log-config", "config.json", "--debug"])

        p2 = argparse.ArgumentParser()
        add_logging_arguments(p2)
        with pytest.raises(SystemExit):
            p2.parse_args(["--log-config", "config.json", "--verbose"])

        p3 = argparse.ArgumentParser()
        add_logging_arguments(p3)
        with pytest.raises(SystemExit):
            p3.parse_args(["--debug", "--verbose"])

    @m.context("When log formatting options are mutually exclusive")
    @m.it("Rejects using --colour and --log-json together")
    def test_logging_args_format_group(self):
        parser = argparse.ArgumentParser()
        add_logging_arguments(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--colour", "--log-json"])


@m.describe("CLI input/output stream helpers")
class TestOpenInputOutput:
    @pytest.mark.parametrize("path", ["-", None])
    @m.context("When reading text from a default input path")
    @m.it("Uses sys.stdin for '-' or None")
    def test_open_input_uses_stdin_text_for_default_path(self, path):
        with open_input(path, "rt") as stream:
            assert stream is sys.stdin

    @pytest.mark.parametrize("path", ["-", None])
    @m.context("When reading binary data from a default input path")
    @m.it("Uses sys.stdin.buffer for '-' or None")
    def test_open_input_uses_stdin_binary_for_default_path(self, path):
        with open_input(path, "rb") as stream:
            assert stream is sys.stdin.buffer

    @m.context("When reading from a file path")
    @m.it("Opens the file and closes it when exiting the context")
    def test_open_input_opens_and_closes_file(self, tmp_path):
        path = tmp_path / "input.txt"
        path.write_text("hello\n", encoding="utf-8")

        with open_input(str(path), "rt") as stream:
            assert stream.read() == "hello\n"

        assert stream.closed

    @m.context("When reading from a file path with an explicit encoding")
    @m.it("Passes encoding through to Path.open")
    def test_open_input_passes_encoding_kwarg_to_path_open(self, tmp_path):
        path = tmp_path / "input-utf16.txt"
        expected = "hello café\n"
        path.write_text(expected, encoding="utf-16")

        with open_input(str(path), "rt", encoding="utf-16") as stream:
            assert stream.read() == expected

        with open_input(str(path), "rt", encoding="latin-1") as stream:
            assert stream.read() != expected

    @pytest.mark.parametrize("path", ["-", None])
    @m.context("When writing text to a default output path")
    @m.it("Uses sys.stdout for '-' or None")
    def test_open_output_uses_stdout_text_for_default_path(self, path):
        with open_output(path, "wt") as stream:
            assert stream is sys.stdout

    @pytest.mark.parametrize("path", ["-", None])
    @m.context("When writing binary data to a default output path")
    @m.it("Uses sys.stdout.buffer for '-' or None")
    def test_open_output_uses_stdout_binary_for_default_path(self, path):
        with open_output(path, "wb") as stream:
            assert stream is sys.stdout.buffer

    @m.context("When writing to a file path")
    @m.it("Opens the file, writes content, and closes it on context exit")
    def test_open_output_opens_and_closes_file(self, tmp_path):
        path = tmp_path / "output.txt"

        with open_output(str(path), "wt") as stream:
            stream.write("hello\n")

        assert stream.closed
        assert path.read_text(encoding="utf-8") == "hello\n"

    @m.context("When writing to a file path with an explicit encoding")
    @m.it("Passes encoding through to Path.open")
    def test_open_output_passes_encoding_kwarg_to_path_open(self, tmp_path):
        path = tmp_path / "output-utf16.txt"
        expected = "hello café\n"

        with open_output(str(path), "wt", encoding="utf-16") as stream:
            stream.write(expected)

        assert stream.closed
        assert path.read_text(encoding="utf-16") == expected
        assert path.read_text(encoding="latin-1") != expected
