import pytest

from paita.llm.chat import AsyncHandler, Chat
from paita.llm.chat_history import ChatHistory
from paita.llm.enums import AIService
from paita.llm.services.service import LLMSettingsModel

ai_service_models = {
    # AIService.AWSBedRock.value: "anthropic.claude-v2",
    # AIService.OpenAI.value: "gpt-3.5-turbo",
    AIService.Ollama.value: "llama3.1:latest",
}


@pytest.fixture(params=list(ai_service_models.items()))
def settings_model(request):
    key, value = request.param
    return LLMSettingsModel(ai_service=key, ai_model=value)


def mock_callback():
    pass


@pytest.fixture
def chat() -> Chat:
    return Chat()


@pytest.fixture
def callback_handler() -> AsyncHandler:
    callback_handler = AsyncHandler()
    callback_handler.register_callbacks(mock_callback, mock_callback, mock_callback)
    return callback_handler


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SOMETHING")


@pytest.fixture
def chat_history():
    return ChatHistory(app_name="test", app_author="test", file_history=False)


@pytest.mark.integration
@pytest.mark.usefixtures("mock_env")
def test_init_models(chat, settings_model, chat_history, callback_handler):
    chat.init_model(
        settings_model=settings_model,
        chat_history=chat_history,
        callback_handler=callback_handler,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_empty_history(chat, settings_model, chat_history, callback_handler):
    chat.init_model(
        settings_model=settings_model,
        chat_history=chat_history,
        callback_handler=callback_handler,
    )

    await chat.request("First")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_some_history(chat, settings_model, chat_history, callback_handler):
    chat.init_model(
        settings_model=settings_model,
        chat_history=chat_history,
        callback_handler=callback_handler,
    )
    await chat.request("First")
    await chat.request("Second")
