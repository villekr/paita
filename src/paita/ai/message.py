from typing import Dict, List, Union

from pydantic import BaseModel

from paita.ai.enums import Role


class Message(BaseModel):
    content: Union[str, List[Union[str, Dict]]]
    role: Role
