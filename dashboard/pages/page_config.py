from bokeh import models as bkm, layouts as bkl
from bokeh.models.widgets import Select
from bokeh.layouts import widgetbox
from utils import insturment_manager

page = bkm.Panel(title="Configure", child = bkm.Div(text=""))



instrument_settings_grid = []

def update_settings_grid():
    instrument_settings_grid = []
    print(insturment_manager)
    for key in insturment_manager.keys():
        instrument = insturment_manager[key]
        select = Select(value="Tunisia", options=["Tunisia", "Algeria", "Canada", "France"])
        instrument_settings_grid.append([bkm.Div(text= str(instrument)), select])


refresh_button = bkm.Button(label="Load Instruments", width=200)
refresh_button.on_click(update_settings_grid)

page.update( 
    child = bkl.column([refresh_button, bkl.layout(instrument_settings_grid)])
    )