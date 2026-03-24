from ..settings import config
from ..lib.message import Message
from .append import append

from jinja2 import Environment

footer = """<div></div><div style="margin-top: 10px; padding:16px; background-color:#f5f5f5; font-family:Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px; margin:0 auto; background-color:#ffffff; border-top:1px solid #e8e8e8;">
        <tr>
            <td align="center" style="padding:16px 20px;">
                <p style="margin:0; color:#777777; font-size:12px; line-height:18px;">
                    Si ya no quieres recibir estos correos, puedes
                    <a href="{{trackingURL}}/ml/unsubscribe?mid={{mid}}" style="color:#555555; text-decoration:underline; font-size:12px; line-height:18px;">
                        darte de baja aquí
                    </a>.
                </p>
            </td>
        </tr>
    </table>
</div>
"""

env = Environment()
template = env.from_string(footer)


def add_unsubs_footer(mssg: Message, mid: str, trackingURL: str = config.trackingURL):
    if "://" not in trackingURL:
        trackingURL = "http://" + trackingURL

    output = template.render(trackingURL=trackingURL, mid=mid)

    append(mssg, output)
