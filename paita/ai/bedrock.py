# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Helper utilities for working with Amazon Bedrock from Python notebooks"""
# Python Built-Ins:
import os
from typing import Optional

# External Dependencies:
import boto3
from botocore.config import Config

from paita.utils.logger import log


def get_bedrock_client(
    assumed_role: Optional[str] = None,
    region: Optional[str] = None,
    runtime: Optional[bool] = True,
):
    if region is None:
        target_region = os.environ.get(
            "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION")
        )
    else:
        target_region = region

    # log.debug(f"Create new client\n  Using region: {target_region}")
    session_kwargs = {"region_name": target_region}
    client_kwargs = {**session_kwargs}

    profile_name = os.environ.get("AWS_PROFILE")
    if profile_name:
        # log.debug(f"  Using profile: {profile_name}")
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
        log.debug(f"  Using role: {assumed_role}", end="")
        sts = session.client("sts")
        response = sts.assume_role(
            RoleArn=str(assumed_role), RoleSessionName="langchain-llm-1"
        )
        # log.debug(" ... successful!")
        client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        client_kwargs["aws_secret_access_key"] = response["Credentials"][
            "SecretAccessKey"
        ]
        client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]
    if runtime:
        service_name = "bedrock-runtime"
    else:
        service_name = "bedrock"

    bedrock_client = session.client(
        service_name=service_name, config=retry_config, **client_kwargs
    )

    return bedrock_client
