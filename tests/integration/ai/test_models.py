import pytest

from paita.ai.models import list_all_models


@pytest.mark.skip("Need to setup github action permissions")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_all_models():
    _ = await list_all_models()
