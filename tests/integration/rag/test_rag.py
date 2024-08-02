import pytest
from pydantic import ValidationError

from paita.llm.enums import AIService
from paita.llm.models import get_embeddings
from paita.settings.rag_settings import RAGSource, RAGSources, RAGSourceType
from paita.settings.rag_settings import RAG, RAGModel, RAGVectorStoreType


@pytest.fixture
def rag() -> RAG:
    return RAG(
        RAGModel(
            app_name="test_rag",
            app_author="unit_test_author",
            embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
            vector_store_type=RAGVectorStoreType.CHROMA,
        )
    )


@pytest.mark.integration
def test_rag(rag: RAG):
    assert rag is not None


@pytest.mark.integration
def test_rag_invalid():
    with pytest.raises(ValidationError):
        return RAG(
            RAGModel(
                app_name=None,
                app_author="unit_test_author",
                embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
                vector_store_type=RAGVectorStoreType.CHROMA,
            )
        )

    with pytest.raises(ValidationError):
        return RAG(
            RAGModel(
                app_name="test_rag",
                app_author="unit_test_author",
                embeddings=get_embeddings(ai_service=AIService.AWSBedRock.value),
                vector_store_type="something",
            )
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_url_impl(rag: RAG):
    url = "https://www.google.com"
    docs = await rag.load_url_impl(url=url, max_depth=2)
    assert docs is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create(rag: RAG):
    url = "https://www.google.com"
    await rag.create(url=url, max_depth=1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_na(rag: RAG):
    rag_sources = await rag.read()
    assert rag_sources is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read(rag: RAG):
    try:
        await rag.create(url="https://www.google.com", max_depth=1)
        rag_sources: RAGSources = await rag.read()
        assert rag_sources is not None
        assert len(rag_sources.rag_sources) > 0
        rag_source: RAGSource = rag_sources.rag_sources[0]
        assert type(rag_source.rag_source_type) is RAGSourceType
    finally:
        pass
        # await delete_folder(rag_settings.file_path, recursive=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete(rag: RAG):
    await rag.create(url="https://www.google.com", max_depth=1)
    await rag.delete("https://www.google.com")
