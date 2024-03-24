from pathlib import Path
from shutil import rmtree

import pytest
from cache3 import DiskCache

from paita.ai.enums import AIService, Tag

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
    _cache.set(AIService.OpenAI.value, MODELS_B, tag=Tag.AI_MODELS.value)
    yield _cache

    if path.exists():
        rmtree(path.as_posix())


def test_get(cache):
    models_from_cache = cache.get(AIService.AWSBedRock.value, tag=Tag.AI_MODELS.value)
    assert models_from_cache == MODELS_A


def test_get_overwrite_existing(cache):
    cache.set(AIService.AWSBedRock.value, MODELS_B, tag=Tag.AI_MODELS.value)
    models_from_cache = cache.get(AIService.AWSBedRock.value, tag=Tag.AI_MODELS.value)
    assert models_from_cache == MODELS_B


def test_get_empty(cache):
    cache.clear()
    value = cache.get(AIService.AWSBedRock.value, tag=Tag.AI_MODELS.value)
    assert value is None


def test_keys(cache):
    ai_services = list(cache.keys(tag=Tag.AI_MODELS.value))
    assert sorted(ai_services) == sorted([AIService.AWSBedRock.value, AIService.OpenAI.value])
