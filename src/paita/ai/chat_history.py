from typing import TYPE_CHECKING

from langchain.memory import ChatMessageHistory, FileChatMessageHistory
from langchain_core.chat_history import AIMessage, BaseChatMessageHistory

from paita.ai.enums import Role
from paita.ai.message import Message
from paita.utils.config_dirs import compose_path

if TYPE_CHECKING:
    from pathlib import Path


HISTORY_FILE_NAME = "chat_history"


class ChatHistory:
    """
    ChatHistory is a factory for creating specific langchain ChatHistory instance
    """

    def __init__(self, *, app_name: str, app_author: str, file_history: bool = True):
        file_path: Path = compose_path(HISTORY_FILE_NAME, app_name=app_name, app_author=app_author)
        self.history: BaseChatMessageHistory = None
        if file_history:
            self.history = FileChatMessageHistory(str(file_path))
        else:
            self.history = ChatMessageHistory()

    async def messages(self) -> [Message]:
        # TODO: This conversion is quite unnecessary. Use Langchain classes directly.
        lc_messages = await self.history.aget_messages()
        messages: [Message] = []
        for lc_message in lc_messages:
            role = Role.question
            if type(lc_message) is AIMessage:
                role = Role.answer
            messages.append(Message(content=lc_message.content, role=role))
        return messages
