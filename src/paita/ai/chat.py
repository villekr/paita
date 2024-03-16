import os
from typing import TYPE_CHECKING

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain_community.chat_models import bedrock as br
from langchain_core.runnables.history import RunnableWithMessageHistory

from paita.ai.callbacks import AsyncHandler
from paita.ai.chat_history import ChatHistory
from paita.ai.mock_model import MockModel
from paita.ai.models import AIService
from paita.utils.logger import log
from paita.utils.settings_model import SettingsModel

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


HISTORY_FILE_NAME = "chat_history"

# https://github.com/langchain-ai/langchain/issues/11668
BEDROCK_DISABLE_STREAMING = bool(os.getenv("BEDROCK_DISABLE_STREAMING", "True"))


class Chat:
    """
    Chat capsulates chat history and can use different AI Models
    """

    def __init__(self):
        self._model: BaseChatModel = None
        self._settings_model: SettingsModel = None
        self._callback_handler: AsyncHandler = None
        self.parser: StrOutputParser = StrOutputParser()

    def init_model(
        self,
        *,
        settings_model: SettingsModel,
        callback_handler: AsyncHandler,
    ):
        self._settings_model = settings_model
        self._callback_handler = callback_handler

        if settings_model.ai_service == AIService.AWSBedRock.value:
            model_kwargs = {
                # "max_tokens_to_sample": self._settings_model.ai_max_tokens,
                "temperature": 1,
                "top_k": 250,
                "top_p": 0.8,
                # "stop_sequences": ["\n\nHuman"],
            }
            if self._settings_model.ai_model_kwargs:
                model_kwargs.update(self._settings_model.ai_model_kwargs)
            log.debug(f"{model_kwargs=}")
            self._model = br.BedrockChat(
                model_id=settings_model.ai_model,
                streaming=(False if BEDROCK_DISABLE_STREAMING else self._settings_model.ai_streaming),
                model_kwargs=model_kwargs,
                # max_tokens=settings_model.ai_max_tokens,
                # n=settings_model.ai_n,
                callbacks=[callback_handler],
                # callback_manager=callback_handler,
            )
        elif settings_model.ai_service == AIService.OpenAIChatGPT.value:
            from langchain_openai import ChatOpenAI

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
            self._model = ChatOpenAI(
                model_name=settings_model.ai_model,
                streaming=settings_model.ai_streaming,
                model_kwargs=model_kwargs,
                max_tokens=settings_model.ai_max_tokens,
                temperature=temperature,
                # n=settings_model.ai_n,
                callbacks=[callback_handler],
                # callback_manager=callback_handler,
            )
        else:
            self._model = MockModel()

    async def request(self, data: str, *, chat_history: ChatHistory) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self._settings_model.ai_persona,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        if self._settings_model.ai_streaming and not BEDROCK_DISABLE_STREAMING:
            chain = prompt | self._model | self.parser
            chain_with_message_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: chat_history.history,  # noqa: ARG005
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            async for _ in chain_with_message_history.astream(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            ):
                pass
        else:
            chain = prompt | self._model | self.parser
            chain_with_message_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: chat_history.history,  # noqa: ARG005
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            await chain_with_message_history.ainvoke(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            )
        await self._trim_history(chat_history, max_length=self._settings_model.ai_history_depth)

    @classmethod
    async def _trim_history(cls, chat_history: ChatHistory, *, max_length: int = 20):
        stored_messages = await chat_history.history.aget_messages()
        if len(stored_messages) <= max_length:
            return

        await chat_history.history.aclear()
        await chat_history.history.aadd_messages(stored_messages[-max_length:])

    async def _summarize_messages(self, chat_history: ChatHistory, *, max_length: int = 20):
        stored_messages = chat_history.history.messages
        if len(stored_messages) <= max_length:
            return
        summarization_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "user",
                    "Distill the above chat messages into a single summary message."
                    "Include as many specific details as you can.",
                ),
            ]
        )
        summarization_chain = summarization_prompt | self._model

        summary_message = summarization_chain.invoke({"chat_history": stored_messages})

        chat_history.history.clear()

        chat_history.history.add_message(summary_message)
