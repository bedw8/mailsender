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
from mailsender.lib.errors import AccountNotFoundOnDB, UnsubscribedAddress

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
    db_account: Annotated[EmailStr | None, Form()] = None,
    to: Annotated[EmailStr | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
    mssg: Annotated[str | None, Form()] = None,
    html: Annotated[bool, Form()] = True,
    image: list[UploadFile]| None = None,
    file: list[UploadFile] | None = None,
    # file_name: Annotated[str | None, Form()] = None,
    fields: Annotated[dict[str, str], Depends(parse_data)] = {},
):
    email = locals()

    if file is not None and len(file)>0:
        attach = []
        for f in file:
            # TODO: corregir esto. es un fix para solo un archivo
            # fname = file_name if file_name is not None else f.filename
            attach.append( (f.filename, BytesIO(await f.read())) )
            # del file
    else:
        attach = None

    if image and len(image)>0:
        i_attach = []
        for i in image:
            i_attach.append( (i.filename, BytesIO(await i.read())) )
    else:
        i_attach = None

    try:
        sender = Sender(from_address=sender,db_account=db_account)
    except AccountNotFoundOnDB as e:
        raise HTTPException(status_code=404, detail=str(e))

    mssg = Message(
        subject=subject,
        message=mssg,
        img=i_attach,
        files=attach,
        html=html,
        fields=fields,
    )

    try:
        record = sender.send(to, mssg)
        email["mid"] = record.mid
    except UnsubscribedAddress as e:
        raise HTTPException(status_code=409, detail=str(e))

    del email['mssg'] 
    return email
