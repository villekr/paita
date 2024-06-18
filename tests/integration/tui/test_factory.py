from pathlib import Path
from shutil import rmtree

import pytest
from cache3 import DiskCache

from paita.llm.enums import AIService, Tag
from paita.tui.factory import create_rag_manager
from paita.utils.settings_model import SettingsModel

MODELS_A = ["modelA1", "modelA2", "modelA3"]
MODELS_B = ["modelB1", "modelB2", "modelB3"]


@pytest.fixture
def cache() -> DiskCache:
    directory = "paita unit-tests"
    path = Path(directory)
    if path.exists():
        rmtree(path.as_posix())

    _cache: DiskCache = DiskCache(directory)
    _cache.set(AIService.AWSBedRock.value, MODELS_A, tag=Tag.AI_MODELS.value)
    yield _cache

    if path.exists():
        rmtree(path.as_posix())


@pytest.mark.integration
def test_create_rag_manager():
    settings_model = SettingsModel(ai_service=AIService.AWSBedRock)
    rag_manager = create_rag_manager(
        app_name="test_rag_manager",
        app_author="unit_test_author",
        settings_model=settings_model,
    )
    assert rag_manager is not None
