import pyvisa as pv
from bokeh import models as bkm, layouts as bkl
import numpy as np

from .page_system_messages import log
from instrument import Instrument
from utils import insturment_manager

rm = pv.ResourceManager()

page = bkm.Panel(title="Dummy Instrument")

def refresh_instruments():
    visa_ports_display.children = []
    
    class dummy_inst:
        def query(self, command):
            return np.random.lognormal(1, 0.1, 1)
        
        def write(self, command):
            return
   
    candidate = dummy_inst()
    port = 'VIRTUAL::DUMMY::DEVICE'
    idn = ['DUMMYINST']

    insturment_manager.update({port: Instrument(candidate, port, *idn)})
    visa_ports_display.children += [bkm.Div(text=port+"\t:</br>"+str(insturment_manager[port]))]


visa_refresh_button = bkm.Button(label="Load Instruments", width=200)
visa_refresh_button.on_click(refresh_instruments)
visa_ports_display = bkl.column([bkm.Div(text="", width=1200)], sizing_mode="stretch_both")

page.update(
    child = bkl.column([visa_refresh_button, visa_ports_display])
    )
