# HF Master Pinger - Production Setup

## Date: 2026-01-18

---

## Overview

A centralized Hugging Face Space that keeps all other Spaces alive by pinging them on independent schedules, reducing external ping requirements from Google Apps Script.

---

## Final Architecture

```
    ┌────────────────────────────────────────────────────────┐
    │                    Master Pinger                       │
    │  ┌─────────────┐    ┌─────────────┐    ┌───────────┐  │
    │  │   Gradio    │    │   FastAPI   │    │ Scheduler │  │
    │  │  (UI:7860)  │    │ (API:7861)  │    │(APScheduler)│ │
    │  └─────────────┘    └─────────────┘    └───────────┘  │
    └────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
      ┌──────────┐       ┌──────────┐       ┌──────────┐
      │ Discord  │       │   RAG    │       │   LLM    │
      │   Bot    │       │  Space   │       │ Backend  │
      │  (2 min) │       │  (5 min) │       │  (3 min) │
      └──────────┘       └──────────┘       └──────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| No ping-back | Workers don't ping master - redundant since master was already awake |
| Per-worker intervals | Different services need different ping frequencies |
| Self-ping loop | Keeps master alive between external GAS pings |
| Hardcoded workers | Simple, readable; redeploy when adding workers anyway |
| 120s timeout + 3 retries | Handles cold-start delays gracefully |

---

## How It Works

| Step | Action | Interval |
|------|--------|----------|
| 1 | GAS pings Master `/health` | Every 3-5 min |
| 2 | Master runs scheduler jobs | Per-worker intervals |
| 3 | Self-ping keeps master active | Every 2 min |
| 4 | All Spaces stay alive | Done |

---

## GAS Request Comparison

| Architecture | GAS Requests per 5 min | Per Day |
|--------------|------------------------|---------|
| GAS → Each Space directly | 4 (one per Space) | 1,152 |
| GAS → Master only | 1 | 288 |

**75% reduction in GAS usage**

---

## Components

### Gradio UI (app.py)
- Status dashboard showing worker health
- Uptime display
- Worker table with URL, interval, last ping, status
- Manual refresh button

### FastAPI (main.py)
- `/health` - Simple health check
- `/status` - JSON with uptime and worker status
- Scheduler management via lifespan

### Scheduler (APScheduler)
- Self-ping job: every 2 min
- Per-worker jobs: configurable intervals
- Retry with exponential backoff

---

## Configuration

```python
WORKERS = [
    {"url": "https://discord-bot.hf.space/health", "interval_minutes": 2},
    {"url": "https://rag-space.hf.space/health", "interval_minutes": 5},
    {"url": "https://llm-backend.hf.space/health", "interval_minutes": 3},
]
```

---

## Deployment

### GitHub Actions Pipeline
1. Push to main → triggers deploy.yml
2. Typecheck with pyright
3. Deploy to HF Spaces via git push

### Required Secrets/Variables
- `HF_TOKEN` (secret): HuggingFace access token
- `HF_USERNAME` (variable): HuggingFace username
- `HF_SPACE_NAME` (variable): Space name

---

## Related Notes

See [centralized-hf-master-pinger-architecture.md](centralized-hf-master-pinger-architecture.md) for original design exploration.

See `../.dev-notes/2026-01-17.md` for:
- Space state definitions (Hot/Warm/Cool/Just Alive)
- Use case recommendations by service type
- Industry best practices for ping intervals
