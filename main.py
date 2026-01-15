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
    file: Annotated[UploadFile | None, File(...)] = None
    file_name: str | None = None


@app.post("/send")
async def send_email(
    email: Annotated[EmailContent, Form(...)],
):
    if email.file is not None:
        # TODO: corregir esto. es un fix para solo un archivo
        fname = email.file_name if email.file_name is not None else email.file.filename
        attach = (fname, BytesIO(await email.file.read()))
        del email.file
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
