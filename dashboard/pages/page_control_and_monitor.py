from bokeh import models as bkm, layouts as bkl

page = bkm.Panel(title="Control and Monitor",
                         child=bkl.grid([bkm.Div(text="Test 2")]))