from nicegui import ui
import asyncio

def create_logs(log):
    columns = [
        {"name": "time", "label": "Time", "field": "time"},
        {"name": "student", "label": "Student", "field": "student"},
        {"name": "event", "label": "Event", "field": "event"},
    ]
    table = ui.table(columns=columns, rows=[]).classes('w-full')\
    .style('height: 60vh; display: block; overflow-y: auto; overflow-x: auto')
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
    ui.timer(0.25, lambda: asyncio.create_task(refresh_logs()))
