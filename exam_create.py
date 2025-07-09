from nicegui import ui
import json

class Questions:
    others = {'title': 'Exam Title', 'reg_message': 'Register for test...'}
    questions = {}
    dark = False

def get_row_data(questions: dict):
    rows = []
    for qkey, qdata in questions.items():
        q_type = ''.join(filter(str.isalpha, qkey))
        if isinstance(qdata, list) and len(qdata) > 1:
            total = sum(item.get('marks', 0) for item in qdata)
            rows.append({
                'key': qkey,
                'number': len(rows) + 1,
                'type': q_type,
                'marks': total,
            })
    return rows

def get_questions():
    return Questions

def create_exam(to_be_updated=lambda e=None: ()):
    dialog = ui.dialog().props('persistent')
    questions = Questions.questions
    async def delete_selected():
        rows = await grid.get_selected_rows()
        if not rows:
            ui.notify('Please select question(s) to delete.', type='warning',
                      close_button=True)
            return
        deleted = 0
        for row in rows:
            qkey = row['key']
            if qkey in questions:
                questions.pop(qkey)
                deleted += 1
        if deleted:
            grid.options['rowData'] = get_row_data(questions)
            grid.update()
            to_be_updated(others=Questions.others)
            ui.notify(f'{deleted} question(s) deleted.', type='positive',
                      close_button=True)
        else:
            ui.notify('No selected questions found.', type='negative',
                      close_button=True)
    def handle_upload(event):
        try:
            files = event if isinstance(event, list) else [event]
            uploaded_types = set()
            for file in files:
                content = file.content.read().decode('utf-8')
                data = json.loads(content)
                if not isinstance(data, list) or not isinstance(data[0], dict) or 'type' not in data[0]:
                    ui.notify(f'File `{file.name}` must start with'
                              'a dict that includes a `"type"` key. Skipping the file...', 
                              type='warning',
                      close_button=True)
                    continue
                q_type = data[0]['type'].strip().lower()
                if q_type not in ['mcqs', 'sqs', 'poc', 'wtc', 'dtc']:
                    ui.notify(f'Unsupported question type `{q_type}` in file `{file.name}`. . Skipping the file...',
                                type='warning',
                      close_button=True)
                    continue
                new_data_str = json.dumps(data, sort_keys=True)
                for existing in questions.values():
                    if json.dumps(existing, sort_keys=True) == new_data_str:
                        ui.notify(f'These {q_type.upper()} questions already exist.', 
                                  type='warning',
                      close_button=True)
                        break
                else:
                    key = f"{q_type}{len(questions)}"
                    questions[key] = data
                    Questions.questions = questions
                    uploaded_types.add(q_type.upper())
            if uploaded_types:
                ui.notify(f"{', '.join(uploaded_types)} question(s) uploaded successfully!",
                        type='positive',
                      close_button=True)
            dialog.close()
            grid.options['rowData'] = get_row_data(questions)
            grid.update()
            to_be_updated(others=Questions.others)
        except Exception as e:
            ui.notify(f'Error: {e}', type='negative',
                      close_button=True)

    with dialog:
        with ui.card():
            ui.label('📥 Upload Questions').classes('text-lg font-bold')
            ui.upload(
                label='Upload JSON File',
                auto_upload=True,
                on_upload=handle_upload,
                multiple=True
            ).classes('w-full')
            ui.button('Cancel', on_click=dialog.close).props('flat color=red')

    def create_editor_dialog(title: str, key: str):
        with ui.dialog().props("persistent").classes("items-start justify-start") as dialog, \
            ui.card().style('width: 70vw; height: 70vh; padding: 16px;') as card:
            prev_value = Questions.others.get(key, "")
            def set_value(e):
                Questions.others[key] = e.value
                preview.set_content(e.value)
            def export_html():
                content = preview.content
                filename = f'{key}.html'.replace('_', '')
                ui.download(content.encode(), filename)
            def cancel_edit():
                Questions.others[key] = prev_value
                dialog.close()
            with ui.row().classes("items-center justify-between w-full mb-2"):
                ui.label(title).classes('text-lg font-bold')
                with ui.button_group().props('unelevated round'):
                    ui.button(on_click=export_html)\
                        .props('color=orange unelevated icon=download round outline=True')\
                            .style("font-size: 0.8rem;").tooltip(f"Download")
                    ui.button(on_click=dialog.close)\
                        .props('color=green unelevated icon=check round outline=True')\
                            .style("font-size: 0.8rem;").tooltip(f"Apply")
                    ui.button(on_click=cancel_edit)\
                        .props('color=red unelevated icon=cancel round outline=True')\
                            .style("font-size: 0.8rem;").tooltip(f"Discard")
            with ui.row().classes('gap-4 w-full overflow-auto')\
                    .style('height: calc(100% - 100px);'):
                with ui.column().classes('flex-1 min-w-[300px]').style('height: 100%;'):
                    ui.label('Markdown Editor').classes('text-sm font-semibold')
                    ui.codemirror(
                        value=prev_value,
                        language='Markdown',
                        on_change=set_value
                    ).style('height: 100%; width: 100%; font-size: 0.8rem; border: 1px solid #ccc; border-radius: 8px;')
                with ui.column().classes('flex-1 min-w-[300px]').style('height: 100%;'):
                    ui.label('Live Preview').classes('text-sm font-semibold')
                    preview = ui.markdown(prev_value).style("""
                        height: 100%;
                        width: 100%;
                        overflow-y: auto;
                        background-color: #f9f9f9;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        font-size: 0.85rem;
                    """)
        dialog.open()


    with ui.column(align_items='center').classes('w-full').style('height: 60vh; '\
    'display: block; justify-content: center;'):
        grid = ui.aggrid({
            'defaultColDef': {'flex': 1,
                        'suppressMovable': True
                        },
            'columnDefs': [
                {'headerName': 'QKey', 'field': 'key', 'checkboxSelection': True},
                {'headerName': 'Q#', 'field': 'number', 'checkboxSelection': True},
                {'headerName': 'QType', 'field': 'type'},
                {'headerName': 'Total Marks', 'field': 'marks'},
            ],
            'rowData': get_row_data(questions),
            'rowSelection': 'multiple',
            ':getRowId': 'params => params.data.key'
            }).classes('w-full').style('min-height: 40vh; overflow-y: auto;')

        def toggle_mode():
            Questions.dark = not Questions.dark
            ui.dark_mode(Questions.dark)
            mode_btn.props(f'icon={"dark_mode" if Questions.dark else "light_mode"}')
            grid.classes(
                add='ag-theme-balham-dark' if Questions.dark else 'ag-theme-balham',
                remove='ag-theme-balham ag-theme-balham-dark'
            )
        with ui.row(align_items='center')\
            .classes('gap-2 items-center mx-auto')\
                .style( 'margin-top: 5px; width: 100%;'
                        ' padding: 7px 7px;'
                        ' justify-content: center;'
                        ' border-radius: 50px;'
                ):
        
            ui.button(on_click=delete_selected)\
                .props('icon=delete_forever color=primary round')\
                .tooltip('Delete Selected')

            ui.button(on_click=dialog.open)\
                .props('icon=note_add color=primary round')\
                .tooltip('Add Question')

            ui.button(on_click=lambda : create_editor_dialog('Registry Page', 'reg_message'))\
                .props('icon=chat color=secondary round')\
                .tooltip('Message on Registry Page')

            ui.button(on_click=lambda: create_editor_dialog("Exam Title", "title"))\
                .props('icon=title color=secondary round')\
                .tooltip('Examination Title')

            ui.button(on_click=lambda: ui.download.content(
                json.dumps(Questions.questions, indent=2), "questions.json")
            )\
                .props('icon=file_download color=purple round')\
                .tooltip('Export Questions')

            mode_btn = ui.button(on_click=toggle_mode)\
                .props(f'icon={"dark_mode" if Questions.dark else "light_mode"} color=purple round')\
                .tooltip('Toggle Dark Mode')

            ui.button(on_click=lambda: ui.navigate.to('/',
                                                    new_tab=True))\
                .props('icon=open_in_new color=positive round')\
                .tooltip('Visit Exam Page')

            ui.button(on_click=lambda: ui.navigate.to('/download-all-students', True))\
                .props('icon=save color=positive round')\
                .tooltip('Download student submissions')

            ui.dark_mode(Questions.dark)
            mode_btn.props(f'icon={"dark_mode" if Questions.dark else "light_mode"}')
            grid.classes(
                add='ag-theme-balham-dark' if Questions.dark else 'ag-theme-balham',
                remove='ag-theme-balham ag-theme-balham-dark'
            )

