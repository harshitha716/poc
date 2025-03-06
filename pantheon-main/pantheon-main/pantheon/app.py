from fastapi import FastAPI

from pantheon.middlewares import (
    LoggingMiddleware,
    RequestMiddleware,
)

from fastapi.middleware.cors import CORSMiddleware

from pantheon.routers import health
from pantheon.routers import chat
from pantheon.routers import fileimport
import structlog

from pantheon import settings


logger = structlog.get_logger(__name__)


logger.info("Starting Pantheon API", environment=settings.ENVIRONMENT)

app = FastAPI()

app.add_middleware(CORSMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestMiddleware)


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(fileimport.router)

app.router.redirect_slashes = False

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
