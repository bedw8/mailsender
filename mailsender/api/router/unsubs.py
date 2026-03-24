from typing import Annotated
from fastapi import APIRouter, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from mailsender.lib.errors import (
    AlreadyUnsubscribed,
    RecordNotFound,
)

from mailsender.db.records import (
    PgRecordsDBInterface,
    unsubscribe_from_record,
    resubscribe_from_record,
    add_comment_from_record,
)
from sqlmodel import Session
from importlib import resources
from fastapi.templating import Jinja2Templates

static_path = resources.files("mailsender.api").joinpath("static")


def get_session():
    db = PgRecordsDBInterface()
    with db.get_session() as session:
        yield session


temps = [
    ("unsubs", "unsubscribe.html"),
    ("comment", "comments-sent.html"),
    ("resubs", "resubscribed.html"),
]

pages_html = {name: (static_path / temp).open("r").read() for name, temp in temps}
templates = Jinja2Templates(directory=static_path)

router = APIRouter()


@router.get("/unsubscribe", response_class=HTMLResponse)
async def remove_from_maillist(
    request: Request,
    mid: str,
    session: Annotated[Session, Depends(get_session)],
):
    try:
        unsubscribe_from_record(mid, session)
    except AlreadyUnsubscribed as e:
        return HTTPException(status_code=409, detail=str(e))
    except RecordNotFound as e:
        return HTTPException(status_code=404, detail=str(e))

    return templates.TemplateResponse(
        request=request, name="unsubscribe.html", context={"mid": mid}
    )


@router.get("/resubscribe")
async def add_to_maillist(
    request: Request,
    mid: str,
    session: Annotated[Session, Depends(get_session)],
):
    try:
        resubscribe_from_record(mid, session)
    except AlreadyUnsubscribed as e:
        return HTTPException(status_code=409, detail=str(e))
    except RecordNotFound as e:
        return HTTPException(status_code=404, detail=str(e))

    # TODO: crear otra pagina html
    return templates.TemplateResponse(request=request, name="resubscribed.html")


@router.post("/unsubscribe/comment")
async def add_comment(
    request: Request,
    mid: str,
    comments: Annotated[str, Form()],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        add_comment_from_record(mid, comments, session)
    except RecordNotFound as e:
        return HTTPException(status_code=404, detail=str(e))

    return templates.TemplateResponse(request=request, name="comments-sent.html")
