from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.language_models.chat_models import BaseChatModel

    from paita.llm.callbacks import AsyncHandler


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


class LLMSettingsModel(BaseModel):
    version: float = 0.1
    ai_service: Optional[str] = None
    ai_model: Optional[str] = None
    ai_persona: Optional[str] = "You are a helpful assistant. Answer all questions to the best of your ability."
    ai_streaming: Optional[bool] = True
    ai_model_kwargs: Optional[dict[str, Any]] = {}
    ai_n: Optional[int] = 1
    ai_max_tokens: Optional[int] = 2048
    ai_history_depth: Optional[int] = 20
