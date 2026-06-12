from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request
from starlette.responses import Response

from input import (
    max_anonymous_image_size,
    max_authenticated_image_size,
    max_premium_image_size,
    ANONYMOUS_USER,
    USER,
    PREMIUM_USER
)


class UploadLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        user_auth = getattr(request.state, 'authorisations', ANONYMOUS_USER)
        size_limit = {
            PREMIUM_USER: max_premium_image_size,
            USER: max_authenticated_image_size,
            ANONYMOUS_USER: max_anonymous_image_size
        }[user_auth]

        content_len = request.headers.get('content-length')
        if content_len and int(content_len) > size_limit:
            return Response(
                status_code=413,
                content=f"Image size too big {content_len}, max size allowed: {max_anonymous_image_size}")

        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.headers.get('authorisation'):
            request.state.authorisations = USER
        else:
            request.state.authorisations = ANONYMOUS_USER

        return await call_next(request)

