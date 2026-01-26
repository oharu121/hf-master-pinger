# Auto-Restart n8n on Supabase Connection Failures

## Problem

n8n instance on Hugging Face Spaces intermittently loses connection to Supabase. Manual restart fixes the issue.

## Solution

Enhanced `hf-master-pinger` to automatically restart n8n after consecutive health check failures.

### How It Works

1. **Health Check**: Pings `/healthz/readiness` (tests DB connection) every 60 minutes
2. **Failure Tracking**: Counts consecutive failures per worker
3. **Auto-Restart**: After 3 consecutive failures (3 hours), calls HF API to restart the Space
4. **Dashboard**: Shows failure count and auto-restart status in Gradio UI

### Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| Endpoint | `/healthz/readiness` | Tests actual DB connection, not just n8n reachability |
| Ping interval | 60 minutes | Hourly checks as requested |
| Failure threshold | 3 | Restart after 3 consecutive failures (3 hours of issues) |

### Files Modified (in hf-master-pinger repo)

- `main.py` - Added `restart_space()` function, failure tracking, updated WORKERS config
- `app.py` - Added "Failures" and "Auto-Restart" columns to dashboard

### Key Code Changes

```python
# Worker config with auto-restart
{
    "url": "https://oharu121-n8n-workflow.hf.space/healthz/readiness",
    "interval_minutes": 60,
    "space_id": "oharu121/n8n-workflow",
}

# Restart function
async def restart_space(space_id: str) -> bool:
    url = f"https://huggingface.co/api/spaces/{space_id}/restart"
    response = await client.post(url, headers={"Authorization": f"Bearer {HF_TOKEN}"})
    return response.status_code == 200
```

### Requirements

- `HF_TOKEN` environment variable must have write permission
- Token can be generated at https://huggingface.co/settings/tokens

## Alternative Approaches Considered

1. **Google Apps Script** - Would work but adds another system to maintain
2. **GitHub Actions** - Minimum 5-min interval, less responsive
3. **Internal n8n workflow** - Can't reliably self-heal if n8n is failing

## Root Cause (Still Unknown)

The auto-restart is a pragmatic operational solution. Possible root causes to investigate:

- Supabase free tier connection limits
- HF <-> Supabase network path issues
- n8n connection pooling not handling stale connections
- Supabase pausing (though db-keepalive.sh should prevent this)

## Status

Implemented and deployed. Monitor via hf-master-pinger Gradio dashboard.
