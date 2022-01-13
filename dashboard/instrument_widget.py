import numpy as np
from copy import deepcopy
from bokeh import layouts as bkl, models as bkm, plotting as bkp


class InstrumentWidget:

    def __init__(self, instrument) -> None:
        self.inst = instrument
        self.linked_enable = {}
        self.linked_disable = {}
        self.periodic_polls = {}

    def generate(self):

        list_layout = self.parse_layout(self.inst.config["layout"])
        return bkl.grid(list_layout)

    def parse_layout(self, layout_spec):
        layout = []
        for element in layout_spec:
            if np.shape(element):
                layout.append(self.parse_layout(element))
            else:
                block = deepcopy(self.inst.config)
                locspec = element.split(":")
                for loc in locspec:
                    block = block[loc]

                if "settings" in locspec:

                    attr = "value"

                    if block["option_type"] == "set":

                        widget = bkm.Select(
                            title=locspec[-1],
                            options=block["options"],
                            value=block["value"]
                        )

                    elif block["option_type"] == "range":

                        widget = bkm.NumericInput(
                            title=locspec[-1],
                            value=block["value"],
                            low=block["options"][0],
                            high=block["options"][1],
                            mode="float"
                        )

                    elif block["option_type"] == "bool":

                        widget = bkm.Toggle(
                            label=locspec[-1],
                            active=block["value"]
                        )

                        attr = "active"

                        # NOT SURE HOW BEST TO HANDLE THESE LINKS?
                        if "enable" in block:
                            pass
                        if "disable" in block:
                            pass
                        # PERHAPS KEEP A RECORD OF INDICES AND APPLY
                        # DEPENDENCIES ONCE LAYOUT IS COMPLETE?
                        # Note - we're only changing GUI elements,
                        # so a js-only callback is sufficient, and
                        # cheaper for not needing the GIL!

                    elif block["option_type"] == "int":

                        bound = 1 if block["options"] == "int+" else None

                        widget = bkm.NumericInput(
                            title=locspec[-1],
                            low=bound,
                            value=block["value"],
                            mode="int"
                        )

                    widget.on_change(attr, self.inst.operations[element])
                    layout.append(widget)

                elif "monitors" in locspec:

                    self.periodic_polls.update({element:None})

                    if block["type"] == "plot":
                        cds = bkm.sources.ColumnDataSource({"x": [], "y": []})
                        self.inst.manager.register(
                            {element: cds}
                        )

                        scatterplot = bkp.figure()
                        scatterplot.dot(x="x", y="y", source=cds)
                        
                        lineplot = bkp.figure()
                        lineplot.line(x="x", y="y", source=cds)

                        scatterpanel = bkm.Panel(
                            child=scatterplot, title="Scatter"
                        )
                        
                        linepanel = bkm.Panel(
                            child=lineplot, title="Line"
                        )

                        plots = bkm.Tabs(
                            tabs=[linepanel, scatterpanel], tabs_location="left"
                        )
                        
                        refresh_rate_input = bkm.NumericInput(
                            title="Polling Interval",
                            low = 1,
                            value = 1000,
                            mode = "int"
                        )

                        enable_rtm = bkm.Toggle(
                            label="Enable Continuous Monitoring",
                            active=False
                        )
                        
                        def polling_methods(element):

                            def poll():
                                to_stream = self.inst.operations[element]()
                                datalen = len(to_stream["x"]) if "x" in to_stream else 0
                                if datalen > 0:
                                    cds.stream(to_stream, datalen)

                            def enable_poll(old, new, attr):
                                if new:
                                    refresh_rate_input.disabled = False
                                    periodic_poll = bkp.curdoc().add_periodic_callback(poll, refresh_rate_input.value)
                                    self.periodic_polls.update({element:periodic_poll})
                                else:
                                    refresh_rate_input.disabled = True
                                    bkp.curdoc().remove_periodic_callback(self.periodic_polls[element])
                                    self.periodic_polls.update({element:None})

                            def update_poll_interval(old, new, attr):
                                cd = bkp.curdoc()
                                if old != new and self.periodic_polls[element] is not None:
                                    cd.remove_periodic_callback(self.periodic_polls[element])
                                    new_poll = cd.add_periodic_callback(poll, new)
                                    self.periodic_polls.update({element:new_poll})
                            
                            return poll, enable_poll, update_poll_interval
                        
                        poll, enable_poll, update_poll_interval = polling_methods(element)
                        enable_rtm.on_change("active", enable_poll)

                        
                        
                        refresh_rate_input.on_change("value", update_poll_interval)


                        widget = bkl.column([plots, bkl.row([refresh_rate_input, enable_rtm])])

                        layout.append(widget)

                    if block["type"] == "num":
                        cds = bkm.sources.ColumnDataSource({"x": []})
                        self.inst.manager.register(
                            {element: cds}
                        )
                        pass

                    pass

        return layout
