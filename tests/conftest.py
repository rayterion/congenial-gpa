# tests/conftest.py

import pytest
from scripts.dev_db import down_dev_db, up_dev_db


@pytest.fixture(scope="session", autouse=True)
def before_all_tests():
    print("Running setup before all tests")
    up_dev_db()

    yield

    print("Running cleanup after all tests")
    down_dev_db()