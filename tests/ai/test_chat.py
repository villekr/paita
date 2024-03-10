import pytest

from paita.ai.chat import AsyncHandler, Chat
from paita.ai.enums import AIService
from paita.utils.settings_model import SettingsModel

ai_service_models = {
    AIService.AWSBedRock.value: "anthropic.claude-v2",
    AIService.OpenAIChatGPT.value: "gpt-3.5-turbo",
}


@pytest.fixture(params=[(key, value) for key, value in ai_service_models.items()])
def settings_model(request):
    key, value = request.param
    model = SettingsModel(ai_service=key, ai_model=value)
    return model


def mock_callback(*args, **kwargs):
    pass


@pytest.fixture()
def chat() -> Chat:
    return Chat(app_name="paita_unit_test", app_author="test", file_history=False)


@pytest.fixture()
def callback_handler() -> AsyncHandler:
    callback_handler = AsyncHandler()
    callback_handler.register_callbacks(mock_callback, mock_callback, mock_callback)
    return callback_handler


@pytest.fixture()
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SOMETHING")
    pass


def test_init_models(chat, settings_model, callback_handler, mock_env):
    chat.init_model(
        settings_model=settings_model,
        callback_handler=callback_handler,
    )


@pytest.mark.skip("Needs mocking")
@pytest.mark.asyncio
async def test_request_empty_history(chat, settings_model, callback_handler, mock_env):
    chat.init_model(
        settings_model=settings_model,
        callback_handler=callback_handler,
    )

    await chat.request("First")


@pytest.mark.skip("Needs mocking")
@pytest.mark.asyncio
async def test_request_some_history(chat, settings_model, callback_handler, mock_env):
    chat.init_model(
        settings_model=settings_model,
        callback_handler=callback_handler,
    )
    await chat.request("First")
    await chat.request("Second")
