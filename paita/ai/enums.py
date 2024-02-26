from enum import StrEnum


class AIService(StrEnum):
    AWSBedRock = "AWS Bedrock"
    OpenAIChatGPT = "OpenAI ChatGPT"
    # LocalMock = "Local Mock"


class Tag(StrEnum):
    AI_SERVICE = "ai_services"
    AI_MODELS = "ai_models"
