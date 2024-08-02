import pytest

from paita.settings.rag_settings import RAGSource, RAGSources, RAGSourceType
from paita.utils.json_utils import JsonUtils

APP_NAME = "TestApp"
APP_AUTHOR = "TestAuthor"
FILE_NAME = "test_file.json"
RAG_SOURCES = RAGSources(
    rag_sources=[
        RAGSource(
            rag_source_type=RAGSourceType.web_page,
            rag_source="aA",
            rag_source_max_depth=1,
        ),
        RAGSource(
            rag_source_type=RAGSourceType.web_page,
            rag_source="bB",
            rag_source_max_depth=1,
        ),
    ]
)


@pytest.mark.asyncio
async def test_read_not_found():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    with pytest.raises(FileNotFoundError):
        await instance.read(RAGSources)


@pytest.mark.asyncio
async def test_write_read():
    try:
        instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
        await instance.write(RAG_SOURCES)
        rag_sources = await instance.read(RAGSources)
        assert rag_sources == RAG_SOURCES
    finally:
        await instance.delete()


@pytest.mark.asyncio
async def test_delete_not_found():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    with pytest.raises(FileNotFoundError):
        await instance.read(RAGSources)


@pytest.mark.asyncio
async def test_delete():
    instance = JsonUtils(app_name=APP_NAME, app_author=APP_AUTHOR, file_name=FILE_NAME)
    await instance.write(RAG_SOURCES)
    await instance.delete()
    with pytest.raises(FileNotFoundError):
        await instance.read(RAGSources)
