import json
import re
from typing import Any, Union


def to_str(value: Any) -> Union[str or None]:
    return str(value) if value else None


def from_str(value: str or None, ttype: Any) -> Union[Any or None]:
    return str(value) if str else ""


def str_to_num(value: Union[int, float, str]) -> Union[int, float, str]:
    if isinstance(value, int) or isinstance(value, float):
        return value
    elif isinstance(value, str):
        try:
            result = int(value)
        except ValueError:
            try:
                result = float(value)
            except ValueError:
                result = value
        return result
    else:
        raise ValueError(f"Invalid type {type(value)}")


def str_to_dict(value: str) -> dict:
    val = re.sub(r"\s+", "", value)

    result = {}
    for kv in val.split(","):
        if "=" in kv:
            key, value_str = kv.split("=")
            if not key or not value_str:
                raise ValueError(f"Invalid key-value pair: {kv}")
            result[key] = str_to_num(value_str)

    return result


def dict_to_str(value: dict) -> str:
    if not isinstance(value, dict):
        raise TypeError("Input must be a dictionary")

    sorted_items = sorted(value.items())

    def is_nested(d):
        return any(isinstance(v, dict) for v in d.values())

    filtered_items = [
        (key, val) for key, val in sorted_items if not is_nested({key: val})
    ]

    return ",".join(f"{key}={json.dumps(val)}" for key, val in filtered_items)
