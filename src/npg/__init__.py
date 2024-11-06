import importlib.metadata

__version__ = importlib.metadata.version("npg-python-lib")


def version() -> str:
    """Return the current version."""
    return __version__
