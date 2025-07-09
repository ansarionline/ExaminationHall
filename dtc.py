from nicegui import ui
from mcqs import save_file 

def create_editable_aggrid(button0, button1, buggy_code_lines=[]):
    def add_row():
        with ui.dialog() as dialog, ui.card():
            def set(e):
                bug_prev.value = buggy_code_lines[int(e.value) - 1]
            line = ui.number('Line #', on_change=lambda e: set(e), min=1, max=len(buggy_code_lines))
            bug_prev = ui.codemirror('Line from code...', language='Python', highlight_whitespace=True, theme='vscodeDark')\
                        .style('height: 70px;')
            corrected = ui.input('Correction', placeholder='Corrected here...')
            ui.button('Insert', on_click=lambda e: [
                grid.options['rowData'].append({
                    'indx': len(grid.options['rowData']) + 1,
                    'line': line.value,
                    'corrected': corrected.value,
                    'toshow': f"<pre style='margin:0;font-family:monospace'>{corrected.value}</pre>"
                }),
                grid.update(),
                ui.notify('✅ Inserted!', type='positive'),
                dialog.close()
            ])
        dialog.open()

    async def remove():
        rows = await grid.get_selected_rows()
        data = grid.options['rowData']
        for row in rows:
            data.remove(row)
        grid.update()

    grid = ui.aggrid({
        'defaultColDef': {'flex': 1, 'suppressMovable': True},
        'columnDefs': [
            {'headerName': 'Line', 'field': 'line'},
            {'headerName': 'Corrected', 'field': 'toshow'},
        ],
        'rowData': [],
        'rowSelection': 'multiple',
        'animateRows': True,
    }, html_columns=[1]).classes('w-full').style('min-height: 40vh; overflow-y: auto;')

    button0.on_click(add_row).props('icon=add round color=green')
    button1.on_click(remove).props('icon=remove round color=red')

    return grid

def add_dtc(dtc, part, styling, field_style, con_style):
    fields, marks, mistakes = [], [], []
    for j, item in enumerate(dtc):
        with ui.row():
            ui.markdown(part.replace('{n}', str(j)) + item.get('ques', ''))
            ui.markdown('-----' + str(item.get('marks', 0)))
        with ui.row().classes('w-full items-start gap-4 flex-nowrap').\
            style(con_style):
            buggy_code = '\n'.join(item.get('buggy_code_lines', []))
            with ui.column():
                with ui.element('div').classes('resize-x overflow-auto bg-gray-100 p-4 rounded')\
                                      .style('min-width: 100px; max-width: 100%; font-family:monospace; font-size:0.85rem; white-space:pre-wrap; line-height:1.4;')\
                                      .style(styling):
                    ui.markdown(f'```python\n{buggy_code}\n```')
                with ui.button_group():
                    button0 = ui.button()
                    button1 = ui.button()
            with ui.column().classes('flex-1 flex flex-col-reverse'):
                grid = create_editable_aggrid(button0, button1, item.get('buggy_code_lines', []))\
                       .style(field_style)

        fields.append(grid)
        marks.append(item.get('marks', 0))
        mistakes.append(item.get('mistakes', [{}]))
    return fields, mistakes, marks

def submit_dtc(fields, mistakes, marks, name, log, key, exp=None):
    total_score, total_possible = 0, 0
    for i, grid in enumerate(fields):
        rows = grid.options['rowData']
        actual_mistakes = mistakes[i]
        max_marks = marks[i]
        total_possible += max_marks
        if not actual_mistakes:
            continue
        marks_per_fix = max_marks / len(actual_mistakes)
        expected_set = {(int(m['line']), m['corrected'].strip()) for m in actual_mistakes}
        student_set = {(int(row['line']) - 1, row['corrected'].strip()) for row in rows}
        correct_fixes = student_set & expected_set
        wrong_fixes = student_set - expected_set
        score = len(correct_fixes) * marks_per_fix - len(wrong_fixes) * marks_per_fix
        score = max(0, min(score, max_marks))
        total_score += score
        for row in rows:
            row['disabled'] = True
        grid.update()
    save_file(name, total_possible, total_score, key=key)
    ui.notify(f"Your total DTC score: {total_score}/{total_possible}", type='positive')
    log(f"Submitted DTC: {total_score}/{total_possible}", name)
    if exp:
        exp.set_value(False)
        exp.disable()

def safe(data, key='', else_=''):
    try:
        return data[0][key]
    except:
        return else_

def create_dtc(name, dtc, log=lambda: (), on_val=lambda: (), i=0):
    i = str(i)
    statement = safe(dtc, 'statement').replace('{N}', i)
    statement_styling = safe(dtc, 'statement_styling').replace('{N}', i)
    part = safe(dtc, 'part_state')
    styling = safe(dtc, 'qstyling')
    props = safe(dtc, 'props')
    fixfield_styling = safe(dtc, 'fixfield_styling')
    con_style = safe(dtc, 'container_style')
    with ui.expansion(statement, on_value_change=lambda e: [on_val(e.value)])\
            .style(statement_styling).props(props if props else '') as exp:
        fields, mistakes, marks = add_dtc(dtc[1:], part, styling, fixfield_styling,
                                        con_style)
        ui.button("Submit", on_click=lambda:
            submit_dtc(fields, mistakes, marks, name, log,f"Q#{i}: DTCs", exp)
        )
