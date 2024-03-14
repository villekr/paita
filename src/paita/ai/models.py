import asyncio
from typing import Dict, List

from openai import OpenAI
from openai.types import Model

from paita.ai.bedrock import get_bedrock_client
from paita.ai.enums import AIService
from paita.utils.asyncify import asyncify
from paita.utils.logger import log


async def list_models(ai_service: str = AIService.AWSBedRock.value):
    if ai_service == AIService.AWSBedRock.value:
        return await bedrock_models()
    elif ai_service == AIService.OpenAIChatGPT.value:
        return await openai_models()
    # elif ai_service == AIService.Mock:
    #     return [
    #         "mock_model_1",
    #         "mock_model_2"
    #     ]
    else:
        raise ValueError(f"Invalid value for {ai_service=}")


async def list_all_models() -> Dict[str, List[str] or None]:
    services = [service.value for service in AIService]
    tasks = [list_models(service) for service in services]
    responses: [[str] or None] = await asyncio.gather(*tasks)
    response: Dict[str, List[str]] = {
        service: response
        for service, response in zip(services, responses)  # noqa: B905
    }
    # log.debug(f"{response=}")
    return response


@asyncify
def bedrock_models() -> [str] or None:
    try:
        bedrock_client = get_bedrock_client(runtime=False)
        response = bedrock_client.list_foundation_models(byOutputModality="TEXT")
        return [model["modelId"] for model in response["modelSummaries"]]
    except Exception as e:
        log.info(e)
        return None


@asyncify
def openai_models() -> [str] or None:
    try:
        openai_client = OpenAI()
        response: [Model] = openai_client.models.list()
        return [model.id for model in response.data]
    except Exception as e:
        log.info(e)
        return None


async def main():
    log.debug(await bedrock_models())
    log.debug(await openai_models())
    log.debug(await list_all_models())


if __name__ == "__main__":
    asyncio.run(main())
