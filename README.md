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

## Configuration

Edit `main.py` to configure workers:

```python
WORKERS = [
    {"url": "https://your-space.hf.space/health", "interval_minutes": 2},
    {"url": "https://another-space.hf.space/health", "interval_minutes": 5},
]
```

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
