from paita.ai.enums import Role
from paita.ai.message import Message


def test_message():
    # Initialize role with "str"
    message = Message(content="Hello", role=Role.question.value)
    assert message.content == "Hello"
    assert message.role == Role.question

    # Initialize role with enum
    message = Message(content="Hello", role=Role.question)
    assert message.content == "Hello"
    assert message.role == Role.question
