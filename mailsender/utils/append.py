import re
from ..lib.message import Message
from base64 import b64decode, b64encode

RE_BASE64 = "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"


def likeBase64(s: str) -> bool:
    return False if s is None or not re.search(RE_BASE64, s) else True


def append(mssg: Message, extra: str):
    text = mssg.mroot.get_payload()[0]
    text_data = text.get_payload()

    text_data = b64decode(text_data).decode()
    final = text_data + extra
    final = b64encode(final.encode()).decode()

    text.set_payload(final)
