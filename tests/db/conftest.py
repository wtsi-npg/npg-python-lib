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
#

from pathlib import Path

import pytest
from sqlalchemy import URL, make_url


@pytest.fixture()
def sqlite_url(tmp_path, request):
    """Provide a new SQLite database URL."""
    return URL.create("sqlite", database=str(tmp_path / "test.sqlite"))


@pytest.fixture(params=[b"", b"not a database", b"x" * 100])
def invalid_sqlite_url(sqlite_url, request):
    """Provide files that fail SQLite size or header validation."""
    Path(make_url(sqlite_url).database).write_bytes(request.param)
    return sqlite_url
