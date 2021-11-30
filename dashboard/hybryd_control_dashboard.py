from bokeh import plotting as bkp, models as bkm, layouts as bkl
from datetime import datetime
import pyvisa as pv
from os import path
import json
from bokeh.io import curdoc

def timestamp():
    return datetime.now().strftime("%Y-%m-%d@%H:%M:%S")

instruments = {}
rm = pv.ResourceManager()

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


instrument_page = bkm.Panel(title="Instrument Rack",
                            child=bkl.grid([bkm.Div(text="Test 1")]))
monitor_page = bkm.Panel(title="Control and Monitor",
                         child=bkl.grid([bkm.Div(text="Test 2")]))
VISA_page = bkm.Panel(title="Connections", child=bkl.grid([bkm.Div(text="Test 3")]))

message_buffer = bkl.column(
    [bkm.Div(text=timestamp()), bkm.Div(text="HybRyd Dashboard Startup")],
    sizing_mode="stretch_both")
message_resolutions = bkl.column([bkm.Div(text=""), bkm.Div(text="")])
messages_page = bkm.Panel(title="System Messages",
                          child=bkl.row([message_buffer, message_resolutions])
                          )


page_header = bkm.Div(text="<h1>HybRyd Dashboard</h1>",
                      sizing_mode="stretch_both")
notifications = bkm.Div(text="", sizing_mode="stretch_both", align="end")

top_bar = bkl.row([page_header, notifications])


def push_message(msg, resolution_cmd=None):
    print(msg)
    ts_element = bkm.Div(text=timestamp())
    msg_element = bkm.Div(text=msg)
    message_buffer.children += [ts_element, msg_element]
    message_resolutions.children += [bkm.Div(text="")]
    if resolution_cmd is None:
        message_resolutions.children += [bkm.Div(text="")]
    else:
        b = bkm.Button(label = "Resolve")
        message_resolutions.children += [b]
    if len(message_buffer.children) > app_config["retained_messages"]:
        message_buffer.children = message_buffer.children[-app_config["retained_messages"]:]
        message_resolutions.children = message_resolutions.children[-app_config["retained_messages"]:]

    notifications.update(text="New System Message(s)")


def refresh_instruments():
    ports = rm.list_resources()
    visa_ports_display.children = []
    if ports:
        for port in ports:
            try:
                candidate = rm.open_resource(port)

                idn = candidate.query("*IDN?")
                idn = idn.replace("*", "").replace("IDN", "").strip()

                instruments.update({port: Instrument(
                    candidate, port, *(idn.split(",")[:4]))})

                visa_ports_display.children += [bkm.Div(text=port+"\t:\t"+str(instruments[port]))]

            except Exception as e:
                push_message(str(e))
                visa_ports_display.children += [bkm.Div(text=port+"\t:\t"+str(e))]
    else:
        message = "No instrument ports were found. Check power and data connections?"
        push_message(message)

visa_refresh_button = bkm.Button(label="Load Instruments", width=200)
visa_refresh_button.on_click(refresh_instruments)
visa_ports_display = bkl.column([bkm.Div(text="", width=1200)], sizing_mode="stretch_both")
VISA_page.update(
    child = bkl.column([visa_refresh_button, visa_ports_display])
    )


class Instrument:
    """A class for representing laboratory instruments within the
    HYbRyd control dashboard, driven by prebuilt config files."""

    def __init__(
        self, device, port, *spec
    ):

        ### THE FOLLOWING MEMBER VARIABLES ARE SET AT INSTANTIATION ###

        self.device = device  # The open VISA instrument
        self.port = port  # The port identifier the instrument is located at
        self.spec = spec  # The identity of the instrument

        ### THE REMAINING MEMBER VARIABLES ARE SET FROM A CONFIG FILE ###

        self.desc = ""  # A brief description of the instrument
        self.man = ""  # A URL where a manual for the instrument can be found

        self.settable = {}  # A dictionary mapping settable variable names to a tuple
        # of the form (min, max, command, command_arg_count)

        self.gettable = {}  # A dictionary mapping gettable variable names to a tuple
        # of the form (command, command_arg_count)

        self.config_found = False  # A flag indicating whether the config file
        # has been loaded successfully

    def load_config(self):

        # The config file should be called instrument.cfg and located in a directory
        # with a name given by the manufacturer and model of the instrument, as
        # reported by the SCPI *IDN? command
        # This location should be relative to the installation directory of
        # the HybRyd Control Dashboard
        dst = path.abspath(path.join(
            ".","drivers", *self.spec, "instrument.cfg"))

        # Check that the file exists!
        self.config_found = path.isfile(dst)

        # If the config file is found
        if self.config_found:
            try:
                # Try to load the config file as a JSON object
                with open(dst) as config_file:
                    config = json.loads(config_file)

                # And assign the member variables of the Instrument object
                self.desc = config['desc']
                self.man = config['manual']
                self.settable = config['settable']
                self.gettable = config['gettable']

            # If we cannot load the file and assign the variables of the Instrument
            except Exception as e:
                # Raise a flag that indicates the failure
                self.config_found = False

                # And add the exception to the message buffer
                push_message(str(e))
        else:
            push_message(dst + " was not found.")

        # Report the success state of the config load at end of method call
        return self.config_found

    def gen_rack_element(self):
        pass

    def __str__(self):
        return "_".join(self.spec)


t = bkm.Tabs(tabs=[instrument_page, monitor_page, VISA_page,
                   messages_page], sizing_mode="stretch_both")


def clear_notifications(attr, old, new):
    if new == 3:
        notifications.update(text="")


t.on_change("active", clear_notifications)

app_layout = bkl.grid(bkl.column(top_bar, t), sizing_mode="stretch_both")

curdoc().add_root(app_layout)
curdoc().title = "HybRyd Dashboard"
