from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class RAGSourceType(Enum):
    web_page = "web_page"


class RAGVectorStoreType(Enum):
    CHROMA = "chroma"


class RAGSource(BaseModel):
    rag_source_type: RAGSourceType = RAGSourceType.web_page
    rag_source: Optional[str] = None
    rag_source_max_depth: int = 1
    rag_document_ids: List[str] = []

    class Config:
        use_enum_values = False


class RAGSources(BaseModel):
    rag_sources: List[RAGSource] = []
