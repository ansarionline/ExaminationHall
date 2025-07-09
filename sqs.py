from nicegui import ui
import os, json

def save_file(name, key, content = {}):
    file_path = f'students/{name}.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[key] = content
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def submit(ansfields, questions, max_marks, name, log, qs, exp=None):
    answers = [field.value for field in ansfields]
    content = []
    for i, q in enumerate(questions):
        content.append({
            'question': q,
            'answer': answers[i],
            'marks_total': max_marks[i]
        })
    log(f'Submitted: {len(answers)} answers', name)
    ui.notify(f"{name}, your answers have been submitted.")
    for field in ansfields:
        field.disable()
    save_file(name, qs, content)
    if exp:
        exp.set_value(False)
        exp.disable()
def add_sqs(sqs=[],
            part_stat  =  '',
            qstyling = '',
            ansfield_style = ''):
    sqs = sqs[1:]
    ansfields = []
    max_marks = []
    questions = []
    for i, q in enumerate(sqs):
        with ui.row():
            ui.markdown(part_stat.replace('{n}', f'{i + 1}') + q['ques']).style(qstyling)
            ui.markdown('------' + str(q.get('marks', 0)))
        field = ui.textarea(placeholder='Your answer here...').style(ansfield_style)
        ansfields.append(field)
        questions.append(q.get('ques', ''))
        max_marks.append(q.get('marks', 0))
    return questions, ansfields, max_marks

def safe(mcqs, part='', else_=''):
    try:
        return mcqs[0][part]
    except:
        return else_

def create_sqs(name, sqs, log, on_val = lambda : (), i = 0):
    i = str(i)
    statement = safe(sqs, 'statement').replace('{N}', i)
    statement_styling = safe(sqs, 'statement_styling').replace('{N}', i)
    part = safe(sqs, 'part_state')
    styling = safe(sqs, 'qstyling')
    props = safe(sqs, 'props')
    ansfield_styling = safe(sqs, 'ansfield_styling')
    with ui.expansion(statement, on_value_change=lambda e: [
                on_val(e.value)
        ]).props(props if props else '').style(statement_styling) as exp:
        question , answer_fields, max_marks = add_sqs(sqs, part, styling, ansfield_styling)
        ui.button('Submit', on_click=lambda: 
            submit(answer_fields,
                question, max_marks,
                name, 
                log,
                f"Q#{i}: SQs",
                exp)
            )
