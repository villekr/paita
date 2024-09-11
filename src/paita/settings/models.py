from __future__ import annotations

# class RAGSourceType(Enum):
#     web_page = "web_page"
#
#
# class RAGVectorStoreType(Enum):
#     CHROMA = "chroma"


# class RAGSource(BaseModel):
#     rag_source_type: RAGSourceType = RAGSourceType.web_page
#     rag_source: Optional[str] = None
#     rag_source_max_depth: int = 1
#     rag_document_ids: List[str] = []
#
#     class Config:
#         use_enum_values = False
#
#
# class RAGSources(BaseModel):
#     rag_sources: List[RAGSource] = []
#
#
# class RAGModel(BaseModel):
#     app_name: str
#     app_author: str
#     embeddings: Embeddings
#     vector_store_type: RAGVectorStoreType
#
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     rag_enabled: Optional[bool] = False
#     rag_vector_store_type: Optional[str] = None
#     rag_contextualize_prompt: Optional[str] = """Given a chat history and the latest user question \
#     which might reference context in the chat history, formulate a standalone question \
#     which can be understood without the chat history. Do NOT answer the question, \
#     just reformulate it if needed and otherwise return it as is."""
#     rag_system_prompt: Optional[str] = """You are an assistant for question-answering tasks. \
#     Use the following pieces of retrieved context to answer the question. \
#     If you don't know the answer, just say that you don't know. \
#     Use two sentences maximum and keep the answer concise.\
#
#     {context}"""
