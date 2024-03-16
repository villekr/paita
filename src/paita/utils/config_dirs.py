from pathlib import Path

from appdirs import user_config_dir


def compose_path(file_name: str, *, app_name: str, app_author: str) -> Path:
    config_dir = user_config_dir(appname=app_name, appauthor=app_author)
    return Path(config_dir) / file_name
