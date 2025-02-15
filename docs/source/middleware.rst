==========
Middleware
==========

********
What for
********

The middleware effectively creates the context for the request, so you must configure your app to use it.
More usage detail along with code examples can be found in :doc:`/plugins`.


***********************************
Errors and Middlewares in Starlette
***********************************

There may be a validation error occuring while processing the request in the plugins, which requires sending an error response.
Starlette however does not let middleware use the regular error handler (`more details <https://www.starlette.io/exceptions/#errors-and-handled-exceptions>`_),
so middlewares facing a validation error have to send a response by themselves.

By default, the response sent will be a 400 with no body or extra header, as a Starlette ``Response(status_code=400)``.
This response can be customized at both middleware and plugin level.

The middlewares accepts a ``Response`` object (or anything that inherits it, such as a ``JSONResponse``) through ``default_error_response`` keyword argument at init.
This response will be sent on raised ``starlette_context.errors.MiddleWareValidationError`` exceptions, if it doesn't include a response itself.

.. code-block:: python

    middleware = [
        Middleware(
            ContextMiddleware,
            default_error_response=JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                content={"Error": "Invalid request"},
            ),
            # plugins = ...
        )
    ]


****************************************************
Why are there two middlewares that do the same thing
****************************************************

.. warning::
    ``ContextMiddleware`` middleware is deprecated and will be removed in version 1.0.0.
    Use ``RawContextMiddleware`` instead. For more information, see
    `this ticket <https://github.com/tomwojcik/starlette-context/issues/47>`_.

``ContextMiddleware`` inherits from ``BaseHTTPMiddleware`` which is an interface prepared by ``encode``.
That is, in theory, the "normal" way of creating a middleware. It's simple and convenient.
However, if you are using ``StreamingResponse``, you might bump into memory issues. See
 * https://github.com/encode/starlette/issues/919
 * https://github.com/encode/starlette/issues/1012

Authors recently started to `discourage the use of BaseHTTPMiddleware <https://github.com/encode/starlette/issues/1012#issuecomment-673461832>`_
in favor of what they call "raw middleware". The problem with the "raw" one is that there's no docs for how to actually create it.

The ``RawContextMiddleware`` does more or less the same thing.
It is entirely possible that ``ContextMiddleware`` will be removed in the future release.
It is also possible that authors will make some changes to the ``BaseHTTPMiddleware`` to fix this issue.
I'd advise to only use ``RawContextMiddleware``.

.. warning::
    Due to how Starlette handles application exceptions, the ``enrich_response`` method won't run,
    and the default error response will not be used after an unhandled exception.

    Therefore, this middleware is not capable of setting response headers for 500 responses.
    You can try to use your own 500 handler, but beware that the context will not be available.

****************
How does it work
****************

First, an empty "storage" is created, that's bound to the context of your async request.
The ``set_context`` method allows you to assign something to the context on creation
therefore that's the best place to add everything that might come in
handy later on. You can always alter the context, so add/remove items from it, but each operation comes with some cost.

All ``plugins`` are executed when ``set_context`` method is called. If you want to add something else there you might
either write your own plugin or just overwrite the ``set_context`` method which returns a ``dict``.

Then, once the response is created, we iterate over plugins so it's possible to set some response headers based on the context contents.

Finally, the "storage" that async python apps can access is removed.
