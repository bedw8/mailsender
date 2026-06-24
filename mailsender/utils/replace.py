import re
from ..lib.message import Message
from base64 import b64decode, b64encode

def replace(mssg: Message, key: str, value: str):
    text = mssg.mroot.get_payload()[0]
    text_data = text.get_payload()

    text_data = b64decode(text_data).decode()
    final = re.sub("{" + key + "}", value, text_data)

    final = b64encode(final.encode()).decode()
    text.set_payload(final)
