from fastapi import FastAPI, File, Form, UploadFile, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, EmailStr
import json
from typing import Annotated, Optional
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


def parse_data(params: Annotated[str | None, Form()] = None):
    try:
        if params is None:
            return {}
        return json.loads(params)
    except Exception as e:
        raise HTTPException(
            detail=jsonable_encoder(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class Params(BaseModel):
    params: dict[str, str] | None


@app.post("/send")
async def send_email(
    to: Annotated[EmailStr | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
    mssg: Annotated[str | None, Form()] = None,
    html: Annotated[bool, Form()] = True,
    sender: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File(...)] = None,
    file_name: Annotated[str | None, Form()] = None,
    params: Annotated[dict[str, str], Depends(parse_data)] = {},
):
    email = locals()

    if file is not None:
        # TODO: corregir esto. es un fix para solo un archivo
        fname = file_name if file_name is not None else file.filename
        attach = (fname, BytesIO(await file.read()))
        del file
    else:
        attach = None

    send(
        email=to,
        subject=subject,
        mssg_content=mssg,
        html=html,
        sender=Sender(sender),
        files=attach,
        fields=params,
    )
    # logger.info(email)
    return email
