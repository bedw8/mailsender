from ..settings import config
from ..lib.message import Message
from .append import append


def add_pixel(mssg: Message, mid: str, trackingURL: str = config.trackingURL):
    if "://" not in trackingURL:
        trackingURL = "http://" + trackingURL

    pixel = f'<img src="{trackingURL}/pixel.gif?mid={mid}" width="1" height="1" style="display:none;" alt="">'

    append(mssg, pixel)
