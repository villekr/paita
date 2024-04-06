from __future__ import annotations

import asyncio
import os
from functools import partial
from typing import Optional

import boto3
from botocore.config import Config
from langchain_community.chat_models.bedrock import BedrockChat

from paita.ai.services.service import Service
from paita.utils.logger import log

# https://github.com/langchain-ai/langchain/issues/11668
BEDROCK_DISABLE_STREAMING = bool(os.getenv("BEDROCK_DISABLE_STREAMING", "True"))


class Bedrock(Service):
    @classmethod
    async def models(cls):
        loop = asyncio.get_event_loop()
        try:
            bedrock_client = cls._get_bedrock_client(runtime=False)
            pf = partial(bedrock_client.list_foundation_models, byOutputModality="TEXT")
            response = await loop.run_in_executor(None, pf)
            models = [model["modelId"] for model in response["modelSummaries"]]
            return sorted(models)
        except Exception as e:  # noqa: BLE001 TODO
            log.info(e)
            return []

    def chat_model(self) -> BedrockChat:
        model_kwargs = {
            # "max_tokens_to_sample": self._settings_model.ai_max_tokens,
            "temperature": 1,
            "top_k": 250,
            "top_p": 0.8,
            # "stop_sequences": ["\n\nHuman"],
        }
        if self._settings_model.ai_model_kwargs:
            model_kwargs.update(self._settings_model.ai_model_kwargs)
        log.debug(f"{model_kwargs=}")
        return BedrockChat(
            model_id=self._settings_model.ai_model,
            streaming=(False if BEDROCK_DISABLE_STREAMING else self._settings_model.ai_streaming),
            model_kwargs=model_kwargs,
            # max_tokens=settings_model.ai_max_tokens,
            # n=settings_model.ai_n,
            callbacks=[self._callback_handler],
            # callback_manager=callback_handler,
        )

    @classmethod
    def _get_bedrock_client(
        cls,
        *,
        assumed_role: Optional[str] = None,
        region: Optional[str] = None,
        runtime: Optional[bool] = True,
    ):
        target_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION")) if region is None else region

        session_kwargs = {"region_name": target_region}
        client_kwargs = {**session_kwargs}

        profile_name = os.environ.get("AWS_PROFILE")
        if profile_name:
            session_kwargs["profile_name"] = profile_name

        retry_config = Config(
            region_name=target_region,
            connect_timeout=10,
            read_timeout=3,
            retries={
                "max_attempts": 3,
                "mode": "standard",
            },
        )
        session = boto3.Session(**session_kwargs)

        if assumed_role:
            sts = session.client("sts")
            response = sts.assume_role(RoleArn=str(assumed_role), RoleSessionName="langchain-llm-1")
            client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
            client_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
            client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]
        service_name = "bedrock-runtime" if runtime else "bedrock"

        return session.client(service_name=service_name, config=retry_config, **client_kwargs)
