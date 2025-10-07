from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, EmailStr

from typing import Annotated, Callable
from send_emails import send, Sender

import logging
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)


app = FastAPI()


class EmailContent(BaseModel):
    to: EmailStr | None = None
    subject: str | None = None
    mssg: str | Callable | None = None
    html: bool = True
    sender: str | None = None
    giftcard: Annotated[UploadFile | None, File(...)] = None


@app.post("/send")
async def send_email(
    email: Annotated[EmailContent, Form(...)],
):
    if email.giftcard is not None:
        # TODO: corregir esto. es un fix para solo un archivo
        attach = (email.giftcard.filename, BytesIO(await email.giftcard.read()))
        del email.giftcard
    else:
        attach = None

    send(
        email=email.to,
        subject=email.subject,
        mssg_content=email.mssg,
        html=email.html,
        sender=Sender(email.sender),
        files=attach,
    )
    logger.info(email)
    return email
