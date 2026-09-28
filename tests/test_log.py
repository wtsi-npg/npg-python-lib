# -*- coding: utf-8 -*-
#
# Copyright © 2026 Genome Research Ltd. All rights reserved.
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
import json
import logging
from contextlib import contextmanager
from pathlib import Path

import structlog
from pytest import CaptureFixture
from pytest import mark as m

from npg.log import configure_structlog


@m.describe("configure_structlog")
class TestConfigureStructlog:
    @m.context("When configuring with default options")
    @m.it("Logs to stderr")
    def test_normal_defaults(self, capsys: CaptureFixture):
        # Act
        with reset_logging():
            configure_structlog()
            log = structlog.stdlib.get_logger()
            log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" in stderr
        assert not "CRITICAL" in stderr

    @m.context("When configuring with config file specifying logging to file")
    @m.it("Logs to file")
    def test_normal_config_file(self, capsys: CaptureFixture, tmp_path: Path):
        # Arrange
        config_file = tmp_path / "logging.json"
        log_path = tmp_path / "test.log"
        config_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "disable_existing_loggers": False,
                    "loggers": {
                        "root": {
                            "level": "INFO",
                            "handlers": [
                                "file",
                            ],
                        }
                    },
                    "handlers": {
                        "file": {
                            "class": "logging.FileHandler",
                            "level": "INFO",
                            "formatter": "simple",
                            "filename": str(log_path),
                            "mode": "a",
                        }
                    },
                    "formatters": {"simple": {"format": "%(message)s"}},
                }
            )
        )

        # Act
        with reset_logging():
            configure_structlog(config_file)
            log = structlog.stdlib.get_logger()
            log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" not in stderr
        assert "Test Message" in log_path.read_text()
        assert "CRITICAL" not in stderr
        assert "CRITICAL" not in log_path.read_text()

    @m.context("When configuring with missing config file")
    @m.it("Falls back to default log to stderr behaviour")
    @m.it("and logs a CRITICAL error to stderr")
    def test_error(self, capsys: CaptureFixture):
        # Act
        with reset_logging():
            configure_structlog("missing-logging.json")
            log = structlog.stdlib.get_logger()
            log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" in stderr
        assert "CRITICAL" in stderr


@contextmanager
def reset_logging():
    """
    Resets logging before and after each test to isolate a test from pytest
    logging plugin and other tests.

    Logging has global state which is modified by pytest logging plugin and
    may be modified by a test.

    logging.basicConfig does nothing if root logger already has handlers configured.

    Disables caplog functionality.

    pytest installs its per-test logging handlers after fixture setup, so
    logging must be reset from within the test call itself hence in test context
    manager rather than fixture.
    """

    # Remove pytest logging plugin
    root = logging.getLogger()
    pytest_handlers = root.handlers[:]
    original_level = root.level

    root.handlers.clear()
    structlog.reset_defaults()

    try:
        yield

    finally:
        # Remove test handlers
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            if handler not in pytest_handlers:
                handler.close()

        # Restore pytest logging plugin
        root.handlers[:] = pytest_handlers
        root.setLevel(original_level)
        structlog.reset_defaults()
