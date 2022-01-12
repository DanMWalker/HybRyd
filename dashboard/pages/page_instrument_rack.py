import pyvisa as pv
from bokeh import models as bkm, layouts as bkl

from data_manager import DataManager

from .page_system_messages import log

page = bkm.Panel(title="Instrument Rack",
                            child=bkl.grid([bkm.Div(text="Test 1")]))


from instrument import Instrument

rm = pv.ResourceManager()
dm = DataManager()
visa_refresh_button = bkm.Button(label="Load Instruments", width=200)

def refresh_instruments():
    visa_refresh_button.disabled = True

    ports = rm.list_resources()
    visa_ports_display.children = []
    if ports:
        for port in ports:
            try:
                candidate = rm.open_resource(port)

                idn = candidate.query("*IDN?")
                idn = idn.replace("*", "").replace("IDN", "").replace(".", "-").strip()

                inst = Instrument(candidate, dm, *(idn.split(",")[:4]))
                inst.load_config()

                visa_ports_display.children += [inst.instrument_widget.generate()]
                #[bkm.Div(text=port+"\t:</br>"+str(inst))]

            except Exception as e:
                log("Exception encountered opening port "+port+" : "+str(e))
                log("Provide a driver file?", bkm.FileInput())
                #visa_ports_display.children += [bkm.Div(text=port+"\t:</br>"+str(e))]
    else:
        message = "No instrument ports were found. Check power and data connections?"
        log(message)
    
    visa_refresh_button.disabled = False


visa_refresh_button.on_click(refresh_instruments)

visa_ports_display = bkl.column([bkm.Div(text="", width=1200)], sizing_mode="stretch_both")

page.update(
    child = bkl.column([visa_refresh_button, visa_ports_display])
    )