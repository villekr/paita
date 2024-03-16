import pytest

from paita.utils.string_utils import dict_to_str, str_to_dict, str_to_num


def test_to_num():
    assert str_to_num("1") == 1
    assert str_to_num("2.1") == 2.1
    assert str_to_num("string") == "string"
    assert str_to_num(1) == 1
    assert str_to_num(2.1) == 2.1


def test_str_to_dict():
    value_str = " temperature=1, top_p= 0.95 ,\t max_tokens_to_sample = 1000\n"
    value_dict = str_to_dict(value_str)
    assert value_dict == {
        "temperature": 1,
        "top_p": 0.95,
        "max_tokens_to_sample": 1000,
    }


def test_str_to_dict_invalid():
    invalid_1 = " temperature, top_p= 0.95 ,\t max_tokens_to_sample = 1000\n"
    invalid_2 = " temperature=1, top_p= ,\t max_tokens_to_sample = 1000\n"
    invalid_3 = " temperature=1, top_p ,\t max_tokens_to_sample = 1000\n"
    invalid_4 = " temperature=1,,\t max_tokens_to_sample = 1000\n"

    assert str_to_dict(invalid_1) == {
        "max_tokens_to_sample": 1000,
        "top_p": 0.95,
    }

    with pytest.raises(ValueError, match="Invalid key-value pair"):
        str_to_dict(invalid_2)

    assert str_to_dict(invalid_3) == {
        "max_tokens_to_sample": 1000,
        "temperature": 1,
    }

    assert str_to_dict(invalid_4) == {
        "max_tokens_to_sample": 1000,
        "temperature": 1,
    }


def test_dict_to_str():
    value_dict = {
        "temperature": 1,
        "top_p": 0.95,
        "max_tokens_to_sample": 1000,
        "discard": {"nested": "dictionary"},
    }
    value_str = dict_to_str(value_dict)
    assert value_str == "max_tokens_to_sample=1000,temperature=1,top_p=0.95"
