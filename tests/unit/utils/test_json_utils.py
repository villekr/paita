import json
import pytest
from unittest.mock import patch, mock_open
from paita.utils.json_utils import JsonUtils

APP_NAME = "TestApp"
APP_AUTHOR = "TestAuthor"
FILE_NAME = "test_file.json"
MOCK_DATA = {"keyABC": ["aA", "bB", "cC"], "keyDEF": ["dD", "eE", "fF"]}


@pytest.mark.asyncio
async def test_save():
    try:
        instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
        await instance.save(MOCK_DATA)
    finally:
        await instance.delete()


@pytest.mark.asyncio
async def test_load():
    try:
        instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
        await instance.save(MOCK_DATA)
        data = await instance.load()
        assert data == MOCK_DATA
    finally:
        await instance.delete()
