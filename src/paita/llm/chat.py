from typing import TYPE_CHECKING

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from paita.llm.callbacks import AsyncHandler
from paita.llm.chat_history import ChatHistory
from paita.llm.models import AIService
from paita.llm.services import bedrock, ollama, openai
from paita.llm.services.service import LLMSettingsModel

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.runnables import Runnable


HISTORY_FILE_NAME = "chat_history"


class Chat:
    """
    Chat encapsulates chat history and can use different AI Models
    """

    def __init__(self):
        self._chat_model: BaseChatModel = None
        self._settings_model: LLMSettingsModel = None
        self._chat_history: ChatHistory = None
        self._chain: Runnable = None
        self._callback_handler: AsyncHandler = None
        self.parser: StrOutputParser = StrOutputParser()

    def init_model(
        self,
        *,
        settings_model: LLMSettingsModel,
        chat_history: ChatHistory,
        callback_handler: AsyncHandler,
    ):
        self._settings_model = settings_model
        self._chat_history = chat_history
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
        self._chat_model = service.chat_model()
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

        chain = prompt | self._chat_model | self.parser
        self._chain = RunnableWithMessageHistory(
            chain,
            lambda session_id: self._chat_history.history,  # noqa: ARG005
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    async def request(self, data: str):
        await self._trim_history(self._chat_history, max_length=self._settings_model.ai_history_depth)

        if self._settings_model.ai_streaming:
            async for _ in self._chain.astream(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            ):
                pass
        else:
            await self._chain.ainvoke(
                {"input": data},
                {"configurable": {"session_id": "unused"}},
            )

    @classmethod
    async def _trim_history(cls, chat_history: ChatHistory, *, max_length: int = 20):
        stored_messages = await chat_history.history.aget_messages()
        if len(stored_messages) <= max_length:
            return

        await chat_history.history.aclear()
        trim_history_messages = stored_messages[-max_length:]
        await chat_history.history.aadd_messages(trim_history_messages)

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
        summarization_chain = summarization_prompt | self._chat_model

        summary_message = summarization_chain.invoke({"chat_history": stored_messages})

        chat_history.history.clear()

        chat_history.history.add_message(summary_message)
