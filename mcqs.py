from nicegui import ui
import json
import os

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

def add_mcqs(mcqs=[], part_stat = '', 
            styling = '',
            radio_styling = ''):
    radios = []
    answers = []
    total = 0
    mcqs = mcqs[1:]
    for i,item in enumerate(mcqs):
        with ui.row():
            ui.markdown(part_stat.replace('{n}', f'{i + 1}') + item['ques']).style(styling)
            ui.markdown('-----' + str(item['marks']))
        radio = ui.radio(item['choices']).style(radio_styling)
        radios.append(radio)
        answers.append(item['answer'])
        total += item['marks']
    total = total
    return radios, answers, total

def submit_mcqs(radios, answers, name, total, log, qs, exp = None):
    score = sum(1 for i, r in enumerate(radios) if r.value == answers[i])
    log(f'Submitted: Score: {score}/{total}', name)
    ui.notify(f"{name}, you scored {score}/{total}")
    for i in radios:
        i.disable()
    save_file(name, total, score, qs)
    if exp:
        exp.set_value(False)
        exp.disable()

def safe(mcqs, part='', else_=''):
    try:
        return mcqs[0][part]
    except:
        return else_

def create_mcqs(name='', mcqs=[],  log = lambda:(),
                on_value_change_of_expansion = lambda : (),
                i = 0):
    i = str(i)
    statement = safe(mcqs, 'statement').replace('{N}', i)
    statement_styling = safe(mcqs, 'statement_styling').replace('{N}', i)
    props = safe(mcqs, 'props')
    part = safe(mcqs, 'part_state')
    styling = safe(mcqs, 'qstyling')
    radio_styling = safe(mcqs, 'radio_styling')
    with ui.expansion(statement, on_value_change=lambda e: [
                on_value_change_of_expansion(e.value)
        ]).style(statement_styling).props(props if props else '') as exp:
        radios, answers, total = add_mcqs(mcqs, part, styling, radio_styling)
        ui.button('Submit', on_click=lambda:
            submit_mcqs(radios,
                        answers,
                        name,
                        total,
                        log,
            f"Q#{i}: MCQs",
            exp))

