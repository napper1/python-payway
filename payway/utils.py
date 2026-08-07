from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus

from payway.exceptions import PaywayError


def snake_to_camel(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(word.title() for word in rest)


def json_list(name: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        def wrapper(*args: dict, **kwargs: dict) -> dict:
            result = function(*args, **kwargs)
            if result.status_code == HTTPStatus.NO_CONTENT:
                # DELETE methods successful response
                return result
            if result.status_code in [HTTPStatus.OK, HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY]:
                return result.json()
            raise PaywayError(result.status_code, result.text)

        return wrapper

    return decorator
