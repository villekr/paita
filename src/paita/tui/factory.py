from paita.llm.models import get_embeddings
from paita.rag.rag_manager import RAGManager, RAGManagerModel, RAGVectorStoreType
from paita.utils.settings_model import SettingsModel


def create_rag_manager(*, app_name: str, app_author: str, settings_model: SettingsModel) -> RAGManager:
    # TODO: Refactor, identical code with settings manager
    ai_service = settings_model.ai_service
    ai_model = settings_model.ai_model

    embeddings = get_embeddings(ai_service=ai_service, ai_model=ai_model)
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
