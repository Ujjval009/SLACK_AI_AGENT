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
from app.routers import health, members, test


slack_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global slack_client
    try:
        log.info("Initializing database...")
        try:
            await init_database()
            log.info("Database initialized successfully")
        except Exception as e:
            log.error(f"Database initialization failed: {e}")
            log.error("App will run without database — Slack events will not be saved")

        log.info("Starting Slack Socket Mode...")
        try:
            slack_client = await start_socket_mode()
            log.info("⚡️ Slack Socket Mode connected")
        except Exception as e:
            log.error(f"Slack Socket Mode connection failed: {e}")
            log.error("Check SLACK_APP_TOKEN and Socket Mode settings in Slack API dashboard")

        if slack_client:
            log.info("✅ Slack AI Agent is fully running!")
        else:
            log.warning("⚠️ App started but Slack bot is not connected — check logs above")

        if settings.node_env == "development":
            log.info(f"Test endpoint: POST http://localhost:{settings.port}/test/analyze-member")

        yield
    finally:
        log.info("Shutting down...")
        if slack_client:
            await slack_client.close()
        try:
            await close_database()
        except Exception as e:
            log.error(f"Database shutdown error: {e}")
        log.info("Stopped successfully")


app = FastAPI(
    title="Slack AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(members.router)

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
