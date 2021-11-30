from bokeh import plotting as bkp, models as bkm, layouts as bkl
from datetime import datetime
import pyvisa
from os import path
import json
from bokeh.io import curdoc


instruments = {}
rm = pyvisa.ResourceManager()

try:
    cfg_path = path.abspath(path.join(".", "config", "dashboard.cfg"))
    with open(cfg_path) as app_config_file:
        app_config = json.load(app_config_file)
except Exception as e:
    print("An exception occurred loading the external config file:\n", e)
    print("Reverting to built-in default config.")
    app_config = {
        "retained_messages": 14,
        "software_instruments": []
    }

t = bkm.Tabs(tabs=[instrument_page, monitor_page, VISA_page,
                   messages_page], sizing_mode="stretch_both")

page_header = bkm.Div(text="<h1>HybRyd Dashboard</h1>",
                      sizing_mode="stretch_both")
notifications = bkm.Div(text="", sizing_mode="stretch_both", align="end")

top_bar = bkl.row([page_header, notifications])

def clear_notifications(attr, old, new):
    if new == 3:
        notifications.update(text="")


t.on_change("active", clear_notifications)

app_layout = bkl.grid(bkl.column(top_bar, t), sizing_mode="stretch_both")

curdoc().add_root(app_layout)
curdoc().title = "HybRyd Dashboard"