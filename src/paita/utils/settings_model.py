from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class SettingsModel(BaseModel):
    version: float = 0.1
    ai_service: Optional[str] = None
    ai_model: Optional[str] = None
    ai_persona: Optional[str] = "You are a helpful assistant. Answer all questions to the best of your ability."
    ai_streaming: Optional[bool] = True
    ai_model_kwargs: Optional[dict[str, Any]] = {}
    ai_n: Optional[int] = 1
    ai_max_tokens: Optional[int] = 2048
    ai_history_depth: Optional[int] = 20

    ai_rag_enabled: Optional[bool] = False
    ai_rag_vector_store_type: Optional[str] = None
    ai_rag_contextualize_prompt: Optional[str] = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
    ai_rag_system_prompt: Optional[str] = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use two sentences maximum and keep the answer concise.\

{context}"""
