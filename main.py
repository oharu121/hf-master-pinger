import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKERS = [
    {"url": "https://oharu121-discord-gemini-bot.hf.space/healthz", "interval_minutes": 5},
    {"url": "https://oharu121-n8n-workflow.hf.space/healthz", "interval_minutes": 5},
    {"url": "https://oharu121-keiba-oracle.hf.space/healthz", "interval_minutes": 10},
    {"url": "https://oharu121-rag-demo.hf.space/healthz", "interval_minutes": 10},
    {"url": "https://oharu121-rich-chat-demo.hf.space/healthz", "interval_minutes": 10},
]

TIMEOUT = 120
MAX_RETRIES = 3
SELF_PING_INTERVAL_MINUTES = 2

scheduler = AsyncIOScheduler()
start_time: datetime | None = None
worker_status: dict[str, dict[str, str | int]] = {}


async def ping_worker_job(url: str):
    """Scheduled job to ping a single worker with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=TIMEOUT)
                response.raise_for_status()
                logger.info(f"Successfully pinged {url}")
                worker_status[url] = {
                    "last_ping": datetime.now().isoformat(),
                    "status": "ok",
                    "attempts": attempt + 1,
                }
                return
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = 5 * (2**attempt)
                await asyncio.sleep(delay)

    logger.error(f"All {MAX_RETRIES} attempts failed for {url}")
    worker_status[url] = {
        "last_ping": datetime.now().isoformat(),
        "status": "failed",
        "attempts": MAX_RETRIES,
    }


async def self_ping():
    """Ping own health endpoint to keep the Space alive."""
    port = int(os.getenv("PORT", "7860"))
    url = f"http://localhost:{port}/healthz"
    try:
        async with httpx.AsyncClient() as client:
            await client.get(url, timeout=10)
            logger.info("Self-ping successful")
    except Exception as e:
        logger.warning(f"Self-ping failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global start_time
    start_time = datetime.now()

    # Self-ping job
    scheduler.add_job(self_ping, "interval", minutes=SELF_PING_INTERVAL_MINUTES)

    # Per-worker jobs with individual intervals
    for worker in WORKERS:
        scheduler.add_job(
            ping_worker_job,
            "interval",
            minutes=worker["interval_minutes"],
            args=[worker["url"]],
        )
        logger.info(f"Scheduled ping for {worker['url']} every {worker['interval_minutes']} min")

    scheduler.start()
    logger.info("Scheduler started")
    yield
    scheduler.shutdown()
    logger.info("Scheduler shut down")


app = FastAPI(title="HF Master Pinger", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")


@app.get("/status")
async def status():
    """Status endpoint with worker ping information."""
    uptime_seconds = (datetime.now() - start_time).total_seconds() if start_time else 0
    return {
        "status": "online",
        "uptime_seconds": int(uptime_seconds),
        "workers": worker_status,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
