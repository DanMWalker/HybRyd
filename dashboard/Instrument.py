import enum
from os import path
import json
import numpy as np
from pages.page_system_messages import log

class Instrument:
    """A class for representing laboratory instruments within the
    HYbRyd control dashboard, driven by prebuilt config files."""

    def __init__(
        self, device, port, *idn
    ):

        ### THE FOLLOWING MEMBER VARIABLES ARE SET AT INSTANTIATION ###

        self.device = device  # The open VISA instrument
        self.port = port  # The port identifier the instrument is located at
        self.idn = idn  # The identity of the instrument

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
            ".","drivers", *self.idn, "instrument.cfg"))

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
                self.writeable = config['read']
                self.readable = config['write']

            # If we cannot load the file and assign the variables of the Instrument
            except Exception as e:
                # Raise a flag that indicates the failure
                self.config_found = False

                # And add the exception to the message buffer
                log(str(e))
        else:
            log(dst + " was not found.")

        # Report the success state of the config load at end of method call
        return self.config_found

    def gen_rack_element(self):
        pass

    def __str__(self):
        return "_".join(self.idn).replace(" ", "").replace("\t", "")

    def write(self, **kwargs):

        for key in kwargs:
            if key in self.settable:
                minval, maxval, cmd, n_args = self.settable[key]
                x = kwargs[key]

                if np.size(x) == n_args:

                    if np.shape(x):
                        submit = [min(max(minval[i], x[i]), maxval[i]) for i in range(n_args)]
                        if any([s != x[i] for i, s in enumerate(submit)]):
                            msg = "suppplied parameter "+key+"("+str(x)+") out of bounds, using bounded value: "+str(submit)
                            log(msg)
                        self.device.write(cmd.format(*submit))
                    else:
                        submit = min(max(minval, x), maxval)
                        if submit != x:
                            msg = "suppplied parameter "+key+"("+str(x)+") out of bounds, using bounded value: "+str(submit)
                            log(msg)
                        self.device.write(cmd.format(x))
                
                else:
                    log(
                        "Unexpected number of parameters passed to "+str(self)+" argument : "+key+
                        " ("+n_args+" excpected, "+np.shape(kwargs[key])+" recieved)"
                        )
            else:
                log("Parameter "+key+" not recognised as a writeable parameter for "+str(self))

    def read(self, **kwargs):
        pass