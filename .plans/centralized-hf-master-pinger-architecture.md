# Centralized HF Master Pinger Architecture

## Date: 2026-01-18

---

## Overview

A centralized Hugging Face Space acts as a "Master Pinger" to keep all other Spaces alive, reducing external ping requirements (e.g., Google Apps Script).

---

## Architecture Diagram

```
                    ┌─────────────────┐
                    │  Master Pinger  │
                    │   (HF Space)    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ Discord  │       │   RAG    │       │   LLM    │
   │   Bot    │       │  Space   │       │ Backend  │
   └──────────┘       └──────────┘       └──────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Master Pinger  │
                    │   (ping back)   │
                    └─────────────────┘
```

---

## How It Works

| Step | Action | Interval |
|------|--------|----------|
| 1 | GAS pings Master (only 1 request) | Every 3-5 min |
| 2 | Master pings all workers | Immediately |
| 3 | Workers ping back Master | Immediately |
| 4 | All Spaces stay alive | Done |

---

## GAS Request Comparison

| Architecture | GAS Requests per 5 min | Per Day |
|--------------|------------------------|---------|
| GAS → Each Space directly | 4 (one per Space) | 1,152 |
| GAS → Master only | 1 | 288 |

**75% reduction in GAS usage!**

---

## Potential Issues & Solutions

| Issue | Problem | Solution |
|-------|---------|----------|
| Bootstrap | If Master is sleeping, nothing works | GAS wakes Master, Master wakes others |
| Master fails | All pings stop | Workers could ping each other as fallback |
| Cascade timeout | Master wakes slowly, times out pinging others | Add retry logic or staggered pings |
| Single point of failure | Master down = all down | Keep GAS as backup for critical Spaces |

---

## Implementation: Master Pinger (FastAPI)

```python
from fastapi import FastAPI, BackgroundTasks
import httpx
import asyncio

app = FastAPI()

WORKERS = [
    "https://discord-bot.hf.space/health",
    "https://rag-space.hf.space/health",
    "https://llm-backend.hf.space/health",
]

@app.get("/ping")
async def ping(background_tasks: BackgroundTasks):
    background_tasks.add_task(ping_all_workers)
    return {"status": "pinging workers"}

async def ping_all_workers():
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [client.get(url) for url in WORKERS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Workers will ping back via /health endpoint

@app.get("/health")
async def health():
    return {"status": "alive"}
```

---

## Implementation: Worker Spaces (Add to existing code)

```python
@app.get("/health")
async def health(background_tasks: BackgroundTasks):
    # Ping master back
    background_tasks.add_task(ping_master)
    return {"status": "alive"}

async def ping_master():
    async with httpx.AsyncClient(timeout=30) as client:
        await client.get("https://master-pinger.hf.space/health")
```

---

## Enhanced: Mesh Fallback Architecture

For more resilience, workers can also ping each other if Master fails:

```
         Master
        /  |  \
       A ──┼── B
        \  |  /
           C
```

Each worker pings Master + one neighbor as backup.

---

## Comparison Summary

| Criteria | Centralized Master | Direct GAS to Each |
|----------|-------------------|-------------------|
| GAS usage | 75% less | More requests |
| Complexity | More setup | Simple |
| Reliability | Single point of failure | Independent |
| Scalability | Add workers easily | Update GAS each time |

---

## Recommendation

Use centralized Master architecture but keep GAS as a fallback ping to the most critical Space (e.g., Discord bot) for redundancy.

---

## Clarification: Discord WebSocket Misconception

### What's NOT the Problem
- Discord WebSocket doesn't randomly drop after 5 min of inactivity
- Discord libraries (discord.py/discord.js) automatically send heartbeats every ~41 seconds

### What IS the Problem
The issue is the **HF Space process getting disrupted**, not Discord:

| Hosting | Process Behavior | Discord Connection |
|---------|------------------|-------------------|
| HF Spaces (free) | Process may be throttled/paused when "idle" | Library can't send heartbeats → Discord drops |
| Railway/Fly.io | Process runs continuously 24/7 | Library sends heartbeats normally → stays connected |

### Key Insight
Railway/Fly.io don't do anything special - they just **keep your process running continuously**. If frequent pings keep HF Space processes truly active (not throttled), the Discord library handles heartbeats automatically.

---

## Related Notes

See [2025-01-17.md](2025-01-17.md) for:
- Space state definitions (Hot/Warm/Cool/Just Alive)
- Use case recommendations by service type
- Industry best practices for ping intervals
