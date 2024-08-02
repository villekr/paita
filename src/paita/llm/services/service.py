from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from paita.llm.callbacks import AsyncHandler
from paita.settings.llm_settings.llm_settings import LLMSettingsModel


class Service:
    def __init__(self, *, settings_model: LLMSettingsModel, callback_handler: AsyncHandler):
        self._settings_model = settings_model
        self._callback_handler = callback_handler

    @classmethod
    async def models(cls) -> [str]:
        raise NotImplementedError

    @classmethod
    def embeddings(cls, model_id: Optional[str] = None) -> Embeddings:
        raise NotImplementedError

    def chat_model(self) -> BaseChatModel:
        raise NotImplementedError
