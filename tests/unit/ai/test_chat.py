import pytest

from paita.ai.chat import AsyncHandler, Chat
from paita.ai.chat_history import ChatHistory
from paita.ai.enums import AIService
from paita.utils.settings_model import SettingsModel

ai_service_models = {
    AIService.AWSBedRock.value: "anthropic.claude-v2",
    # AIService.OpenAIChatGPT.value: "gpt-3.5-turbo",
}


@pytest.fixture(params=list(ai_service_models.items()))
def settings_model(request):
    key, value = request.param
    return SettingsModel(ai_service=key, ai_model=value)


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
