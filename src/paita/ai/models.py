import asyncio
from typing import TYPE_CHECKING, Dict, List

from paita.ai.bedrock import get_bedrock_client
from paita.ai.enums import AIService
from paita.utils.asyncify import asyncify
from paita.utils.logger import log

if TYPE_CHECKING:
    from openai.types import Model


async def list_models(ai_service: str = AIService.AWSBedRock.value):
    if ai_service == AIService.AWSBedRock.value:
        return await bedrock_models()
    if ai_service == AIService.OpenAIChatGPT.value:
        return await openai_models()
    # if ai_service == AIService.Mock:
    #     return [
    #         "mock_model_1",
    #         "mock_model_2"
    #     ]
    msg = f"Invalid value for {ai_service=}"
    raise ValueError(msg)


async def list_all_models() -> Dict[str, List[str]]:
    services = [service.value for service in AIService]
    tasks = [list_models(service) for service in services]
    responses: [[str]] = await asyncio.gather(*tasks)
    response: Dict[str, List[str]] = dict(zip(services, responses))
    # log.debug(f"{response=}")
    return response


@asyncify
def bedrock_models() -> [str]:
    try:
        bedrock_client = get_bedrock_client(runtime=False)
        response = bedrock_client.list_foundation_models(byOutputModality="TEXT")
        return [model["modelId"] for model in response["modelSummaries"]]
    except Exception as e:  # noqa: BLE001 TODO
        log.info(e)
        return []


@asyncify
def openai_models() -> [str]:
    from openai import OpenAI

    try:
        openai_client = OpenAI()
        response: [Model] = openai_client.models.list()
        return [model.id for model in response.data]
    except Exception as e:  # noqa: BLE001 TODO
        log.info(e)
        return []


async def main():
    log.debug(await bedrock_models())
    log.debug(await openai_models())
    log.debug(await list_all_models())


if __name__ == "__main__":
    asyncio.run(main())
