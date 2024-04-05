import asyncio
from typing import Dict, List

from paita.ai.enums import AIService
from paita.ai.services import bedrock, ollama, openai
from paita.utils.logger import log


async def list_models(ai_service: str):
    if ai_service == AIService.AWSBedRock.value:
        return await bedrock.Bedrock.models()
    if ai_service == AIService.OpenAI.value:
        return await openai.OpenAI.models()
    if ai_service == AIService.Ollama.value:
        return await ollama.Ollama.models()
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


async def main():
    log.debug(await bedrock.Bedrock.models())
    log.debug(await ollama.Ollama.models())
    log.debug(await openai.OpenAI.models())
    log.debug(await list_all_models())


if __name__ == "__main__":
    asyncio.run(main())
