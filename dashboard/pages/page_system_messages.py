
from utils import timestamp
from bokeh import layouts as bkl, models as bkm

message_buffer = bkl.column(
    [bkm.Div(text=timestamp()), bkm.Div(text="HybRyd Dashboard Startup")],
    sizing_mode="stretch_both")
message_resolutions = bkl.column([bkm.Div(text=""), bkm.Div(text="")])

page = bkm.Panel(title="System Messages",
                          child=bkl.row([message_buffer, message_resolutions])
                          )

from utils import app_config

notifications = bkm.Div(text="", sizing_mode="stretch_both", align="end")

def log(msg, resolver=None):
    print(msg)
    ts_element = bkm.Div(text=timestamp())
    msg_element = bkm.Div(text=msg)
    message_buffer.children += [ts_element, msg_element]
    message_resolutions.children += [bkm.Div(text="")]
    if resolver is None:
        message_resolutions.children += [bkm.Div(text="")]
    else:
        message_resolutions.children += [resolver]
    if len(message_buffer.children) > app_config["retained_messages"]:
        message_buffer.children = message_buffer.children[-app_config["retained_messages"]:]
        message_resolutions.children = message_resolutions.children[-app_config["retained_messages"]:]

    notifications.update(text="New System Message(s)")