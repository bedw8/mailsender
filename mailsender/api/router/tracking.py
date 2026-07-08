from typing import Annotated
from fastapi import APIRouter, Query, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator

from mailsender.db.records import (
    Track,
    PgRecordsDBInterface,
    add_track,
    list_trackings,
    TrackingQueryParams,
)
from mailsender.api.router.auth import token_dep
from sqlmodel import Session


def get_session():
    db = PgRecordsDBInterface()
    with db.get_session() as session:
        yield session


router = APIRouter()

PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
    b"\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00"
    b"\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)

headers = {
    # intenta minimizar caché (no siempre lo ressendpeta Gmail)
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@router.get(
    "/tracking",
)
async def tracking(
    params: Annotated[TrackingQueryParams, Query()],
    session: Annotated[Session, Depends(get_session)],
    token: token_dep,
):
    t = list_trackings(params=params, session=session)

    return JSONResponse(t)


@router.get(
    "/pixel.gif",
    response_model=None,
)
async def send_email(
    mid: str,
    session: Annotated[Session, Depends(get_session)],
):
    track = Track(mid=mid)
    status_code = 200 if add_track(track, session) else 404

    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers=headers,
        status_code=status_code,
    )
