from typing import List, Tuple

from cache3 import DiskCache

from paita.ai.enums import Tag
from paita.ai.models import get_embeddings
from paita.rag.rag_manager import RAGManager, RAGManagerModel, RAGVectorStoreType
from paita.utils.settings_model import SettingsModel


def create_rag_manager(
    *, app_name: str, app_author: str, settings_model: SettingsModel, cache: DiskCache
) -> RAGManager:
    ai_service = settings_model.ai_service
    ai_services: List[Tuple[str, str]] = list(cache.keys(tag=Tag.AI_MODELS.value))
    if ai_service not in ai_services:
        ai_service = ai_services[0]
    if ai_service is None:
        error_str = f"{ai_service=} must be defined"
        raise ValueError(error_str)

    embeddings = get_embeddings(ai_service)
    try:
        vector_store_type = RAGVectorStoreType(settings_model.ai_rag_vector_store_type)
    except ValueError:
        vector_store_type = RAGVectorStoreType.CHROMA
    return RAGManager(
        RAGManagerModel(
            app_name=app_name,
            app_author=app_author,
            vector_store_type=vector_store_type,
            embeddings=embeddings,
        )
    )
