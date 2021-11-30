from datetime import datetime
from dashboard.pages.page_system_messages import message_buffer

def timestamp():
    return datetime.now().strftime("%Y-%m-%d@%H:%M:%S")

