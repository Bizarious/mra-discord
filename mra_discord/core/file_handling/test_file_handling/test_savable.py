import json
from pathlib import Path

import pytest

from core.file_handling.savable import DataDict, DataList

_TEST_FILES = "test_files"


@pytest.fixture(scope="session", autouse=True)
def handle_test_dir():
    p = Path(_TEST_FILES)
    p.mkdir()
    yield
    p.rmdir()


def test_data_dict_save_right_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = {"a": 1, "b": 2}
        data = DataDict(provided, path=path)
        data["c"] = 3

        expected = {"a": 1, "b": 2, "c": 3}
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


def test_data_dict_save_right_data_recursive():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = {"a": 1, "b": 2}
        data = DataDict(provided, path=path)
        data["c"] = {}
        data["c"]["a"] = 1

        expected = {"a": 1, "b": 2, "c": {"a": 1}}
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


def test_data_dict_not_save_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = {"a": 1, "b": 2}
        data = DataDict(provided, path=path)
        data.save()
        data.do_save = False
        data["c"] = {}
        data["c"]["a"] = 1

        expected = {"a": 1, "b": 2}
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


def test_data_dict_bulk_save_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = {"a": 1, "b": 2}
        data = DataDict(provided, path=path)
        data.save()
        data.do_save = False
        data["c"] = {}
        data["c"]["a"] = 1

        expected_before = {"a": 1, "b": 2}
        with open(path, "r") as file:
            assert json.load(file) == expected_before

        data.do_save = True

        expected_after = {"a": 1, "b": 2, "c": {"a": 1}}
        with open(path, "r") as file:
            assert json.load(file) == expected_after
    finally:
        path.unlink()


def test_data_dict_load_and_ignore_inital_value():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        pre_provided = {"a": 1, "b": 2}
        pre_data = DataDict(pre_provided, path=path)
        pre_data.save()

        provided = {"b": 3}
        data = DataDict(provided, path=path)
        with open(path, "r") as file:
            assert json.load(file) == data

    finally:
        path.unlink()


def test_data_list_save_right_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = [1, 2, 3, 4]
        data = DataList(provided, path=path)
        # noinspection PyArgumentList
        data.append(5)

        expected = [1, 2, 3, 4, 5]
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


def test_data_list_save_right_data_recursive():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = [1, 2, 3, 4]
        data = DataList(provided, path=path)
        # noinspection PyArgumentList
        data.append([])
        data[4].append("a")

        expected = [1, 2, 3, 4, ["a"]]
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


def test_data_list_not_save_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = [1, 2, 3, 4]
        data = DataList(provided, path=path)
        data.save()
        data.do_save = False
        # noinspection PyArgumentList
        data.append(5)

        expected = [1, 2, 3, 4]
        with open(path, "r") as file:
            assert json.load(file) == expected
    finally:
        path.unlink()


# noinspection PyArgumentList
def test_data_list_bulk_save_data():
    path = Path(f"{_TEST_FILES}/test.json")
    try:
        provided = [1, 2, 3, 4]
        data = DataList(provided, path=path)
        data.save()
        data.do_save = False
        data.append(5)
        data.append([])
        data[5].append("a")

        expected_before = [1, 2, 3, 4]
        with open(path, "r") as file:
            assert json.load(file) == expected_before

        data.do_save = True

        expected_after = [1, 2, 3, 4, 5, ["a"]]
        with open(path, "r") as file:
            assert json.load(file) == expected_after
    finally:
        path.unlink()
