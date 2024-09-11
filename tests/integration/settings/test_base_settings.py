import pytest

from paita.settings.base_settings import BaseModel, BaseSettings, SettingsBackendType, load_and_parse


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
    ) -> "SettingsA":
        if backend_type == SettingsBackendType.LOCAL:
            try:
                model: ChildModelA = await load_and_parse(
                    file_name=cls.FILE_NAME, app_name=app_name, app_author=app_author, model_type=ChildModelA
                )
            except FileNotFoundError:
                model: ChildModelA = ChildModelA(name="name", role="role")
            return SettingsA(
                model=model,
                file_name=cls.FILE_NAME,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )
        msg = f"Backend type not supported {backend_type}"
        raise ValueError(msg)


class SettingsB(BaseSettings):
    FILE_NAME: str = "settings_b.json"

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> "SettingsB":
        if backend_type == SettingsBackendType.LOCAL:
            try:
                model: ChildModelB = await load_and_parse(
                    file_name=cls.FILE_NAME, app_name=app_name, app_author=app_author, model_type=ChildModelB
                )
            except FileNotFoundError:
                model: ChildModelB = ChildModelB(name="name", age=18)
            return SettingsB(
                model=model,
                file_name=cls.FILE_NAME,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )
        msg = f"Backend type not supported {backend_type}"
        raise ValueError(msg)


@pytest.mark.asyncio
async def test_settings_load():
    settings_a = await SettingsA.load(app_name="app", app_author="author")
    settings_b = await SettingsB.load(app_name="app", app_author="author")

    assert type(settings_a) == SettingsA
    assert type(settings_b) == SettingsB
