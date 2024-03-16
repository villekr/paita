import pytest

from paita.ai.enums import AIService
from paita.utils.settings_manager import SettingsManager, SettingsModel


@pytest.mark.asyncio
async def test_load_unsupported_backend():
    with pytest.raises(NotImplementedError):
        await SettingsManager.load(
            app_name="paita_unit_tests",
            app_author="unit_test",
            backend_type="some_unsupported",
        )


@pytest.mark.asyncio
async def test_save_load_local():
    model: SettingsModel = SettingsModel(
        version=1.0,
        ai_service=AIService.AWSBedRock.value,
        ai_model="SomeModel",
        ai_persona="Custom Persona",
    )
    manager: SettingsManager = SettingsManager(
        model=model,
        app_name="paita_unit_tests",
        app_author="unit_test",
    )
    try:
        await manager.save()
        loaded_manager: SettingsManager = await SettingsManager.load(
            app_name="paita_unit_tests", app_author="unit_test"
        )
        assert loaded_manager.model == model
    finally:
        await SettingsManager.delete(app_name="paita_unit_tests", app_author="unit_test")
