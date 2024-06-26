import pytest

from paita.llm.models import list_all_models


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_all_models():
    _ = await list_all_models()
