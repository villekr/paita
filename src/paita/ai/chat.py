from typing import TYPE_CHECKING

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from paita.ai.callbacks import AsyncHandler
from paita.ai.chat_history import ChatHistory
from paita.ai.models import AIService
from paita.ai.services import bedrock, ollama, openai
from paita.utils.settings_model import SettingsModel

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


HISTORY_FILE_NAME = "chat_history"


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
            service = bedrock.Bedrock(settings_model=settings_model, callback_handler=self._callback_handler)
        elif settings_model.ai_service == AIService.OpenAI.value:
            service = openai.OpenAI(settings_model=settings_model, callback_handler=self._callback_handler)
        elif settings_model.ai_service == AIService.Ollama.value:
            service = ollama.Ollama(settings_model=settings_model, callback_handler=self._callback_handler)
        else:
            msg = f"Invalid AI Service {settings_model.ai_service}"
            raise ValueError(msg)
        self._model = service.chat_model()

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

        await self._trim_history(chat_history, max_length=self._settings_model.ai_history_depth)

        if self._settings_model.ai_streaming and not bedrock.BEDROCK_DISABLE_STREAMING:
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
