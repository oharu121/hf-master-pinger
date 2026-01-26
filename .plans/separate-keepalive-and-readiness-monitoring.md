# Separate Keep-Alive and DB Readiness Monitoring

**Status:** Completed
**Date:** 2026-01-27

## Goal

Refactor the monitoring system to clearly separate two concerns:
1. **Keep-Alive Pings** - Simple health checks to prevent Spaces from sleeping
2. **DB Readiness Monitoring** - Health checks with failure tracking and auto-restart

## Problem

The original implementation conflated keep-alive pings with DB readiness monitoring. This made it unclear what each worker entry was doing and prevented independent tuning of intervals.

## Solution

### Two-Entry Pattern

For Spaces that need both keep-alive and DB monitoring (like n8n), use two separate config entries:

```python
# Keep-alive (prevents sleep, frequent)
{"url": "https://oharu121-n8n-workflow.hf.space/health", "interval_minutes": 5},

# DB readiness monitoring (auto-restart, less frequent)
{
    "url": "https://oharu121-n8n-workflow.hf.space/healthz/readiness",
    "interval_minutes": 60,
    "space_id": "oharu121/n8n-workflow",
},
```

### Two-Table Dashboard

The Gradio UI now displays two separate tables:

**Table 1: Keep-Alive Pings**
| Worker | Interval | Last Ping | Status |
|--------|----------|-----------|--------|

Simple view showing if Spaces are running.

**Table 2: DB Readiness Monitoring**
| Space | Interval | Last Check | Status | Failures | Last Restart | Restarts |
|-------|----------|------------|--------|----------|--------------|----------|

Detailed view with failure tracking and restart history.

### Enhanced Tracking

Added new fields for monitored workers:
- `last_restart_time` - When the last restart was triggered
- `total_restarts` - Total number of restarts since startup

## Files Modified

- [main.py](../main.py) - Updated WORKERS config, added restart tracking
- [app.py](../app.py) - Two-table dashboard, `extract_worker_name()` helper
- [README.md](../README.md) - Updated configuration documentation

## Benefits

1. **Clear separation of concerns** - Each config entry has one purpose
2. **Independent tuning** - Adjust keep-alive and DB check intervals separately
3. **Self-documenting config** - Reading the config shows what each entry does
4. **Better failure visibility** - DB failures get their own dedicated table
5. **Restart history** - Track when and how often restarts occur
