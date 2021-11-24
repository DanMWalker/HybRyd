from bokeh import plotting as bkp, models as bkm, layouts as bkl
from datetime import datetime
import pyvisa as pv
from os import path
import json
from bokeh.themes import built_in_themes
from bokeh.io import curdoc

curdoc().theme = "dark_minimal"


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
                            child=bkm.Div(text="Test 1"))
monitor_page = bkm.Panel(title="Control and Monitor",
                         child=bkm.Div(text="Test 2"))
VISA_page = bkm.Panel(title="Connections", child=bkm.Div(text="Test 3"))
message_buffer = bkl.column(
    [bkm.Div(text=timestamp()), bkm.Div(text="HybRyd Dashboard Startup")],
    sizing_mode="stretch_both")
messages_page = bkm.Panel(title="System Messages", child=message_buffer)

page_header = bkm.Div(text="<h1>HybRyd Dashboard</h1>",
                      sizing_mode="stretch_both")
notifications = bkm.Div(text="", sizing_mode="stretch_both", align="end")

top_bar = bkl.row([page_header, notifications])


def push_message(msg):
    ts_element = bkm.Div(text=timestamp())
    msg_element = bkm.Div(text=msg)
    message_buffer.children += [ts_element, msg_element]
    if len(message_buffer.children) > app_config["retained_messages"]:
        message_buffer.children = message_buffer.children[-app_config["retained_messages"]:]
    notifications.update(text="New System Message(s)")


def refresh_instruments():
    ports = rm.list_resources()
    if ports:
        for port in ports:
            try:
                candidate = rm.open_resource(port)
                idn = candidate.query("*IDN?")
                idn.replace("*IDN", "").strip()
                instruments[port] = Instrument(
                    candidate, port, *(idn.split(",")))
            except Exception as e:
                push_message(str(e))
    else:
        message = "No instrument ports were found. Check power and data connections?"
        push_message(message)

    for port in ports:
        instruments[port].load_config()


visa_refresh_button = bkm.Button(label="Load Instruments", width=200)
visa_refresh_button.on_click(refresh_instruments)

VISA_page.update(child=visa_refresh_button)


class Instrument:
    """A class for representing laboratory instruments within the
    HYbRyd control dashboard, driven by prebuilt config files."""

    def __init__(
        self, device, port, manufacturer, model,
        serial="Unspecified", firmware="Unspecified"
    ):

        ### THE FOLLOWING MEMBER VARIABLES ARE SET AT INSTANTIATION ###

        self.device = device  # The open VISA instrument
        self.port = port  # The port identifier the instrument is located at
        self.name = manufacturer + " " + model  # The name of the instrument
        self.serial = serial  # Instrument serial number
        self.firmware = firmware  # Instrument firmware revision

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
            ".", self.manufacturer, self.model, "instrument.cfg"))

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
                self.readable = config['readable']

            # If we cannot load the file and assign the variables of the Instrument
            except Exception as e:
                # Raise a flag that indicates the failure
                self.config_found = False

                # And add the exception to the message buffer
                push_message(str(e))
        else:
            push_message(dst + "was not found.")

        # Report the success state of the config load at end of method call
        return self.config_found

    def gen_rack_element(self):
        pass


t = bkm.Tabs(tabs=[instrument_page, monitor_page, VISA_page,
                   messages_page], sizing_mode="stretch_both")


def clear_notifications(attr, old, new):
    if new == 3:
        notifications.update(text="")


t.on_change("active", clear_notifications)

app_layout = bkl.grid(bkl.column(top_bar, t), sizing_mode="stretch_both")

curdoc().add_root(app_layout)
curdoc().title = "HybRyd Dashboard"
