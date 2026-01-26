import re
from datetime import datetime

import gradio as gr
import uvicorn

from main import WORKERS, app, start_time, worker_status


def extract_worker_name(url: str) -> str:
    """Extract Space name from HF URL."""
    # https://oharu121-n8n-workflow.hf.space/health -> n8n-workflow
    match = re.search(r"https://[^-]+-(.+?)\.hf\.space", url)
    return match.group(1) if match else url


def get_status() -> tuple[str, str, list[list[str]], list[list[str]]]:
    """Get current status for Gradio UI."""
    # Overall status
    status = "🟢 Online" if start_time else "🔴 Offline"

    # Uptime
    if start_time:
        uptime_seconds = int((datetime.now() - start_time).total_seconds())
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"
    else:
        uptime = "N/A"

    # Split workers into two tables
    keepalive_data = []
    readiness_data = []

    for worker in WORKERS:
        url = str(worker["url"])
        name = extract_worker_name(url)
        interval = f"{worker['interval_minutes']} min"
        ws = worker_status.get(url, {})
        last_ping = str(ws.get("last_ping", "Not yet"))
        ping_status = "✅" if ws.get("status") == "ok" else ("❌" if ws.get("status") == "failed" else "⏳")

        if worker.get("space_id"):
            # DB Readiness table
            consecutive_failures = str(ws.get("consecutive_failures", 0))
            last_restart = str(ws.get("last_restart_time", "Never"))
            total_restarts = str(ws.get("total_restarts", 0))
            readiness_data.append([name, interval, last_ping, ping_status, consecutive_failures, last_restart, total_restarts])
        else:
            # Keep-alive table
            keepalive_data.append([name, interval, last_ping, ping_status])

    return status, uptime, keepalive_data, readiness_data


def create_ui() -> gr.Blocks:
    """Create Gradio UI."""
    with gr.Blocks(title="HF Master Pinger") as demo:
        gr.Markdown("# HF Master Pinger")
        gr.Markdown("Centralized pinger to keep HF Spaces alive")

        with gr.Row():
            status_text = gr.Textbox(label="Status", interactive=False)
            uptime_text = gr.Textbox(label="Uptime", interactive=False)

        gr.Markdown("## Keep-Alive Pings")
        gr.Markdown("Simple health checks to prevent Spaces from sleeping")
        keepalive_table = gr.Dataframe(
            headers=["Worker", "Interval", "Last Ping", "Status"],
            label="Keep-Alive Workers",
            interactive=False,
        )

        gr.Markdown("## DB Readiness Monitoring")
        gr.Markdown("Health checks with failure tracking and auto-restart")
        readiness_table = gr.Dataframe(
            headers=["Space", "Interval", "Last Check", "Status", "Failures", "Last Restart", "Restarts"],
            label="Monitored Workers",
            interactive=False,
        )

        refresh_btn = gr.Button("Refresh")

        def refresh():
            return get_status()

        refresh_btn.click(fn=refresh, outputs=[status_text, uptime_text, keepalive_table, readiness_table])
        demo.load(fn=refresh, outputs=[status_text, uptime_text, keepalive_table, readiness_table])

    return demo


# Create Gradio UI and mount on FastAPI
demo = create_ui()
combined_app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(combined_app, host="0.0.0.0", port=7860)
