from langchain_community.chat_models.ollama import ChatOllama
from ollama import AsyncClient

from paita.ai.services.service import Service
from paita.utils.logger import log


class Ollama(Service):
    @classmethod
    async def models(cls) -> [str]:
        try:
            client = AsyncClient()
            response = await client.list()
            models = [model["name"] for model in response["models"]]
            return sorted(models)
        except Exception as e:  # noqa: BLE001 TODO
            log.info(e)
            return []

    def chat_model(self) -> ChatOllama:
        model_kwargs = {
            "max_tokens_to_sample": self._settings_model.ai_max_tokens,
            "temperature": 1,
            "top_k": 250,
            "top_p": 0.8,
            # "stop_sequences": ["\n\nHuman"],
        }
        if self._settings_model.ai_model_kwargs:
            model_kwargs.update(self._settings_model.ai_model_kwargs)
        log.debug(f"{model_kwargs=}")
        return ChatOllama(
            model_id=self._settings_model.ai_model,
            streaming=self._settings_model.ai_streaming,
            model_kwargs=model_kwargs,
            # max_tokens=settings_model.ai_max_tokens,
            # n=settings_model.ai_n,
            callbacks=[self._callback_handler],
            # callback_manager=callback_handler,
        )
