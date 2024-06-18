import pytest
from pydantic import ValidationError

from paita.llm.enums import AIService
from paita.llm.models import get_embeddings
from paita.rag.models import RAGSource, RAGSources, RAGSourceType
from paita.rag.rag_manager import RAGManager, RAGManagerModel, RAGVectorStoreType


@pytest.fixture
def rag_manager() -> RAGManager:
    return RAGManager(
        RAGManagerModel(
            app_name="test_rag_manager",
            app_author="unit_test_author",
            embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
            vector_store_type=RAGVectorStoreType.CHROMA,
        )
    )


@pytest.mark.integration
def test_rag_manager(rag_manager: RAGManager):
    assert rag_manager is not None


@pytest.mark.integration
def test_rag_manager_invalid():
    with pytest.raises(ValidationError):
        return RAGManager(
            RAGManagerModel(
                app_name=None,
                app_author="unit_test_author",
                embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
                vector_store_type=RAGVectorStoreType.CHROMA,
            )
        )

    with pytest.raises(ValidationError):
        return RAGManager(
            RAGManagerModel(
                app_name="test_rag_manager",
                app_author="unit_test_author",
                embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
                vector_store_type="something",
            )
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_url_impl(rag_manager: RAGManager):
    url = "https://www.google.com"
    docs = await rag_manager.load_url_impl(url=url, max_depth=1)
    assert docs is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create(rag_manager: RAGManager):
    url = "https://www.google.com"
    docs = await rag_manager.create(url=url, max_depth=1)
    assert docs is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_na(rag_manager: RAGManager):
    rag_sources = await rag_manager.read()
    assert rag_sources is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read(rag_manager: RAGManager):
    try:
        await rag_manager.create(url="https://www.google.com", max_depth=1)
        rag_sources: RAGSources = await rag_manager.read()
        assert rag_sources is not None
        assert len(rag_sources.rag_sources) > 0
        rag_source: RAGSource = rag_sources.rag_sources[0]
        assert type(rag_source.rag_source_type) is RAGSourceType
    finally:
        pass
        # await delete_folder(rag_manager.file_path, recursive=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete(rag_manager: RAGManager):
    await rag_manager.create(url="https://www.google.com", max_depth=1)
    await rag_manager.delete("https://www.google.com")
