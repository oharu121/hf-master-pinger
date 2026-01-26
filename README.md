---
title: HF Master Pinger
emoji: 🏓
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
python_version: "3.12"
---

# HF Master Pinger

A centralized pinger service that keeps multiple Hugging Face Spaces alive by pinging them on independent schedules.

## Architecture

```
                    ┌─────────────────┐
                    │  Master Pinger  │
                    │   (this Space)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ Discord  │       │   RAG    │       │   LLM    │
   │   Bot    │       │  Space   │       │ Backend  │
   └──────────┘       └──────────┘       └──────────┘
```

## How It Works

1. **GAS (Google Apps Script)** pings Master every 3-5 min to wake it
2. **Master** autonomously pings all workers on their configured intervals
3. **Self-ping** keeps Master alive between external pings
4. **All Spaces stay alive** without individual external pings

## Features

| Feature | Description |
|---------|-------------|
| Per-worker intervals | Each worker has its own ping frequency |
| Retry with backoff | 3 retries with exponential backoff (5s, 10s, 20s) |
| 120s timeout | Handles cold-start delays |
| Self-ping | Keeps master alive independently |
| Status dashboard | Gradio UI showing worker health |
| Auto-restart | Automatically restart Spaces after consecutive health check failures |

## Configuration

Edit `main.py` to configure workers. There are two types of workers:

### Keep-Alive Pings

Simple health checks to prevent Spaces from sleeping:

```python
WORKERS = [
    {"url": "https://your-space.hf.space/health", "interval_minutes": 5},
    {"url": "https://another-space.hf.space/healthz", "interval_minutes": 10},
]
```

### DB Readiness Monitoring with Auto-Restart

For Spaces that need database connectivity monitoring and automatic restart on failure, add `space_id`:

```python
WORKERS = [
    # Keep-alive (prevents sleep)
    {"url": "https://your-space.hf.space/health", "interval_minutes": 5},
    # DB readiness monitoring (triggers restart on failure)
    {
        "url": "https://your-space.hf.space/healthz/readiness",
        "interval_minutes": 60,
        "space_id": "username/space-name",
    },
]
```

This pattern allows you to:
- Keep a Space awake with frequent pings (5 min)
- Monitor DB health less frequently (60 min)
- Auto-restart after 3 consecutive DB check failures

| Setting | Default | Description |
|---------|---------|-------------|
| `url` | Required | Health check endpoint URL |
| `interval_minutes` | Required | Ping frequency in minutes |
| `space_id` | None | HF Space ID for auto-restart (e.g., `username/space-name`) |
| Failure threshold | 3 | Consecutive failures before auto-restart |

**Requirements for auto-restart:**
- `HF_RESTART_TOKEN` environment variable with write permission
- Generate token at https://huggingface.co/settings/tokens

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Gradio status dashboard |
| `/health` | Health check (returns `{"status": "alive"}`) |
| `/status` | JSON status with uptime and worker info |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12 |
| Web Framework | FastAPI |
| Scheduler | APScheduler |
| HTTP Client | httpx |
| UI | Gradio |
| Package Manager | uv |

## Deployment

### HuggingFace Spaces

1. Fork this repository
2. Create a new HF Space with Docker SDK
3. Connect your GitHub repository
4. Set up GitHub secrets:
   - `HF_TOKEN`: Your HuggingFace token
5. Set up GitHub variables:
   - `HF_USERNAME`: Your HuggingFace username
   - `HF_SPACE_NAME`: Your Space name

### Local Development

```bash
# Install dependencies
uv sync

# Run type checking
uv run pyright

# Start the app
uv run python app.py
```

## License

MIT
