from fastapi import Request

import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


logger = structlog.get_logger(__name__)


class RequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start_time = time.time()
        response = await call_next(request)
        duration = "{:.2f}s".format(time.time() - start_time)
        logger.info(
            "Processed Request",
            duration=duration,
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
        )
        return response
