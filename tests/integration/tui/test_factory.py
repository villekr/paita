from pathlib import Path
from shutil import rmtree

import pytest
from cache3 import DiskCache

from paita.llm.enums import AIService, Tag

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
