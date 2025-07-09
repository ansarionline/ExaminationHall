import traceback, os, json
from nicegui import ui

def evaluate_with_asserts(student_code: str, test_cases: list[str]) -> dict:
    output = []
    printed = []
    score = 0
    def mock_print(*args, **kwargs):
        printed.append(' '.join(str(a) for a in args))

    safe_env = {
            'print': mock_print,
            'len': len, 'sum': sum, 'abs': abs, 'chr': chr,
            'divmod': divmod, 'enumerate': enumerate, 'int': int,
            'float': float, 'str': str, 'bool': bool, 'range': range,
            'dict': dict, 'list': list, 'tuple': tuple, 'set': set,
            'id': id, 'ord': ord, 'round': round, 'reversed': reversed,
            'type': type, 'zip': zip,
            'all': all, 'any': any, 'max': max, 'min': min, 'sorted': sorted,
            '__printed__': printed, 'stdout': printed,
        }
    try:
        exec(student_code, safe_env, safe_env)
        for i, test in enumerate(test_cases):
            try:
                exec(test, safe_env, safe_env)
                score += 1
                output.append(f"{i + 1}. ✔ {test}")
            except AssertionError:
                output.append(f"{i + 1}. ❌ {test}")
                continue
            except Exception as e:
                output.append(f"{i + 1}. ⚠️ {test} ➜ {type(e).__name__}: {str(e)}")
                continue
        return {
            'success': True,
            'feedback': '\n'.join(output),
            'score': score,
            'total': len(test_cases)
        }
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        return {
            'success': False,
            'feedback': f"{type(e).__name__}: {str(e)}",
            'score': 0,
            'total': len(test_cases)
        }

def save_file(name, total, gained, key='wtc'):
    file_path = f'students/{name}.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except:
        data = {}
    data[key] = {'total': total, 'gained': gained}
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_in_ui(codefield, tests, logfield: ui.log):
    code = codefield.value
    result = evaluate_with_asserts(code, tests)
    logfield.clear()
    logfield.push(result['feedback'])

def add_wtc(wtc=[], codefield_style='',
            label_style='', 
            cont_style='', 
            part_state='',
            log_style = ''):
    wtc = wtc[1:]
    fields = []
    test_sets = []

    for i, ques in enumerate(wtc):
        ui.markdown(part_state.replace('{N}', str(i + 1))+ ques.get('statement', '') + '-----' + str(len(ques.get('tests', []))) + ' marks')\
            .style(label_style)
        with ui.element('div').style(cont_style):
            codefield = ui.codemirror('', language='Python', theme='vscodeDark').style(codefield_style)
            logfield = ui.log().style(log_style)
            ui.button("Run", on_click=lambda c=codefield, t=ques.get('tests', []), l=logfield: run_in_ui(c, t, l))
            fields.append(codefield)
            test_sets.append(ques.get('tests', []))
    return fields, test_sets

def submit_all(name, fields, test_sets, key = '', log = lambda:(), exp = None):
    total_score = 0
    total_asserts = 0
    for i, codefield in enumerate(fields):
        code = codefield.value
        tests = test_sets[i]
        result = evaluate_with_asserts(code, tests)
        total_score += result['score']
        total_asserts += result['total']
    save_file(name, total_asserts, total_score, key=key)
    log(f'WTC Submitted: Score: {total_score}/{total_asserts}', name)
    ui.notify(f"{name}, your WTC score: {total_score}/{total_asserts}")
    if exp:
        exp.set_value(False)
        exp.disable()

def safe(wtc, part='', else_=''):
    try:
        return wtc[0][part]
    except:
        return else_

def create_prac(name='', wtc=[], log=lambda: (), on_value_change_of_expansion=lambda: (), i=0):
    i = str(i)
    statement = safe(wtc, 'statement').replace('{N}', i)
    statement_styling = safe(wtc, 'statement_styling').replace('{N}', i)
    props = safe(wtc, 'props')
    part_state = safe(wtc, 'part_state')
    qstyling = safe(wtc, 'qstyling')
    codestyle = safe(wtc, 'codearea_style')
    logstyle = safe(wtc, 'log_style')
    cont_style = safe(wtc, 'cont_style')
    with ui.expansion(statement, 
                    on_value_change=lambda e: on_value_change_of_expansion(e.value)
            ).props(props or '').style(statement_styling) as exp:
        fields, test_sets = add_wtc(wtc, codestyle, qstyling,
                                cont_style, part_state, logstyle
                                )
        ui.button("Submit All WTC",
          on_click=lambda: submit_all(name, fields, test_sets, f"Q#{i}: WTC", log, exp)).props('color=green flat')

