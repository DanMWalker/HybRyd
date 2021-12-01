from bokeh import models as bkm, layouts as bkl
from bokeh.models.widgets import Select
from bokeh.layouts import widgetbox
from utils import insturment_manager

page = bkm.Panel(title="Configure", child = bkm.Div(text=""))

def update_settings_grid():
    instrument_settings_grid.children = []
    for key in insturment_manager.keys():
        instrument = insturment_manager[key]
        select = Select(value="Tunisia", options=["Tunisia", "Algeria", "Canada", "France"])
        instrument_settings_grid.children.append(bkl.row([bkm.Div(text= str(instrument), align='center'), select]))

refresh_button = bkm.Button(label="Refresh", width=200)
refresh_button.on_click(update_settings_grid)

instrument_settings_grid = bkl.layout()

page.update( 
    child = bkl.column([refresh_button,instrument_settings_grid])
    )