# Vendored SQLAlchemy-Utils database helpers

Source: https://github.com/kvesteri/sqlalchemy-utils
Release: 0.42.1 (BSD-3-Clause)
Archive: https://files.pythonhosted.org/packages/0f/7d/eb9565b6a49426552a5bf5c57e7c239c506dc0e4e5315aec6d1e8241dc7c/sqlalchemy_utils-0.42.1.tar.gz
Archive SHA-256: `881f9cd9e5044dc8f827bccb0425ce2e55490ce44fc0bb848c55cc8ee44cc02e`

## Extraction and local changes

- `database.py`: copied `create_database`, `database_exists`, and `drop_database`,
  plus support functions `_set_url_database`, `_get_scalar_result`, and 
  `_sqlite_file_exists` from `sqlalchemy_utils/functions/database.py`.
- `orm.py`: copied `get_bind` and `quote` from `sqlalchemy_utils/functions/orm.py`.
- Retained only the imports required by these functions; changed the `quote` import
  to `.orm`. Added attribution headers and package initialisers. Function bodies,
  signatures, docstrings, and backend branches are unchanged.
- `LICENSE` is the unmodified upstream licence.
- `tests/db/test_database.py` adapts the SQLite lifecycle and existence scenarios
  from upstream `tests/functions/test_database.py`, with attribution.

SQLAlchemy remains an external dependency, supported here at `>=2,<3` via the
`db` extra. Applications install any required database drivers themselves.

Import the supported API from `npg.db`; this package is private.

## Updating

Download a stable upstream source archive and verify its SHA-256. Re-extract
only the functions listed above and their necessary imports, checking for new
helper dependencies. Preserve the upstream licence and update the release,
archive URL, checksum, and local-change list here. Review upstream changes and
run the local database tests and full suite. Check that both the source and
wheel distributions include this README, the licence, and the vendored modules.

## Security

- Existence queries interpolate database names into SQL literals; encoding is
  also interpolated into creation SQL. Inputs must be trusted configuration.
