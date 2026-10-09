# npg-python-lib

A library of Python functions and classes common to NPG applications.

# Summary

This library covers commonly used topics such as command line interfaces,
logging configuration, and basic data structures.


## Database helpers

Install the optional database support and a driver for your database backend:

```sh
pip install 'npg-python-lib[db]'
```

```python
from npg.db import create_database, database_exists, drop_database

url = "sqlite:///example.sqlite"
if not database_exists(url):
    create_database(url)
# When the database is no longer needed:
drop_database(url)
```

These synchronous functions accept a SQLAlchemy URL string or `URL` object.
`create_database(url, encoding="utf8", template=None)` also accepts an encoding
and a PostgreSQL template. The functions are vendored from SQLAlchemy-Utils
0.42.1 with upstream behaviour preserved; SQLAlchemy-Utils itself is not required.

Use a trusted connection configuration; database names are not sanitised by this code.
Database drivers are installed separately; SQLite uses Python's built-in driver.

See the [vendoring notes](src/npg/_vendor/sqlalchemy_utils/README.md) for source,
licence, update instructions, and preserved limitations, including explicit
in-memory SQLite creation/deletion errors. The supported import path is `npg.db`.
