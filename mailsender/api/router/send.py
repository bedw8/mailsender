from typing import Annotated
from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    status,
    File,
    UploadFile,
    Depends,
)
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, NameEmail

from io import BytesIO

from mailsender import Sender, Message
import json
from ..main import logger
from mailsender.lib.errors import AccountNotFoundOnDB

router = APIRouter()


# fix for dict input on form-encoded data
def parse_data(fields: Annotated[str | None, Form()] = None):
    try:
        if fields is None:
            return {}
        return json.loads(fields)
    except Exception as e:
        raise HTTPException(
            detail=jsonable_encoder(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@router.post("/send")
async def send_email(
    sender: Annotated[NameEmail | None, Form()] = None,
    to: Annotated[EmailStr | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
    mssg: Annotated[str | None, Form()] = None,
    html: Annotated[bool, Form()] = True,
    image: Annotated[UploadFile | None, File(...)] = None,
    file: Annotated[UploadFile | None, File(...)] = None,
    file_name: Annotated[str | None, Form()] = None,
    fields: Annotated[dict[str, str], Depends(parse_data)] = {},
):
    email = locals()

    if file is not None:
        # TODO: corregir esto. es un fix para solo un archivo
        fname = file_name if file_name is not None else file.filename
        attach = (fname, BytesIO(await file.read()))
        del file
    else:
        attach = None

    try:
        sender = Sender(sender)
    except AccountNotFoundOnDB as e:
        return HTTPException(status_code=400, detail=str(e))

    mssg = Message(
        subject=subject,
        message=mssg,
        img=image,
        html=html,
        fields=fields,
    )

    sender.send(to, mssg)

    logger.info(email)
    return email
