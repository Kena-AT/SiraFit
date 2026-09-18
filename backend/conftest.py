import os
import sys
import pytest

# Ensure root directory is on sys.path so tests.conftest is importable
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from tests.conftest import *  # noqa: F401, F403


@pytest.fixture(scope="function")
def db_session(db):
    """Alias db fixture to db_session for legacy tests."""
    return db
