from typing import Optional, Sequence

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from starlette_context import starlette_context
from starlette_context.plugins import Plugin
from starlette_context.errors import (
    ConfigurationError,
    MiddleWareValidationError,
)


class ContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that creates empty context for request it's used on. If not
    used, you won't be able to use context object.

    Not to be used with StreamingResponse / FileResponse.
    https://github.com/encode/starlette/issues/1012#issuecomment-673461832
    """

    def __init__(
        self,
        plugins: Optional[Sequence[Plugin]] = None,
        default_error_response: Response = Response(status_code=400),
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        for plugin in plugins or ():
            if not isinstance(plugin, Plugin):
                raise ConfigurationError(
                    f"Plugin {plugin} is not a valid instance"
                )
        self.plugins = plugins or ()
        self.error_response = default_error_response

    async def set_context(self, request: Request) -> dict:
        """
        You might want to override this method.

        The dict it returns will be saved in the scope of a context. You can
        always do that later.
        """
        return {
            plugin.key: await plugin.process_request(request)
            for plugin in self.plugins
        }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            context = await self.set_context(request)
        except MiddleWareValidationError as e:
            error_response = e.error_response or self.error_response
            return error_response

        # create request-scoped context
        with starlette_context(context):
            # process rest of response stack
            response = await call_next(request)
            # gets back to middleware, process response with plugins
            for plugin in self.plugins:
                await plugin.enrich_response(response)
            # retun response before resetting context
            # allowing further middlewares to still use the context
            return response
        # context reset
