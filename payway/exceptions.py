from __future__ import annotations

from typing import NoReturn


class PaywayError(Exception):
    _code: str = None
    _message: str = None

    def __init__(self, code: str, message: str, *args: dict, **kwargs: dict) -> NoReturn:
        """
        code            : str = PayWay API response/error code
        message         : str = appropriate message
        """

        super().__init__(*args, **kwargs)

        self._code = code
        self._message = f"{code}: {message}".encode()

    def __str__(self) -> str:
        return self.message
