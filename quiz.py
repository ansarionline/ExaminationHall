from nicegui import ui, app
from fastapi import Request
from mcqs import create_mcqs
from sqs import create_sqs
from dtc import create_dtc
from po import create_po
from practical import create_prac
from utils import log
from logs import create_logs
from exam_create import create_exam, get_questions
from metrices import create_metrices
import os, datetime
import zipfile
import tempfile
from fastapi.responses import FileResponse

class STUDENTS:
    students = []

class METRICS:
   metrics: dict[str, dict] = {}

class TIMERS:
    timer:dict[str, float] = {}

@app.get('/download-all-students')
def download_all_students():
    temp_zip_path = tempfile.mktemp(suffix='.zip')
    with zipfile.ZipFile(temp_zip_path, 'w') as zipf:
        for root, dirs, files in os.walk('students'):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, 'students')
                zipf.write(full_path, arcname=os.path.join('students', arcname))
    return FileResponse(temp_zip_path, filename='students_all.zip', media_type='application/zip')

from asyncio import sleep
import asyncio

PENDING_UNLOADS = {}
UNLOAD_TASKS = {}

from datetime import datetime, timedelta

LAST_EVENTS = {}

@app.post('/_nicegui_call/log_focus_loss')
async def log_focus_loss(request: Request):
    data = await request.json()
    name = data.get("name", "Unknown")
    reason = data.get("reason", "unknown")

    now = datetime.now()
    LAST_EVENTS[name] = (reason, now)

    if name not in STUDENTS.students:
        return

    if reason == 'page-unload':
        if name in UNLOAD_TASKS:
            UNLOAD_TASKS[name].cancel()

        async def confirm_exit():
            await sleep(2.5)
            last_reason, last_time = LAST_EVENTS.get(name, ('', datetime.min))
            # 🧠 Ensure no return or activity since the page-unload
            if name in STUDENTS.students and last_reason == 'page-unload' and (datetime.now() - last_time) > timedelta(seconds=2):
                STUDENTS.students.remove(name)
                METRICS.metrics[name]['status'] = "Done"
                log(f"left the exam", name)
            UNLOAD_TASKS.pop(name, None)

        UNLOAD_TASKS[name] = asyncio.create_task(confirm_exit())

    elif reason == 'return':
        task = UNLOAD_TASKS.pop(name, None)
        if task:
            task.cancel()
            log("Returned to exam tab", name)

    elif reason == 'visibility-hidden':
        METRICS.metrics.setdefault(name, {}).setdefault('violations', 0)
        METRICS.metrics[name]['violations'] += 1
        log("Focus lost: visibility-hidden", name)

    else:
        log(f"Focus lost: [{reason}]", name)

def apply_exam_protection_js(name: str):
    ui.run_javascript(f"""
    let lastLog = 0;
    let sentOnce = false;
    let returnLogged = false;
    const originalTitle = document.title;

    function sendEvent(reason) {{
        const now = Date.now();
        if (now - lastLog < 1000) return;
        lastLog = now;
        navigator.sendBeacon(
            '/_nicegui_call/log_focus_loss',
            new Blob([JSON.stringify({{ name: '{name}', reason: reason }})], {{ type: 'application/json' }})
        );
    }}

    function showOverlay(msg) {{
        if (document.getElementById('exam-warning-overlay')) return;

        document.title = "⚠️ Warning!";
        const overlay = document.createElement('div');
        overlay.id = 'exam-warning-overlay';
        overlay.innerText = msg;
        overlay.style = `
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(255, 0, 0, 0.85);
            color: white;
            font-size: 32px;
            font-weight: bold;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 99999;
        `;
        document.body.appendChild(overlay);

        setTimeout(() => {{
            overlay.remove();
            document.title = originalTitle;
        }}, 5000);
    }}

    // 🕵️ Detect tab switch or minimize
    document.addEventListener('visibilitychange', () => {{
        if (document.visibilityState === 'hidden') {{
            sendEvent('visibility-hidden');
            showOverlay("⚠️ Do not leave the tab!");
        }}
    }});
    window.addEventListener('beforeunload', (e) => {{
        if (!sentOnce) {{
            sentOnce = true;
            setTimeout(() => sendEvent('page-unload'), 200);
        }}
        e.preventDefault();
        e.returnValue = '';
    }});

    window.addEventListener('pageshow', () => {{
        document.title = originalTitle;
        sendEvent('return');
    }});

    window.addEventListener('focus', () => {{
        sendEvent('return');
    }});

    // 🛡️ Disable right-click
    document.addEventListener('contextmenu', e => e.preventDefault());

    // 🔒 Block developer shortcuts and tab manipulations
    document.addEventListener('keydown', e => {{
        const forbiddenKeys = ["t", "w", "r", "p", "u", "s"];
        if (
            e.key === "F12" ||
            (e.ctrlKey && forbiddenKeys.includes(e.key.toLowerCase())) ||
            (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "i")
        ) {{
            e.preventDefault();
            e.stopPropagation();
            showOverlay("⚠️ Shortcut blocked!");
        }}
    }});
    """)


