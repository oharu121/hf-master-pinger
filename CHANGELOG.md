# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-27

### Added

- Two-table dashboard separating Keep-Alive Pings from DB Readiness Monitoring
- `extract_worker_name()` helper to display friendly Space names from URLs
- Restart history tracking with `last_restart_time` and `total_restarts` fields
- n8n keep-alive entry (`/health` at 5 min) separate from DB readiness (`/healthz/readiness` at 60 min)

### Changed

- Dashboard now shows two distinct tables for different monitoring purposes
- Worker display names extracted from URLs (e.g., `n8n-workflow` instead of full URL)

## [0.2.0] - 2026-01-27

### Added

- Auto-restart Spaces after consecutive health check failures
- Failure tracking per worker with configurable threshold (default: 3 consecutive failures)
- Dashboard columns showing failure count and auto-restart status
- `restart_space()` function to call HF API for Space restart
- `space_id` configuration option for workers to enable auto-restart

## [0.1.0] - Initial Release

### Added

- Centralized pinger service for keeping multiple HF Spaces alive
- Per-worker configurable ping intervals
- Retry with exponential backoff (3 retries: 5s, 10s, 20s)
- 120s timeout for cold-start handling
- Self-ping to keep master alive
- Gradio status dashboard
- FastAPI health and status endpoints
