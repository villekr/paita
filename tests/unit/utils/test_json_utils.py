from enum import Enum
from typing import List, Optional

import pytest
from pydantic import BaseModel

from paita.utils.json_utils import JsonUtils

APP_NAME = "TestApp"
APP_AUTHOR = "TestAuthor"
FILE_NAME = "test_file.json"


class ItemType(Enum):
    simple = "simple"


class Item(BaseModel):
    item_type: ItemType = ItemType.simple
    item_source: Optional[str] = None

    class ConfigDict:
        use_enum_values = False


class Collection(BaseModel):
    items: List[Item] = []


COLLECTION = Collection(
    items=[
        Item(item_type=ItemType.simple),
        Item(item_type=ItemType.simple),
    ]
)


@pytest.mark.asyncio
async def test_read_not_found():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    with pytest.raises(FileNotFoundError):
        await instance.read(Collection)


@pytest.mark.asyncio
async def test_write_read():
    instance: JsonUtils = None
    try:
        instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
        await instance.write(COLLECTION)
        collection = await instance.read(Collection)
        assert collection == COLLECTION
    finally:
        await instance.delete()


@pytest.mark.asyncio
async def test_delete_not_found():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    with pytest.raises(FileNotFoundError):
        await instance.read(Collection)


@pytest.mark.asyncio
async def test_delete():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    await instance.write(COLLECTION)
    await instance.delete()
    with pytest.raises(FileNotFoundError):
        await instance.read(Collection)
