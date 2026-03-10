from typing import Annotated
from fastapi import APIRouter, Response, Depends

from mailsender.db.records import get_session, Session, Track

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
    "/pixel.gif",
    response_model=None,
)
async def send_email(
    mid: str,
    session: Annotated[Session, Depends(get_session)],
):
    track = Track(mid=mid)
    session.add(track)
    session.commit()

    return Response(content=PIXEL_GIF, media_type="image/gif", headers=headers)
