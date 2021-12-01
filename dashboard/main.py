from bokeh import plotting as bkp, models as bkm, layouts as bkl
from os import path
import json
from bokeh.io import curdoc

import importlib
import pkgutil

import pages

discovered_pages = [
    importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules(pages.__path__, pages.__name__+".")
]

t = bkm.Tabs(
    tabs=[page_module.page for page_module in discovered_pages],
    sizing_mode="stretch_both"
    )

def clear_notifications(attr, old, new):
    if new == 3:
        notifications.update(text="")

t.on_change("active", clear_notifications)


page_header = bkm.Div(text="<h1>HybRyd Dashboard</h1>",
                      sizing_mode="stretch_both")
notifications = bkm.Div(text="", sizing_mode="stretch_both", align="end")

top_bar = bkl.row([page_header, notifications])


app_layout = bkl.grid(bkl.column(top_bar, t), sizing_mode="stretch_both")

curdoc().add_root(app_layout)
curdoc().title = "HybRyd Dashboard"