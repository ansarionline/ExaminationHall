from nicegui import ui
import json
import os

import os, json

def save_file(name, total, gained, key='mcqs', wrong=None):
    file_path = f'students/{name}.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Load existing data if file exists and is valid JSON
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
    else:
        data = {}

    # Store the result under the specified key (e.g., "mcqs", "sqs", etc.)
    data[key] = {
        'total': total,
        'gained': gained
    }

    # Optionally include wrong answers if provided
    if wrong:
        data[key]['wrong'] = wrong

    # Save updated data
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
            ui.markdown('-----' + str(item.get('marks', 1)))
        radio = ui.radio(item['choices']).style(radio_styling)
        radios.append(radio)
        answers.append(item['answer'])
        total += item.get('marks', 1)
    return radios, answers, total

def submit_mcqs(radios, answers, name, total, log, qs, exp=None):
    score = 0
    wrong = {}

    for i, r in enumerate(radios):
        user_choice = r.value
        correct_choice = answers[i]
        if user_choice == correct_choice:
            score += 1
        else:
            wrong[f"Q#{i+1}"] = [user_choice, correct_choice]
        r.disable()

    log(f'Submitted: Score: {score}/{total}', name)
    ui.notify(f"{name}, you scored {score}/{total}")
    save_file(name, total, score, qs, wrong=wrong)
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
