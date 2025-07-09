from copy import deepcopy
from nicegui import ui
import asyncio

def create_metrices(METRICS):
    column_defs = [
        {'headerName': 'Student', 'field': 'name'},
        {'headerName': 'Started At', 'field': 'start_time'},
        {'headerName': 'Exam Status', 'field': 'status'},
        {'headerName': 'Violations', 'field': 'violations'},
    ]

    grid = ui.aggrid({
        'defaultColDef': {
            'flex': 1,
            'suppressMovable': True,
        },
        'columnDefs': column_defs,
        'rowData': [],
        'rowSelection': 'single',
        'animateRows': True,
    }).classes('w-full').style('min-height: 40vh; overflow-y: auto;')

    prev_snapshot = deepcopy(METRICS.metrics)

    async def refresh_aggrid():
        await asyncio.sleep(0)
        nonlocal prev_snapshot

        if prev_snapshot != METRICS.metrics:
            new_rows = [
                {
                    'name': name,
                    'start_time': data.get('start_time', ''),
                    'status': data.get('status', ''),
                    'violations': data.get('violations', 0),
                }
                for name, data in METRICS.metrics.items()
            ]
            # Sort by most recent addition (if desired)
            new_rows.reverse()  # newest entries at the top
            grid.options['rowData'] = new_rows
            grid.update()
            prev_snapshot = deepcopy(METRICS.metrics)

    ui.timer(0.25, lambda: asyncio.create_task(refresh_aggrid()))
