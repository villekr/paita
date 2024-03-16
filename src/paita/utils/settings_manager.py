import json
import os.path
from enum import Enum
from pathlib import Path

import aiofiles
from aiofiles import os as aiofiles_os
from appdirs import user_config_dir

from paita.utils.settings_model import SettingsModel


class SettingsBackendType(Enum):
    LOCAL = "local"
    AWS_APPCONFIG = "aws_appconfig"
    NONE = "none"


SETTINGS_FILE_NAME = "settings.json"


class SettingsManager:
    model: SettingsModel = None

    _backend_type: SettingsBackendType = None

    def __init__(
        self,
        *,
        model: SettingsModel,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ):
        self.model: SettingsModel = model
        self._app_name: str = app_name
        self._app_author: str = app_author
        self._backend_type: SettingsBackendType = backend_type

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> "SettingsManager":
        if backend_type == SettingsBackendType.LOCAL:
            model: SettingsModel = await cls._load_and_parse(app_name=app_name, app_author=app_author)
            return SettingsManager(
                model=model,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )
        raise NotImplementedError

    async def save(self):
        await self._dump_and_save(self.model, app_name=self._app_name, app_author=self._app_author)

    @classmethod
    async def delete(cls, *, app_name: str, app_author: str):
        config_dir = user_config_dir(appname=app_name, appauthor=app_author)
        file_path = Path(config_dir) / SETTINGS_FILE_NAME

        if file_path.exists():
            file_path.unlink(missing_ok=True)
            await aiofiles_os.rmdir(config_dir)

    @classmethod
    async def _load_and_parse(cls, *, app_name: str, app_author: str) -> SettingsModel:
        config_dir = user_config_dir(appname=app_name, appauthor=app_author)
        file_path = Path(config_dir) / SETTINGS_FILE_NAME
        async with aiofiles.open(file_path, "r") as json_file:
            json_data = await json_file.read()
            json_obj = json.loads(json_data)
            model: SettingsModel = SettingsModel.model_validate(json_obj)
            return model

    @classmethod
    async def _dump_and_save(cls, model: SettingsModel, *, app_name: str, app_author: str):
        config_dir = user_config_dir(appname=app_name, appauthor=app_author)
        file_path = Path(config_dir) / SETTINGS_FILE_NAME

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        async with aiofiles.open(file_path, "w") as json_file:
            json_data = model.model_dump()
            json_str = json.dumps(json_data)
            await json_file.write(json_str)
