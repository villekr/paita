import contextlib
from pathlib import Path
from typing import Type, TypeVar

import aiofiles
from aiofiles import os as aiofiles_os
from appdirs import user_config_dir
from pydantic import BaseModel

Model = TypeVar("Model", bound="BaseModel")


class JsonUtils:
    def __init__(self, *, app_name: str, app_author: str, file_name: str):
        self.app_name: str = app_name
        self.app_author: str = app_author
        self.config_dir: Path = Path(user_config_dir(appname=app_name, appauthor=app_author))
        self.file_name: Path = self.config_dir / file_name

    async def read(self, model: Type[Model]) -> Model:
        async with aiofiles.open(self.file_name, "r") as json_file:
            json_str = await json_file.read()
            return model.model_validate_json(json_str)
            # json_obj = json.loads(json_data)
            # log.debug(f"{json_obj=}")
            # model_instance = model.model_validate(json_obj)
            # log.debug(f"{model_instance=}")
            # return model_instance

    async def write(self, model: BaseModel):
        self.config_dir.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.file_name, "w") as json_file:
            json_str = model.model_dump_json()
            await json_file.write(json_str)

    async def delete(self):
        if self.file_name.exists():
            with contextlib.suppress(FileNotFoundError):
                self.file_name.unlink(missing_ok=True)
                await aiofiles_os.rmdir(self.config_dir)
