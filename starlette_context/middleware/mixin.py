import logging
from typing import Callable, Optional

from starlette_context.errors import StarletteContextException
from starlette.responses import PlainTextResponse, Response
from starlette.requests import Request


class StarletteContextMiddlewareMixin:
    def __init__(
        self,
        error_handler: Optional[
            Callable[[Request, StarletteContextException], Response]
        ] = None,
        log_errors: bool = False,
        *args,
        **kwargs,
    ):
        self.error_handler = error_handler or self.default_error_handler
        self.log_errors = log_errors

    def log_error(
        self, request: Request, exc: StarletteContextException
    ) -> None:
        if self.log_errors:
            logger = self.get_logger()
            logger.exception("starlette-context exception")

    @staticmethod
    def default_error_handler(
        request: Request, exc: StarletteContextException
    ) -> Response:
        return PlainTextResponse(
            content=exc.detail, status_code=exc.status_code
        )

    @staticmethod
    def get_logger():
        return logging.getLogger("starlette_context")  # pragma: no cover

    def create_response_from_exception(
        self, request: Request, exc: StarletteContextException
    ) -> Response:
        """
        Middleware / plugins exceptions will always result in 500 plain text
        errors.

        These errors can't be handled using exception handlers passed to the
        app instance / middleware. If you need to customize the response,
        handle it here.
        """
        self.log_error(request, exc)
        return self.error_handler(request, exc)
