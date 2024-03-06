# from paita.ai.mock_model import MockModel
from pathlib import Path

from appdirs import user_config_dir
from langchain.memory import FileChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import bedrock as br
from langchain_community.chat_models import openai
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.history import RunnableWithMessageHistory

from paita.ai.callbacks import AsyncHandler
from paita.ai.models import AIService
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsModel

HISTORY_FILE_NAME = "chat_history"


class Chat:
    """
    Chat capsulates chat history and can use different AI Models
    """

    def __init__(self, *, app_name: str, app_author: str):
        config_dir = user_config_dir(appname=app_name, appauthor=app_author)
        file_path = Path(config_dir) / HISTORY_FILE_NAME
        # self._chat_history = ChatMessageHistory()
        self._chat_history = FileChatMessageHistory(str(file_path))
        self._model: BaseChatModel = None
        self._settings_model: SettingsModel = None
        self._callback_handler: AsyncHandler = None

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
                "max_tokens_to_sample": self._settings_model.ai_max_tokens,
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
                streaming=self._settings_model.ai_streaming,
                model_kwargs=model_kwargs,
                # max_tokens=settings_model.ai_max_tokens,
                # n=settings_model.ai_n,
                callbacks=[callback_handler],
            )
        elif settings_model.ai_service == AIService.OpenAIChatGPT.value:
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
                if "temperature" in model_kwargs.keys():
                    temperature = int(model_kwargs["temperature"])
                    del model_kwargs["temperature"]
            log.debug(f"{model_kwargs=}")
            self._model = openai.ChatOpenAI(
                model_name=settings_model.ai_model,
                streaming=settings_model.ai_streaming,
                model_kwargs=model_kwargs,
                max_tokens=settings_model.ai_max_tokens,
                temperature=temperature,
                # n=settings_model.ai_n,
                callbacks=[callback_handler],
            )
        # elif ai_service == AIService.Mock:
        #     self._model = MockModel(
        #         model_id=ai_model,
        #         streaming=streaming,
        #         callback_on_token=callback_on_token,
        #         callback_on_end=callback_on_end,
        #     )
        else:
            raise ValueError("engine_type not defined")

    async def request(self, data: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self._settings_model.ai_persona,
                    # TODO: the following prompt makes LLM aware that will
                    #  receive a condensed summary instead of a chat history
                    # "You are a helpful assistant. Answer all questions to the best of
                    # your ability. The provided chat history includes facts about the
                    # user you are speaking with.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        if self._settings_model.ai_streaming:
            chain = prompt | self._model
            chain_with_message_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: self._chat_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            async for _ in chain_with_message_history.astream(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            ):
                pass
        else:
            chain = prompt | self._model
            chain_with_message_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: self._chat_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            await chain_with_message_history.ainvoke(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            )
        await self._trim_history(self._settings_model.ai_history_depth)

    async def _trim_history(self, max_length: int = 20):
        stored_messages = await self._chat_history.aget_messages()
        if len(stored_messages) <= max_length:
            return

        await self._chat_history.aclear()
        await self._chat_history.aadd_messages(stored_messages[-max_length:])
        stored_messages = await self._chat_history.aget_messages()

    async def _summarize_messages(self, max_length: int = 20):
        raise NotImplementedError  # TODO: finalize and make async
        stored_messages = self._chat_history.messages
        if len(stored_messages) <= 20:
            return
        summarization_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "user",
                    "Distill the above chat messages into a single summary message. Include as many specific details as you can.",  # noqa: B950
                ),
            ]
        )
        summarization_chain = summarization_prompt | self._model

        summary_message = summarization_chain.invoke({"chat_history": stored_messages})

        self._chat_history.clear()

        self._chat_history.add_message(summary_message)
