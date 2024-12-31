from __future__ import annotations

from typing import Any


class PaywayError(Exception):
    _code: str = ""
    _message: str = ""

    def __init__(self, code: str, message: str, *args: dict[str, Any], **kwargs: dict[str, Any]) -> None:
        """
        code            : str = PayWay API response/error code
        message         : str = appropriate message
        """

        super().__init__(*args, **kwargs)

        self._code = code
        self._message = f"{code}: {message}"

    def __str__(self) -> str:
        return self._message
