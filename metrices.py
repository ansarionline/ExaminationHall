from nicegui import ui
import asyncio
from copy import deepcopy

def create_metrices(METRICS):
    columns = [
        {"name": "name", "label": "Name", "field": "name"},
        {"name": "start_time", "label": "StartedAt", "field": "start_time"},
        {"name": "status", "label": "Status", "field": "status"},
        {"name": "violations", "label": "Violations", "field": "violations"},
    ]

    table = ui.table(columns=columns, rows=[]).classes('w-full')\
        .style('height: 50vh; display: block; overflow-y: auto; overflow-x: auto')

    prev_snapshot = deepcopy(METRICS.metrics)  # use deep copy

    async def refresh_metrices():
        nonlocal prev_snapshot
        await asyncio.sleep(0)

        if prev_snapshot != METRICS.metrics:
            new_rows = [
                {
                    "name": name,
                    "start_time": data.get("start_time", ""),
                    "status": data.get("status", ""),
                    "violations": data.get("violations", 0)
                }
                for name, data in METRICS.metrics.items()
            ]
            table.rows = new_rows[::-1]
            prev_snapshot = deepcopy(METRICS.metrics)  # update snapshot deeply

    ui.timer(0.25, lambda: asyncio.create_task(refresh_metrices()))
