from __future__ import annotations

import asyncio
import os.path
from enum import Enum
from pathlib import Path
from typing import TypeVar, Generic, Type

import aiofiles
from aiofiles import os as aiofiles_os
from appdirs import user_config_dir
from pydantic import BaseModel


class SettingsBackendType(Enum):
    LOCAL = "local"
    AWS_APPCONFIG = "aws_appconfig"
    NONE = "none"


Model = TypeVar("Model", bound=BaseModel)


async def load_and_parse(file_name: str, app_name: str, app_author: str, model_type: Type[Model]) -> Model:
    config_dir = user_config_dir(appname=app_name, appauthor=app_author)
    file_path = Path(config_dir) / file_name
    async with aiofiles.open(file_path, "r") as json_file:
        json_data = await json_file.read()
        model: Model = model_type.model_validate_json(json_data)
        return model


async def dump_and_save(model: Model, file_name: str, app_name: str, app_author: str):
    config_dir = user_config_dir(appname=app_name, appauthor=app_author)
    file_path = Path(config_dir) / file_name

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    async with aiofiles.open(file_path, "w") as json_file:
        json_data = model.model_dump_json()
        await json_file.write(json_data)


async def delete(file_name: str, app_name: str, app_author: str):
    config_dir = user_config_dir(appname=app_name, appauthor=app_author)
    file_path = Path(config_dir) / file_name

    if file_path.exists():
        file_path.unlink(missing_ok=True)
        await aiofiles_os.rmdir(config_dir)


class BaseSettings(Generic[Model]):
    def __init__(
        self,
        *,
        model: Model = None,
        file_name: str,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ):
        self._model: Model = model
        self._file_name: str = file_name
        self._app_name: str = app_name
        self._app_author: str = app_author
        self._backend_type: SettingsBackendType = backend_type

    def __str__(self):
        return self._model.model_dump_json()

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> Model:
        raise NotImplementedError

    async def save(self):
        await dump_and_save(self._model, app_name=self._app_name, app_author=self._app_author)


class ChildModelA(BaseModel):
    name: str
    role: str


class ChildModelB(BaseModel):
    name: str
    age: int


class SettingsA(BaseSettings):
    FILE_NAME: str = "settings_a.json"

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> BaseSettings:
        if backend_type == SettingsBackendType.LOCAL:
            try:
                model: ChildModelA = await load_and_parse(file_name=cls.FILE_NAME, app_name=app_name, app_author=app_author, model_type=ChildModelA)
            except FileNotFoundError:
                model: ChildModelA = ChildModelA(name="name", role="role")
            return SettingsA(
                model=model,
                file_name=cls.FILE_NAME,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )


class SettingsB(BaseSettings):
    FILE_NAME: str = "settings_b.json"

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> BaseSettings:
        if backend_type == SettingsBackendType.LOCAL:
            try:
                model: ChildModelB = await load_and_parse(file_name=cls.FILE_NAME, app_name=app_name, app_author=app_author, model_type=ChildModelB)
            except FileNotFoundError:
                model: ChildModelB = ChildModelB(name="name", age=18)
            return SettingsB(
                model=model,
                file_name=cls.FILE_NAME,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )


async def load():
    settings_a = await SettingsA.load(app_name="app", app_author="author")
    settings_b = await SettingsB.load(app_name="app", app_author="author")

    print(settings_a)
    print(settings_b)


if __name__ == '__main__':
    asyncio.run(load())
