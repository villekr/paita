from __future__ import annotations

from typing import Any, List, Tuple

from appdirs import user_config_dir
from cache3 import DiskCache

from paita.llm.enums import Tag
from paita.llm.models import list_all_models
from paita.llm.services.service import LLMSettingsModel
from paita.localization import labels
from paita.settings.base_settings import BaseSettings, SettingsBackendType, load_and_parse


class LLMSettings(BaseSettings):
    FILE_NAME: str = "llm_settings.json"
    CACHE_DIR = user_config_dir(appname=labels.APP_TITLE, appauthor=labels.APP_AUTHOR)
    CACHE_NAME = "cache"
    CACHE_TTL = 24 * 60 * 60

    def __init__(
        self,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.cache: DiskCache = DiskCache(self.CACHE_DIR, self.CACHE_NAME)

    @classmethod
    async def load(
        cls,
        *,
        app_name: str,
        app_author: str,
        backend_type: SettingsBackendType = SettingsBackendType.LOCAL,
    ) -> LLMSettings:
        if backend_type == SettingsBackendType.LOCAL:
            try:
                model: LLMSettingsModel = await load_and_parse(
                    file_name=cls.FILE_NAME, app_name=app_name, app_author=app_author, model_type=LLMSettingsModel
                )
            except FileNotFoundError:
                model: LLMSettingsModel = LLMSettingsModel()
            return LLMSettings(
                model=model,
                file_name=cls.FILE_NAME,
                app_name=app_name,
                app_author=app_author,
                backend_type=backend_type,
            )
        msg = f"Backend type not supported {backend_type}"
        raise NotImplementedError(msg)

    async def refresh_llms(self):
        all_models = await list_all_models()
        not_none_ai_models = any(len(models) for models in all_models.values())
        if not not_none_ai_models:
            msg = "No models found"
            raise ValueError(msg)
        for key in all_models:
            if all_models[key]:
                self.cache.set(key, all_models[key], self.CACHE_TTL, tag=Tag.AI_MODELS.value)

        available_ai_services: List[Tuple[str, str]] = list(self.cache.keys(tag=Tag.AI_MODELS.value))

        if self.model.ai_service not in available_ai_services:
            self.model.ai_service = available_ai_services[0]

            available_ai_models: List[Tuple[str, str]] = self.cache.get(
                self.model.ai_service, [], tag=Tag.AI_MODELS.value
            )

            if self.model.ai_model not in available_ai_models:
                self.model.ai_model = available_ai_models[0]

    def available_ai_services(self) -> list[tuple[Any, str]]:
        return list(self.cache.keys(tag=Tag.AI_MODELS.value))

    def available_ai_models(self, ai_service: str, default: Any) -> List[str]:
        return self.cache.get(ai_service, default, tag=Tag.AI_MODELS.value)
