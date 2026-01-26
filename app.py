from datetime import datetime

import gradio as gr
import uvicorn

from main import WORKERS, app, start_time, worker_status


def get_status() -> tuple[str, str, list[list[str]]]:
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

    # Worker table data
    table_data = []
    for worker in WORKERS:
        url = worker["url"]
        interval = f"{worker['interval_minutes']} min"
        ws = worker_status.get(url, {})
        last_ping = ws.get("last_ping", "Not yet")
        ping_status = "✅" if ws.get("status") == "ok" else ("❌" if ws.get("status") == "failed" else "⏳")
        consecutive_failures = ws.get("consecutive_failures", 0)
        auto_restart = "🔄" if worker.get("space_id") else ""
        table_data.append([url, interval, str(last_ping), ping_status, str(consecutive_failures), auto_restart])

    return status, uptime, table_data


def create_ui() -> gr.Blocks:
    """Create Gradio UI."""
    with gr.Blocks(title="HF Master Pinger") as demo:
        gr.Markdown("# 🏓 HF Master Pinger")
        gr.Markdown("Centralized pinger to keep HF Spaces alive")

        with gr.Row():
            status_text = gr.Textbox(label="Status", interactive=False)
            uptime_text = gr.Textbox(label="Uptime", interactive=False)

        worker_table = gr.Dataframe(
            headers=["URL", "Interval", "Last Ping", "Status", "Failures", "Auto-Restart"],
            label="Workers",
            interactive=False,
        )

        refresh_btn = gr.Button("🔄 Refresh")

        def refresh():
            return get_status()

        refresh_btn.click(fn=refresh, outputs=[status_text, uptime_text, worker_table])
        demo.load(fn=refresh, outputs=[status_text, uptime_text, worker_table])

    return demo


# Create Gradio UI and mount on FastAPI
demo = create_ui()
combined_app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(combined_app, host="0.0.0.0", port=7860)