ADMIN_PATH = '/a/d/m/i/n/admin'
os.environ.setdefault("ADMIN_PASSWORD", "mypass")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "mypass")
@ui.page('/exam/{name}')
def exam(name: str):
        if name not in STUDENTS.students:
            with ui.column().classes('items-center justify-center gap-6').style(
                "width: 95vw; height: 95vh"
            ):
                ui.icon('block').classes('text-red-600').style('font-size: 5rem')
                ui.label('Unauthorized Access').style('user-select:none; color: #b91c1c; font-size: 2rem; font-weight: bold;')
                ui.label('🚫 You must register before accessing this page.')\
                    .style('color: #7f1d1d; font-size: 1rem; user-select:none; text-align: center; max-width: 600px;')
                ui.button('🔐 Go to Registration', on_click=lambda: ui.navigate.to('/'))\
                    .props('unelevated color=red').classes('text-white text-lg px-6 py-2 rounded-lg')
            return
        apply_exam_protection_js(name)
        log('Started Exam', name)
        METRICS.metrics[name] = {
            "start_time": datetime.now().isoformat().split('T')[1].split('.')[0],
            "status": "Started",
            "violations": 0
        }
        file_path = f'students/{name}.json'
        if os.path.exists(file_path):
            os.remove(file_path)
        Questions = get_questions()
        title = Questions.others.get('title', 'Exam')
        ui.markdown(title)
        def log_statu(type_, v):
            log(f'On Q#{i} of type {type_} : {v}', name)
            METRICS.metrics[name]['status'] = f'Q#{i}: {type_}'
        for i, q in enumerate(Questions.questions.keys()):
            i = i + 1
            if   q.__contains__('mcq'):
                create_mcqs(name,Questions.questions[q], log, 
                        lambda v: log_statu('mcq',v), i)
            elif q.__contains__('sqs'):
                create_sqs(name, Questions.questions[q], log, 
                        lambda v: log_statu('sqs',v), i)
            elif q.__contains__('dtc'):
                create_dtc(name, Questions.questions[q], log, 
                        lambda v: log_statu('dtc',v), i)
            elif q.__contains__('poc'):
                create_po(name, Questions.questions[q], log, 
                        lambda v: log_statu('poc',v), i)
            elif q.__contains__('wtc'):
                create_prac(name, Questions.questions[q], log,
                        lambda v: log_statu('wtc',v), i)

def start_exam(name_input):
    entered_name = name_input.value.strip().replace(" ", "_")
    if not entered_name:
        ui.notify("Please enter your name!", type='warning')
    elif entered_name in STUDENTS.students:
        ui.notify("This name is already used. Please use a different one.", type='negative')
    else:
        STUDENTS.students.append(entered_name)
        ui.navigate.to(f'/exam/{entered_name}')

def create_exam_registery_page(others={}):
    @ui.page('/')
    def index():
        with ui.column().classes('items-center justify-center w-full').style("height: 90vh"):
            with ui.card().classes('items-center'):
                title = others.get('reg_message', 'Enter Your name')
                ui.markdown(title)
                name_input = ui.input("Your Name", placeholder="Enter your name").classes('w-80')
                ui.button(
                "Start Test",
                on_click=lambda: start_exam(name_input))\
            .classes('mt-4').style("width:100%")
class AUTHENTICATED:
    authenticated = False

@ui.page(ADMIN_PATH)
def admin():
    AUTHENTICATED.authenticated = False
    with ui.column(align_items='center')\
        .classes('items-center justify-center w-full') as admin_page:
        with ui.card(align_items='center').style('width: 600px; max-width: 90vw; min-height: 500px; max-height: 90vh; overflow-y: auto;'):
            ui.label('💻 Admin Dashboard').classes('text-3xl font-bold mb-4')
            with ui.tabs() as tabs:
                exam_tab = ui.tab('📝 Exam')
                logs_tab = ui.tab('📋 Logs')
                metrices_tab = ui.tab('📊 Metrics')
            with ui.tab_panels(tabs, value=exam_tab).classes('w-full'):
                with ui.tab_panel(exam_tab):
                    create_exam(create_exam_registery_page)
                with ui.tab_panel(logs_tab):
                    create_logs(log)
                with ui.tab_panel(metrices_tab):
                    create_metrices(METRICS)
    def check_password():
        if password_input.value == ADMIN_PASSWORD:
            dialog.close()
            ui.notify('Logged in as admin.', type='positive')
            AUTHENTICATED.authenticated = True
        else:
            ui.notify('Incorrect password', type='negative',
                    close_button=True)
    dialog = ui.dialog().props('persistent')
    with dialog:
        with ui.card():
            ui.label('Admin Login').classes('text-xl font-bold')
            password_input = ui.input('Password', password=True, password_toggle_button=True)
            with ui.row(align_items='center').classes("justify-between items-center w-full"):
                ui.button('Login', on_click=check_password).props('color=primary')
    if not AUTHENTICATED.authenticated:
        dialog.open()
    else:
        admin_page.visible = True
port = int(os.environ.get("PORT", 8080))
ui.run(host="0.0.0.0", port=port, favicon='📜', title='Examination Hall')
