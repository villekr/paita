import contextlib
from pathlib import Path
from typing import Iterator

from appdirs import user_config_dir
from bs4 import BeautifulSoup as Soup
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel, ConfigDict

from paita.rag.models import RAGSource, RAGSources, RAGSourceType, RAGVectorStoreType
from paita.utils.json_utils import JsonUtils
from paita.utils.settings_model import SettingsModel


class RAGManagerModel(BaseModel):
    app_name: str
    app_author: str
    embeddings: Embeddings
    vector_store_type: RAGVectorStoreType

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RAGManager:
    def __init__(self, model: RAGManagerModel):
        self.model = model
        config_dir = user_config_dir(appname=self.model.app_name, appauthor=self.model.app_author)
        self.file_path = Path(config_dir) / "rag"
        self.vectorstore = self.create_vectorstore(
            vector_store_type=self.model.vector_store_type,
            persist_directory=str(self.file_path),
            embeddings=self.model.embeddings,
        )
        self.json_utils = JsonUtils(
            app_name=self.model.app_name, app_author=self.model.app_author, file_name="rag_sources.json"
        )

    def chain(
        self,
        *,
        chat: BaseChatModel,
        chat_history: BaseChatMessageHistory,
        settings_model: SettingsModel,
    ):
        retriever = self.vectorstore.as_retriever()

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", settings_model.ai_rag_contextualize_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(chat, retriever, contextualize_q_prompt)

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", settings_model.ai_rag_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)

        question_answer_chain_w_history = RunnableWithMessageHistory(
            question_answer_chain,
            lambda session_id: chat_history,  # noqa: ARG005
            input_messages_key="input",
            history_messages_key="chat_history",
        )

        return create_retrieval_chain(history_aware_retriever, question_answer_chain_w_history)

    async def create(self, *, url: str, max_depth: int = 0):
        docs = await self.load_url_impl(url=url, max_depth=max_depth)
        ids = await self._load_documents(docs=docs)
        rag_sources: RAGSources = RAGSources()
        with contextlib.suppress(FileNotFoundError):
            rag_sources = await self.json_utils.read(rag_sources)

        rag_sources.rag_sources.append(
            RAGSource(
                rag_source_type=RAGSourceType.web_page,
                rag_source=url,
                rag_source_max_depth=max_depth,
                rag_document_ids=ids,
            )
        )
        await self.json_utils.write(rag_sources)

    async def read(self) -> RAGSources:
        rag_sources: RAGSources = RAGSources()
        with contextlib.suppress(FileNotFoundError):
            return await self.json_utils.read(rag_sources)
        return rag_sources

    async def delete(self, url: str):
        rag_sources: RAGSources = RAGSources()
        with contextlib.suppress(FileNotFoundError):
            rag_sources = await self.json_utils.read(rag_sources)

        new_rag_sources = []
        for rag_source in rag_sources.rag_sources:
            if rag_source.rag_source != url:
                rag_sources.append(rag_source)
            else:
                await self.vectorstore.adelete(ids=rag_source.rag_document_ids)

        rag_sources.rag_sources = new_rag_sources
        await self.json_utils.write(rag_sources)

    async def _load_documents(self, *, docs: Iterator[Document]) -> [str]:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
        split_docs = text_splitter.split_documents(docs)

        if self.model.vector_store_type == RAGVectorStoreType.CHROMA:
            filtered_docs = filter_complex_metadata(split_docs)
            return await self.vectorstore.aadd_documents(documents=filtered_docs)

        error_str = f"VectorStoreType {self.model.vector_store_type=} not implemented"
        raise NotImplementedError(error_str)

    async def load_url_impl(self, *, url: str, max_depth: int = 0) -> Iterator[Document]:
        def extractor(x):
            return Soup(x, "lxml")

        loader = RecursiveUrlLoader(
            url=url,
            max_depth=max_depth,
            extractor=lambda x: extractor(x).text,
            check_response_status=True,
        )
        return await loader.aload()

    @classmethod
    def create_vectorstore(
        cls,
        *,
        vector_store_type: RAGVectorStoreType,
        persist_directory: str,
        embeddings: Embeddings,
    ) -> VectorStore:
        if vector_store_type == RAGVectorStoreType.CHROMA:
            from chromadb.config import Settings

            return Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                client_settings=Settings(
                    is_persistent=True,
                    allow_reset=True,
                ),
            )

        error_str = f"VectorStoreType {vector_store_type=} not implemented"
        raise NotImplementedError(error_str)
