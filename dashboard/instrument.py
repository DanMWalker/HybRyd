from copy import deepcopy
from os import path
import json

import numpy as np
from dashboard.data_manager import DataManager
from dashboard.instrument_widget import InstrumentWidget
from pages.page_system_messages import log


class Instrument:
    """A class for representing laboratory instruments within the
    HybRyd control dashboard, driven by prebuilt config files."""

    def __init__(
        self, device, data_manager : DataManager, *idn: tuple(str)
    ):

        ### THE FOLLOWING MEMBER VARIABLES ARE SET AT INSTANTIATION ###

        self.device = device  # The open VISA instrument
        self.idn = idn  # The identity of the instrument
        self.query = self.device.query

        self.manager = data_manager

        ### THE REMAINING MEMBER VARIABLES ARE SET FROM A CONFIG FILE ###

        self.desc = ""  # A brief description of the instrument
        self.manual = ""  # A URL where a manual for the instrument can be found

        self.config_found = False  # A flag indicating whether the config file
        # has been loaded successfully

        self.config = None

        self.operations = {}

        self.instrument_widget = None

    def load_config(self):

        # The config file should be called instrument.cfg and located in a directory
        # with a name given by the manufacturer and model of the instrument, as
        # reported by the SCPI *IDN? command
        # This location should be relative to the installation directory of
        # the HybRyd Control Dashboard
        dst = path.abspath(path.join(
            ".", "drivers", *self.idn, "instrument.cfg"))

        # Check that the file exists!
        self.config_found = path.isfile(dst)

        # If the config file is found
        if self.config_found:
            try:
                # Try to load the config file as a JSON object
                with open(dst) as config_file:
                    config = json.loads(config_file)
                    self.config = deepcopy(config)

                    if "baud_rate" in config:
                        self.device.baud_rate = config["baud_rate"]

                    if "read_termination" in config:
                        self.device.read_termination = config["read_termination"]

                    if "write_termination" in config:
                        self.device.write_termination = config["write_termination"]

                    if "query_type" in config:
                        if config["query_type"] == "binary":
                            self.query = self.device.query_binary_values
                        elif config["query_type"] == "ascii":
                            self.query = self.device.query_ascii_values

                    if "init" in config:
                        for cmd in config["init"]:
                            self.device.write(cmd)

                    if "settings" in config:
                        for block in config["settings"]:
                            method = self.bind(config["settings"][block])
                            self.operations.update({"settings:"+block: method})

                    if "monitors" in config:
                        for block in config["monitors"]:
                            method = self.bind(config["monitors"][block])
                            self.operations.update({"monitors:"+block: method})

                    # And assign the member variables of the Instrument object
                    self.desc = config['desc'] if 'desc' in config else ""
                    self.manual = config['manual'] if 'manual' in config else ""

            # If we cannot load the file and assign the variables of the Instrument
            except Exception as e:
                # Raise a flag that indicates the failure
                self.config_found = False

                # And add the exception to the message buffer
                log(str(e))

            self.instrument_widget = InstrumentWidget(self)

        else:
            log(dst + " was not found.")

        # Report the success state of the config load at end of method call
        return self.config_found

    def bind(self, command_set):

        keywords = ("init", "on_change", "x", "y", "z")
        cmd_types = ("inst", "query", "read", "write", "proc", "exec")

        def method(*args):

            to_stream = {}
            last_query = None

            if args:
                attr, old, new = args
            else:
                attr, old, new = "", "", ""

            for k in keywords:
                if k in command_set:
                    for command in command_set[k]:
                        if (
                            ("condition" not in command) or
                            ("condition" in command and eval(
                                command["condition"].format(new, old, attr)))
                        ):

                            if "inst" in command:
                                cmdtxt = command["inst"].format(new, old, attr)
                                if "?" in cmdtxt:
                                    last_query = self.query(
                                        cmdtxt, container=np.array)
                                    to_stream.update({k: last_query})
                                else:
                                    self.device.write(cmdtxt)

                            elif "query" in command:
                                cmdtxt = command["query"].format(
                                    new, old, attr
                                )
                                last_query = self.query(
                                    cmdtxt, container=np.array
                                )
                                to_stream.update({k: last_query})

                            elif "read" in command:
                                cmdtxt = command["read"].format(new, old, attr)
                                last_query = self.device.read_raw()
                                to_stream.update({k: last_query})

                            elif "write" in command:
                                cmdtxt = command["write"].format(
                                    new, old, attr)
                                self.device.write(cmdtxt)

                            elif "proc" in command:
                                f = eval(command["proc"].format(
                                    new, old, attr))
                                to_stream.update({k: f(last_query)})

                            elif "exec" in command:
                                exec(command["exec"].format(new, old, attr))

            to_stream = {k: to_stream[k]
                         for k in ("x", "y", "z") if k in to_stream}

            return to_stream

        return method

    def __str__(self):
        return "_".join(self.idn).replace(" ", "").replace("\t", "")
