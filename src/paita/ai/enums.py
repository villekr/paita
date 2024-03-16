from enum import Enum


class AIService(Enum):
    AWSBedRock = "AWS Bedrock"
    OpenAIChatGPT = "OpenAI ChatGPT"


class Tag(Enum):
    AI_SERVICE = "ai_services"
    AI_MODELS = "ai_models"


class Role(Enum):
    question = "question"
    answer = "answer"
    info = "info"
