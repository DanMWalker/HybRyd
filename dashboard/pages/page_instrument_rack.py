import pyvisa as pv
from bokeh import models as bkm, layouts as bkl

from .page_system_messages import log

page = bkm.Panel(title="Instrument Rack",
                            child=bkl.grid([bkm.Div(text="Test 1")]))


from instrument import Instrument

from utils import insturment_manager

rm = pv.ResourceManager()

def refresh_instruments():
    ports = rm.list_resources()
    visa_ports_display.children = []
    if ports:
        for port in ports:
            try:
                candidate = rm.open_resource(port)

                idn = candidate.query("*IDN?")
                idn = idn.replace("*", "").replace("IDN", "").strip()

                insturment_manager.update({port: Instrument(
                    candidate, port, *(idn.split(",")[:4]))})

                visa_ports_display.children += [bkm.Div(text=port+"\t:</br>"+str(insturment_manager[port]))]

            except Exception as e:
                log(str(e))
                visa_ports_display.children += [bkm.Div(text=port+"\t:</br>"+str(e))]
    else:
        message = "No instrument ports were found. Check power and data connections?"
        log(message)



visa_refresh_button = bkm.Button(label="Load Instruments", width=200)
visa_refresh_button.on_click(refresh_instruments)
visa_ports_display = bkl.column([bkm.Div(text="", width=1200)], sizing_mode="stretch_both")

page.update(
    child = bkl.column([visa_refresh_button, visa_ports_display])
    )