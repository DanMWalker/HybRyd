
message_buffer = bkl.column(
    [bkm.Div(text=timestamp()), bkm.Div(text="HybRyd Dashboard Startup")],
    sizing_mode="stretch_both")
message_resolutions = bkl.column([bkm.Div(text=""), bkm.Div(text="")])
messages_page = bkm.Panel(title="System Messages",
                          child=bkl.row([message_buffer, message_resolutions])
                          )