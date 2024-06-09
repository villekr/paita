import pytest
from pydantic import ValidationError

from paita.ai.enums import AIService
from paita.ai.models import get_embeddings
from paita.rag.rag_manager import RAGManager, RAGManagerModel, RAGVectorStoreType


@pytest.fixture
def rag_manager() -> RAGManager:
    return RAGManager(
        RAGManagerModel(
            app_name="test_rag_manager",
            app_author="unit_test_author",
            embeddings=get_embeddings(AIService.AWSBedRock.value),
            vector_store_type=RAGVectorStoreType.CHROMA,
        )
    )


def test_create(rag_manager: RAGManager):
    assert rag_manager is not None


def test_create_invalid():
    with pytest.raises(ValidationError):
        return RAGManager(
            RAGManagerModel(
                app_name=None,
                app_author="unit_test_author",
                embeddings=get_embeddings(AIService.AWSBedRock.value),
                vector_store_type=RAGVectorStoreType.CHROMA,
            )
        )

    with pytest.raises(ValidationError):
        return RAGManager(
            RAGManagerModel(
                app_name="test_rag_manager",
                app_author="unit_test_author",
                embeddings=get_embeddings(AIService.AWSBedRock.value),
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
async def test_load(rag_manager: RAGManager):
    url = "https://www.google.com"
    docs = await rag_manager.load(url=url, max_depth=1)
    assert docs is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete(rag_manager: RAGManager):
    await rag_manager.load(url="https://www.google.com", max_depth=1)
    await rag_manager.delete("https://www.google.com")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_split_and_load(rag_manager: RAGManager):
    embeddings = get_embeddings(AIService.AWSBedRock.value)
    urls = ["https://www.google.com"]
    docs = await rag_manager.load_urls(urls=urls, max_depth=0)
    vector_store = await rag_manager.load_documents(docs=docs, embeddings=embeddings)
    assert vector_store is not None
