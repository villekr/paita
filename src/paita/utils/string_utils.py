from __future__ import annotations

import json
import re
from typing import Any

import validators


def to_str(value: Any) -> str | None:
    return str(value)


def str_to_num(value: float | str) -> float | str:
    if isinstance(value, (float, int)):
        return value
    if isinstance(value, str):
        try:
            result = int(value)
        except ValueError:
            try:
                result = float(value)
            except ValueError:
                result = value
        return result
    msg = f"Invalid type {type(value)}"
    raise TypeError(msg)


def str_to_dict(value: str) -> dict:
    val = re.sub(r"\s+", "", value)

    result = {}
    for kv in val.split(","):
        if "=" in kv:
            key, value_str = kv.split("=")
            if not key or not value_str:
                msg = "Invalid key-value pair"
                raise ValueError(msg)
            result[key] = str_to_num(value_str)

    return result


def dict_to_str(value: dict) -> str:
    if not isinstance(value, dict):
        msg = "Input must be a dictionary"
        raise TypeError(msg)

    sorted_items = sorted(value.items())

    def is_nested(d):
        return any(isinstance(v, dict) for v in d.values())

    filtered_items = [(key, val) for key, val in sorted_items if not is_nested({key: val})]

    return ",".join(f"{key}={json.dumps(val)}" for key, val in filtered_items)


def fix_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def split_and_validate(source: str) -> [str]:
    pattern = r"[,\s;]+"
    urls = re.split(pattern, source)

    fixed_urls = []
    for url in urls:
        fixed_url = fix_url(url)
        if not validators.url(fixed_url):
            error_str = f"Invalid URL: {fixed_url}"
            raise ValueError(error_str)
        fixed_urls.append(fixed_url)

    return fixed_urls


def validate_and_fix_url(url: str) -> [str]:
    fixed_url = fix_url(url)
    if not validators.url(fixed_url):
        error_str = f"Invalid URL: {fixed_url}"
        raise ValueError(error_str)
    return fixed_url
