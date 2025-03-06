from fastapi import FastAPI

from pantheon_v2.api.middlewares.logging_middleware import LoggingMiddleware
from pantheon_v2.api.middlewares.request_middleware import RequestMiddleware

from fastapi.middleware.cors import CORSMiddleware

from pantheon_v2.api.routers.health.router import router as health_router
import structlog

from pantheon_v2.settings.settings import Settings


logger = structlog.get_logger(__name__)


logger.info("Starting Pantheon_v2 API", environment=Settings.ENVIRONMENT)

app = FastAPI()

app.add_middleware(CORSMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestMiddleware)


app.include_router(health_router)

app.router.redirect_slashes = False

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
