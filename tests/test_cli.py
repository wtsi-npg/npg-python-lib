# -*- coding: utf-8 -*-
#
# Copyright © 2025 Genome Research Ltd. All rights reserved.
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

import pytest

from npg.cli import add_logging_arguments


class TestArgParser:
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

    def test_logging_args_format_group(self):
        parser = argparse.ArgumentParser()
        add_logging_arguments(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--colour", "--log-json"])
