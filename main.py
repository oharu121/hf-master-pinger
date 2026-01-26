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
    {
        "url": "https://oharu121-n8n-workflow.hf.space/healthz/readiness",
        "interval_minutes": 60,
        "space_id": "oharu121/n8n-workflow",
    },
    {"url": "https://oharu121-keiba-oracle.hf.space/healthz", "interval_minutes": 10},
    {"url": "https://oharu121-rag-demo.hf.space/healthz", "interval_minutes": 10},
    {"url": "https://oharu121-rich-chat-demo.hf.space/healthz", "interval_minutes": 10},
]

HF_RESTART_TOKEN = os.getenv("HF_RESTART_TOKEN")
FAILURE_THRESHOLD = 3  # Restart space after this many consecutive failures

TIMEOUT = 120
MAX_RETRIES = 3
SELF_PING_INTERVAL_MINUTES = 2

scheduler = AsyncIOScheduler()
start_time: datetime | None = None
worker_status: dict[str, dict[str, str | int]] = {}


async def restart_space(space_id: str) -> bool:
    """Restart a Hugging Face Space via API."""
    if not HF_RESTART_TOKEN:
        logger.error("HF_RESTART_TOKEN not set, cannot restart space")
        return False

    url = f"https://huggingface.co/api/spaces/{space_id}/restart"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {HF_RESTART_TOKEN}"},
                timeout=30.0,
            )
            if response.status_code == 200:
                logger.info(f"Successfully restarted space: {space_id}")
                return True
            else:
                logger.error(f"Failed to restart {space_id}: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error restarting {space_id}: {e}")
        return False


async def ping_worker_job(worker: dict[str, str | int]):
    """Scheduled job to ping a single worker with retry logic and auto-restart."""
    url = str(worker["url"])
    space_id = worker.get("space_id")

    # Initialize status if not exists
    if url not in worker_status:
        worker_status[url] = {"consecutive_failures": 0}

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
                    "consecutive_failures": 0,
                }
                return
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = 5 * (2**attempt)
                await asyncio.sleep(delay)

    # All retries failed
    consecutive = int(worker_status[url].get("consecutive_failures", 0)) + 1
    logger.error(f"All {MAX_RETRIES} attempts failed for {url} (consecutive failures: {consecutive})")
    worker_status[url] = {
        "last_ping": datetime.now().isoformat(),
        "status": "failed",
        "attempts": MAX_RETRIES,
        "consecutive_failures": consecutive,
    }

    # Auto-restart if threshold reached and space_id is configured
    if space_id and consecutive >= FAILURE_THRESHOLD:
        logger.warning(f"{url} failed {consecutive} consecutive times, restarting {space_id}")
        restarted = await restart_space(str(space_id))
        if restarted:
            worker_status[url]["consecutive_failures"] = 0


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
            args=[worker],
        )
        space_info = f" (auto-restart: {worker['space_id']})" if worker.get("space_id") else ""
        logger.info(f"Scheduled ping for {worker['url']} every {worker['interval_minutes']} min{space_info}")

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
