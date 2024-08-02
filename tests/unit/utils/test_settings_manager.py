import pytest

from paita.llm.enums import AIService
from paita.settings.llm_settings.llm_settings import LLMSettings, LLMSettingsModel


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
        settings_model=model,
        app_name="paita_unit_tests",
        app_author="unit_test",
    )
    try:
        await manager.save()
        loaded_manager: LLMSettings = await LLMSettings.load(app_name="paita_unit_tests", app_author="unit_test")
        assert loaded_manager.model == model
    finally:
        await LLMSettings.delete(app_name="paita_unit_tests", app_author="unit_test")
