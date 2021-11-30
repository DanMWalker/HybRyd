def timestamp():
    return datetime.now().strftime("%Y-%m-%d@%H:%M:%S")



def push_message(msg, resolver=None):
    print(msg)
    ts_element = bkm.Div(text=timestamp())
    msg_element = bkm.Div(text=msg)
    message_buffer.children += [ts_element, msg_element]
    message_resolutions.children += [bkm.Div(text="")]
    if resolver is None:
        message_resolutions.children += [bkm.Div(text="")]
    else:
        message_resolutions.children += [resolver]
    if len(message_buffer.children) > app_config["retained_messages"]:
        message_buffer.children = message_buffer.children[-app_config["retained_messages"]:]
        message_resolutions.children = message_resolutions.children[-app_config["retained_messages"]:]

    notifications.update(text="New System Message(s)")