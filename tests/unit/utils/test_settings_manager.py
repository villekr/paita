import pytest

from paita.llm.enums import AIService
from paita.llm.services.service import LLMSettingsModel
from paita.settings.base_settings import delete
from paita.settings.llm_settings import LLMSettings


@pytest.mark.asyncio
async def test_load_unsupported_backend():
    with pytest.raises(NotImplementedError):
        await LLMSettings.load(
            app_name="paita_unit_tests",
            app_author="unit_test",
            backend_type="some_unsupported",
        )


@pytest.mark.asyncio
async def test_save_load_local():
    model: LLMSettingsModel = LLMSettingsModel(
        version=1.0,
        ai_service=AIService.AWSBedRock.value,
        ai_model="SomeModel",
        ai_persona="Custom Persona",
    )
    manager: LLMSettings = LLMSettings(
        model=model,
        file_name=LLMSettings.FILE_NAME,
        app_name="paita_unit_tests",
        app_author="unit_test",
    )
    try:
        await manager.save()
        loaded_manager: LLMSettings = await LLMSettings.load(app_name="paita_unit_tests", app_author="unit_test")
        assert loaded_manager.model == model
    finally:
        await delete(file_name=manager.FILE_NAME, app_name="paita_unit_tests", app_author="unit_test")
