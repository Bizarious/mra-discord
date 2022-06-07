import json
from pathlib import Path

import pytest

from core.file_handling.savable import DataDict, DataList

_TEST_FILES = Path("test_files")
_TEST_FILE = Path("test.json")
_TEST_PATH = Path(f"{_TEST_FILES}/{_TEST_FILE}")


@pytest.fixture(scope="session", autouse=True)
def handle_test_dir():
    _TEST_FILES.mkdir()
    yield
    _TEST_FILES.rmdir()


@pytest.fixture(scope="function", autouse=True)
def remove_test_file():
    yield
    _TEST_PATH.unlink(missing_ok=True)


def test_data_dict_save_right_data():
    provided = {"a": 1, "b": 2}
    data = DataDict(provided, path=_TEST_PATH)
    data["c"] = 3

    expected = {"a": 1, "b": 2, "c": 3}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_data_dict_save_right_data_recursive():
    provided = {"a": 1, "b": 2}
    data = DataDict(provided, path=_TEST_PATH)
    data["c"] = {}
    data["c"]["a"] = 1

    expected = {"a": 1, "b": 2, "c": {"a": 1}}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_data_dict_not_save_data():
    provided = {"a": 1, "b": 2}
    data = DataDict(provided, path=_TEST_PATH)
    data.save()
    data.do_save = False
    data["c"] = {}
    data["c"]["a"] = 1

    expected = {"a": 1, "b": 2}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_data_dict_bulk_save_data():
    provided = {"a": 1, "b": 2}
    data = DataDict(provided, path=_TEST_PATH)
    data.save()
    data.do_save = False
    data["c"] = {}
    data["c"]["a"] = 1

    expected_before = {"a": 1, "b": 2}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected_before

    data.do_save = True

    expected_after = {"a": 1, "b": 2, "c": {"a": 1}}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected_after


def test_data_dict_load_and_ignore_inital_value():
    pre_provided = {"a": 1, "b": 2}
    pre_data = DataDict(pre_provided, path=_TEST_PATH)
    pre_data.save()

    provided = {"b": 3}
    data = DataDict(provided, path=_TEST_PATH)
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == data


def test_data_list_save_right_data():
    provided = [1, 2, 3, 4]
    data = DataList(provided, path=_TEST_PATH)
    # noinspection PyArgumentList
    data.append(5)

    expected = [1, 2, 3, 4, 5]
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_data_list_save_right_data_recursive():
    provided = [1, 2, 3, 4]
    data = DataList(provided, path=_TEST_PATH)
    # noinspection PyArgumentList
    data.append([])
    data[4].append("a")

    expected = [1, 2, 3, 4, ["a"]]
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_data_list_not_save_data():
    provided = [1, 2, 3, 4]
    data = DataList(provided, path=_TEST_PATH)
    data.save()
    data.do_save = False
    # noinspection PyArgumentList
    data.append(5)

    expected = [1, 2, 3, 4]
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


# noinspection PyArgumentList
def test_data_list_bulk_save_data():
    provided = [1, 2, 3, 4]
    data = DataList(provided, path=_TEST_PATH)
    data.save()
    data.do_save = False
    data.append(5)
    data.append([])
    data[5].append("a")

    expected_before = [1, 2, 3, 4]
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected_before

    data.do_save = True

    expected_after = [1, 2, 3, 4, 5, ["a"]]
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected_after
