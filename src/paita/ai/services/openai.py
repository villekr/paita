import asyncio
from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI
from openai import OpenAI as OpenAIModule

from paita.ai.services.service import Service
from paita.utils.logger import log

if TYPE_CHECKING:
    from openai.types import Model


class OpenAI(Service):
    @classmethod
    async def models(cls):
        loop = asyncio.get_event_loop()
        try:
            client = OpenAIModule()
            pf = client.models.list
            response: [Model] = await loop.run_in_executor(None, pf)
            models = [model.id for model in response.data]
            return sorted(models)
        except Exception as e:  # noqa: BLE001 TODO
            log.info(e)
            return []

    def chat_model(self) -> ChatOpenAI:
        model_kwargs = {
            # "top_k": 250,
            "top_p": 0.8,
            "frequency_penalty": 0.8,
            "presence_penalty": 0.8,
            # "stop_sequences": ["\n\nHuman"],
        }
        temperature = 1
        if self._settings_model.ai_model_kwargs is not None:
            model_kwargs.update(self._settings_model.ai_model_kwargs)
            if "temperature" in model_kwargs:
                temperature = int(model_kwargs["temperature"])
                del model_kwargs["temperature"]
        log.debug(f"{model_kwargs=}")
        return ChatOpenAI(
            model_name=self._settings_model.ai_model,
            streaming=self._settings_model.ai_streaming,
            model_kwargs=model_kwargs,
            max_tokens=self._settings_model.ai_max_tokens,
            temperature=temperature,
            # n=settings_model.ai_n,
            callbacks=[self._callback_handler],
            # callback_manager=callback_handler,
        )
