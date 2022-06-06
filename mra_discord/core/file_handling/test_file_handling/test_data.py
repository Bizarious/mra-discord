from pathlib import Path

import pytest

from core.file_handling import data


_TEST_DATA = Path("test_data")
_TEST_SUB_DATA = Path("test2")
_TEST_FILE = Path("test.json")


@pytest.fixture(scope="session", autouse=True)
def init_data_path():
    data.set_data_path(_TEST_DATA)
    yield
    _TEST_DATA.rmdir()


@pytest.fixture(scope="function", autouse=True)
def remove_test_file():
    yield
    data.clear_data_elements()
    if Path(f"{_TEST_DATA}/{_TEST_SUB_DATA}").exists():
        Path.rmdir(Path(f"{_TEST_DATA}/{_TEST_SUB_DATA}"))


def test_data_create_right_data_object_with_default_value():
    d = data.get_json_data(_TEST_FILE)
    assert {} == d


def test_data_create_right_data_object():
    d = data.get_json_data(_TEST_FILE, [1, 2, 3])
    assert [1, 2, 3] == d


def test_data_get_already_created_object():
    d1 = data.get_json_data(_TEST_FILE, [1, 2, 3])
    d2 = data.get_json_data(_TEST_FILE)
    assert d1 == d2


def test_data_create_sub_folder():
    p = Path(f"{_TEST_SUB_DATA}/{_TEST_FILE}")
    data.get_json_data(Path(p))
    assert Path(f"{_TEST_DATA}/{_TEST_SUB_DATA}").exists()
