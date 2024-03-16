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
