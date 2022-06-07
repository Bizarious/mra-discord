import json
from pathlib import Path

import pytest

from core.file_handling import config


_TEST_CONFIG = Path("test_config")
_TEST_FILE = "test.json"
_TEST_PATH = Path(f"{_TEST_CONFIG}/{_TEST_FILE}")
_TEST_NAME = "test"
_TEST_RESOURCES = Path(Path(__file__).parent / "resources")


@pytest.fixture(scope="session", autouse=True)
def init_data_path():
    config.set_config_path(_TEST_CONFIG)
    yield
    _TEST_CONFIG.rmdir()


@pytest.fixture(scope="function", autouse=True)
def remove_test_file():
    yield
    config.clear_config_categories()
    p = Path(f"{_TEST_CONFIG}/{_TEST_FILE}")
    if p.exists():
        p.unlink()


def test_config_category_get_right_data():
    expected = "test1"
    category = config.ConfigCategory(_TEST_NAME, {"a": expected})
    actual = category.get("a")
    assert actual == expected


def test_config_category_get_default_if_not_key():
    expected = "test1"
    category = config.ConfigCategory(_TEST_NAME)
    actual = category.get("not_exist", default="test1")
    assert actual == expected


def test_config_category_set_right_data():
    expected = "test1"
    category = config.ConfigCategory(_TEST_NAME)
    category.set("a", "test1")
    actual = category.get("a")
    assert actual == expected


def test_config_category_save_right_data():
    category = config.ConfigCategory(_TEST_NAME)
    category.set("a", "test1")
    expected = {"a": "test1"}
    with open(_TEST_PATH, "r") as file:
        assert json.load(file) == expected


def test_config_category_frozen():
    category = config.ConfigCategory.frozen(_TEST_NAME)
    with pytest.raises(config.ConfigCategoryError):
        category.set("a", "test1")


def test_get_existing_config_category():
    config_a = config.get_config_category(_TEST_NAME)
    config_b = config.get_config_category(_TEST_NAME)
    assert config_a == config_b


def test_create_right_external_category_env():
    importer = config.EnvConfigImporter(_TEST_RESOURCES / ".env_test")
    importer.import_from_file()
    config_category = config.get_config_category("external")
    expected = "TEST_VALUE"
    actual = config_category.get("TEST_KEY")
    assert actual == expected
