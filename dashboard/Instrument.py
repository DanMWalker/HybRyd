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
                self.settable = config['settable']
                self.gettable = config['gettable']

            # If we cannot load the file and assign the variables of the Instrument
            except Exception as e:
                # Raise a flag that indicates the failure
                self.config_found = False

                # And add the exception to the message buffer
                push_message(str(e), "a file selection widget")
        else:
            push_message(dst + " was not found.")

        # Report the success state of the config load at end of method call
        return self.config_found

    def gen_rack_element(self):
        pass

    def __str__(self):
        return "_".join(self.idn)