import asyncio
import signal
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.logger import log
from app.database import init_database, close_database
from app.slack_client import start_socket_mode
from app.routers import health, test


slack_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global slack_client
    try:
        log.info("Initializing database...")
        await init_database()

        log.info("Starting Slack Socket Mode...")
        slack_client = await start_socket_mode()

        log.info("Slack AI Agent is running!")
        if settings.node_env == "development":
            log.info(f"Test endpoint: POST http://localhost:{settings.port}/test/analyze-member")

        yield
    finally:
        log.info("Shutting down...")
        if slack_client:
            await slack_client.close()
        await close_database()
        log.info("Stopped successfully")


app = FastAPI(
    title="Slack AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)

if settings.node_env == "development":
    app.include_router(test.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


def run():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.node_env == "development",
    )


if __name__ == "__main__":
    run()
