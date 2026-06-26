from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Response, Depends, status

from mailsender.api.router.auth import token_dep
from mailsender.db.records import Record, Track, PgRecordsDBInterface, add_track, list_records
from sqlmodel import Session

from mailsender.lib.errors import RecordColumnNotFound
from pydantic import BaseModel

def get_session():
    db = PgRecordsDBInterface()
    with db.get_session() as session:
        yield session


router = APIRouter()

class RecordQueryParams(BaseModel):
    q: list[str] = []
    to: list[str] = []
    from_: Annotated[list[str], Query(alias='from')] = []
    limit: int | None = 10
    campaign: int | None = None
    subject: str | None = None


@router.get("/records", 
            # response_model=list[Record],
            # response_model_exclude_unset=True
)
async def records(
    session: Annotated[Session, Depends(get_session)],
    params: Annotated[RecordQueryParams, Query()],
    *,
    token: token_dep,
):
    try:
        recs = list_records(session,**params.model_dump())
        return recs
    except RecordColumnNotFound as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

