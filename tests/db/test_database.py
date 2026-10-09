# SQLite lifecycle and existence scenarios adapted from SQLAlchemy-Utils 0.42.1
# tests/functions/test_database.py. Copyright (c) 2012, Konsta Vesterinen.
# All rights reserved. See src/npg/_vendor/sqlalchemy_utils/LICENSE (BSD-3-Clause).

from pathlib import Path

import pytest
from pytest import mark as m
from sqlalchemy import create_engine, inspect, make_url
from sqlalchemy.exc import OperationalError

from npg.db import create_database, database_exists, drop_database


@m.describe("SQLite database helpers")
class TestSQLite:
    @m.context("When given a missing database")
    @m.it("Creates a usable empty database and removes it")
    def test_create_and_drop(self, sqlite_url):
        original_url = make_url(sqlite_url)
        path = Path(original_url.database)

        assert not database_exists(sqlite_url)
        assert not path.exists()
        assert create_database(sqlite_url) is None
        assert database_exists(sqlite_url)

        engine = create_engine(sqlite_url)
        try:
            assert inspect(engine).get_table_names() == []
        finally:
            engine.dispose()

        assert drop_database(sqlite_url) is None
        assert not database_exists(sqlite_url)
        assert not path.exists()
        assert make_url(sqlite_url) == original_url

    @m.context("When a file lacks a valid SQLite header")
    @m.it("Reports that no database exists")
    def test_invalid_file(self, invalid_sqlite_url):
        assert not database_exists(invalid_sqlite_url)

    @m.context("When an existing file is empty")
    @m.it("Initialises it as a database")
    def test_empty_file(self, sqlite_url):
        Path(make_url(sqlite_url).database).touch()
        assert not database_exists(sqlite_url)

        create_database(sqlite_url)
        assert database_exists(sqlite_url)

        drop_database(sqlite_url)
        assert not database_exists(sqlite_url)

    @m.context("When the file is missing")
    @m.it("Propagates the deletion error")
    def test_drop_missing(self, sqlite_url):
        with pytest.raises(FileNotFoundError):
            drop_database(sqlite_url)

    @m.context("When SQLite has no database component")
    @m.it("Reports existence and treats creation and deletion as no-ops")
    def test_implicit_memory(self):
        assert database_exists("sqlite://")
        assert create_database("sqlite://") is None
        assert drop_database("sqlite://") is None

    @m.context("When the database is explicitly :memory:")
    @m.it("Preserves upstream existence and unsupported DDL behaviour")
    @pytest.mark.parametrize("operation", [create_database, drop_database])
    def test_explicit_memory(self, operation):
        assert database_exists("sqlite:///:memory:")
        with pytest.raises(OperationalError, match="syntax error"):
            operation("sqlite:///:memory:")
