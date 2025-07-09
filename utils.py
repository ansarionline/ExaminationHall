import os, csv, asyncio
from datetime import datetime

LOG_FILE = 'data/logs.csv'

def log(event: str = '', name: str = ''):
    if event:
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name, event])
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            reader = csv.reader(f)
            return list(reader)
    return []
