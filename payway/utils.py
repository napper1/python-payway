from __future__ import annotations

from typing import Callable

from payway.exceptions import PaywayError


def json_list(name: str) -> Callable:
    def decorator(function) -> Callable:
        def wrapper(*args: dict, **kwargs: dict) -> dict:
            result = function(*args, **kwargs)
            if result.status_code in [422, 404]:
                return result.json()
            if result.status_code not in [200, 204]:
                raise PaywayError(result.status_code, result.text)
            if result.status_code == 204:
                # DELETE methods successful response
                return result
            return result.json()

        return wrapper

    return decorator
