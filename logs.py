from nicegui import ui
import asyncio
import os

def create_logs(log):
    log_file = 'data/log.txt'

    columns = [
        {"name": "time", "label": "Time", "field": "time"},
        {"name": "student", "label": "Student", "field": "Student"},
        {"name": "event", "label": "Event", "field": "event"},
    ]

    table = ui.table(columns=columns, rows=[])\
        .classes('w-full').style('height: 60vh; display: block; overflow-y: auto; overflow-x: auto')

    async def refresh_logs():
        await asyncio.sleep(0)
        log_data = log()
        rows = []
        for parts in log_data:
            if isinstance(parts, str):
                parts = parts.strip().split(",", maxsplit=2)
            if len(parts) == 3:
                time, student, event = map(str.strip, parts)
                rows.append({"time": time, "student": student, "event": event})
        table.rows = rows[::-1]
    def clear_log_file():
        try:
            with open(log_file, 'w') as f:
                f.write('')
            ui.notify("Logs cleared", type="positive")
            asyncio.create_task(refresh_logs())
        except Exception as e:
            ui.notify(f"Error clearing logs: {e}", type="negative")
    ui.timer(0.25, lambda: asyncio.create_task(refresh_logs()))
    with ui.row().classes('mt-4'):
        ui.button("Clear Logs", on_click=clear_log_file)\
            .props('unelevated color=red')\
            .classes('text-white')
