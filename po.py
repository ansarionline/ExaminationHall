from nicegui import ui
import os, json

def save_file(name, total, gained, key = 'mcqs'):
    file_path = f'students/{name}.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[key] = {
        'total': total,
        'gained': gained
    }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def submit_po(outputs, questions, marks, corrects, name, log, qs, exp=None):
    def clean(text):
        """Normalize string: strip, lowercase, remove extra spaces"""
        return '\n'.join([line.strip() for line in text.strip().splitlines()]).lower()

    def similarity_score(ans, corr):
        ans_lines = clean(ans).splitlines()
        corr_lines = clean(corr).splitlines()

        if not corr_lines:
            return 0.0
        
        match_count = sum(1 for a, b in zip(ans_lines, corr_lines) if a == b)
        total_lines = len(corr_lines)

        return match_count / total_lines if total_lines else 0

    total = sum(marks)
    gained = 0
    for i in range(len(outputs)):
        user_ans = outputs[i].value
        expected = corrects[i]
        score_ratio = similarity_score(user_ans, expected)
        partial_score = round(score_ratio * marks[i], 1)
        gained += partial_score

    log(f'Submitted PO: Score: {gained}/{total}', name)
    ui.notify(f"{name}, you scored {gained}/{total}")

    for output in outputs:
        output.disable()

    save_file(name, total, gained, qs)

    if exp:
        exp.set_value(False)
        exp.disable()

def add_po( po=[],
            part_stat  =  '',
            styling = '',
            ostyle = '',
            con_style = ''):
    marks = []
    codes = []
    outputs = []
    actual = []
    for idx,i in enumerate(po):
        mark = i.get('marks', 0)
        code = i.get('code', '')
        with ui.row():
            ui.markdown(part_stat.replace('{n}', f'{idx + 1}'))
            ui.markdown('-----' + str(mark))
        with ui.element('div').style(con_style):
            with ui.element('div').classes('resize-x overflow-auto bg-gray-100 p-4 rounded')\
                            .style('min-width: 100px; max-width: 100%; font-family:monospace; font-size:0.85rem; white-space:pre-wrap; line-height:1.4;')\
                            .style(styling):
                ui.markdown(f'```python\n{code}\n```')
            output = ui.codemirror('', language='PowerShell', theme='vscodeDark').style(ostyle)
        marks.append(mark)
        codes.append(code)
        outputs.append(output)
        actual.append(i.get("correct", ''))
    return codes, outputs, marks, actual

def safe(mcqs, part='', else_=''):
    try:
        return mcqs[0][part]
    except:
        return else_

def create_po(name, po, log, on_val = lambda : (), i = 0):
    i = str(i)
    statement = safe(po, 'statement').replace('{N}', i)
    statement_styling = safe(po, 'statement_styling').replace('{N}', i)
    part = safe(po, 'part_state')
    styling = safe(po, 'qstyling')
    props = safe(po, 'props')
    pofield_styling = safe(po, 'pofield_styling')
    con_style = safe(po, 'container_style')
    with ui.expansion(statement, on_value_change=lambda e: [
                on_val(e.value)
        ]).props(props if props else '').style(statement_styling) as exp:
        codes, outputs, marks, actual = add_po(po[1:], part,
                                            styling, pofield_styling,
                                            con_style)
        ui.button('Submit', on_click=lambda: 
            submit_po(outputs, codes, marks, actual, name, log, f"Q#{i}: PO", exp)
        )
