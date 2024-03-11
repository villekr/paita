from enum import Enum


class AIService(Enum):
    AWSBedRock = "AWS Bedrock"
    OpenAIChatGPT = "OpenAI ChatGPT"
    # LocalMock = "Local Mock"


class Tag(Enum):
    AI_SERVICE = "ai_services"
    AI_MODELS = "ai_models"
