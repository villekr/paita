import json
from pathlib import Path
from typing import Dict, List
import os

import aiofiles
from aiofiles import os as aiofiles_os
from appdirs import user_config_dir


class JsonUtils:
    def __init__(self, *, app_name: str, app_author: str, file_name: str):
        self.app_name = app_name
        self.app_author = app_author
        self.config_dir = user_config_dir(appname=app_name, appauthor=app_author)
        self.file_name = Path(self.config_dir) / file_name

    async def load(self) -> Dict[str, List[str]]:
        async with aiofiles.open(self.file_name, "r") as json_file:
            json_data = await json_file.read()
            return json.loads(json_data)

    async def save(self, data: Dict[str, List[str]]):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        async with aiofiles.open(self.file_name, "w") as json_file:
            json_str = json.dumps(data)
            await json_file.write(json_str)

    async def delete(self):
        if self.file_name.exists():
            self.file_name.unlink(missing_ok=True)
            await aiofiles_os.rmdir(self.config_dir)
