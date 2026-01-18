# /healthz Endpoint with FastAPI + Gradio Mount

## Date: 2026-01-19

---

## Problem

Need a `/healthz` endpoint for keep-alive pings from GAS, but Gradio's routing intercepts all routes when running as the main app.

### Previous Architecture (Problematic)

```
Port 7860: Gradio (main)     ← GAS pings here, but Gradio intercepts
Port 7861: FastAPI (internal) ← /healthz lives here, unreachable externally
```

---

## Solution: FastAPI as Main App with Gradio Mount

Instead of running Gradio and FastAPI on separate ports, create FastAPI as the main app and mount Gradio on it.

### New Architecture

```
Request to port 7860
    |
    v
FastAPI app (main.py)
    |
    +---> /healthz --> PlainTextResponse("ok")
    +---> /status  --> JSON status
    |
    +---> /* --> Gradio mounted app (UI)
```

---

## Implementation

### main.py

```python
from fastapi.responses import PlainTextResponse

@app.get("/healthz")
async def healthz() -> PlainTextResponse:
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")
```

### app.py

```python
import gradio as gr
from main import app

demo = create_ui()
combined_app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(combined_app, host="0.0.0.0", port=7860)
```

---

## Why This Works

1. **Route priority**: FastAPI routes registered before mounting take precedence
2. **No Gradio interference**: Gradio is mounted as a sub-application at `/`, not as the main app
3. **Clean separation**: Health endpoint lives outside Gradio's routing entirely
4. **Single port**: Everything runs on port 7860

---

## Endpoint

- URL: `https://<space-name>.hf.space/healthz`
- Response: `ok` (plain text)
- Use case: Keep-alive pings from Google Apps Script

---

## Related

- See [production-setup.md](production-setup.md) for full architecture
- See `../.dev-notes/2026-01-17.md` for ping interval recommendations
