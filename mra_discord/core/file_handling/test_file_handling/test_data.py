import json
import shutil
from pathlib import Path

import pytest

from core.file_handling import data

_DATA_PATH = Path("test_data")


@pytest.fixture(scope="session", autouse=True)
def prepare_test_data_path():
    data.set_data_path(_DATA_PATH)
    yield


@pytest.fixture(scope="function", autouse=True)
def handle_test_dir():
    yield
    data.reset_data()
    if _DATA_PATH.exists():
        shutil.rmtree(_DATA_PATH)


def test_data_set_path_twice():
    with pytest.raises(AssertionError):
        data.set_data_path(_DATA_PATH)


def test_data_empy_path():
    with pytest.raises(FileNotFoundError):
        data.get_json_data(Path(""))


def test_data_create_right_file():
    test_file = Path("test.json")
    data.get_json_data(test_file)
    assert Path(f"{_DATA_PATH}/{test_file}").exists()


def test_data_create_right_content():
    test_file = Path("test.json")
    test_data = {"a": 1}
    data.get_json_data(test_file, default_value=test_data)
    with open(f"{_DATA_PATH}/{test_file}") as file:
        assert json.load(file) == test_data
