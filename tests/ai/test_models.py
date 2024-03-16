import pytest

from paita.ai.models import list_all_models


# @pytest.mark.skip("Needs mocking or only integration test.")
@pytest.mark.asyncio
async def test_list_all_models():
    _ = await list_all_models()
