from typing import Dict, List, Union

from pydantic import BaseModel

from paita.llm.enums import Role


class Message(BaseModel):
    content: Union[str, List[Union[str, Dict]]]
    role: Role
