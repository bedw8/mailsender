from ..settings import config

from ..lib.message import Message


def add_pixel(mssg: Message, mid: str, trackingURL: str = config.trackingURL):
    if "://" not in trackingURL:
        trackingURL = "http://" + trackingURL

    pixel = f'<img src="{trackingURL}/pixel.gif?mid={mid}" width="1" height="1" style="display:none;" alt="">'

    text = mssg.mroot.get_payload()[0]
    text_data = text.get_payload()

    text.set_payload(text_data + pixel)
