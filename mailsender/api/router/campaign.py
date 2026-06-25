from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Query, Response, Depends, status
from pydantic import EmailStr

from mailsender.api.router.auth import token_dep
from mailsender.db.records import Campaign, Record, Track, PgRecordsDBInterface, add_track, del_campaign, get_campaign, list_campaigns, list_records, new_campaign
from sqlmodel import Session

from mailsender.lib.errors import CampaignAlreadyExists


def get_session():
    db = PgRecordsDBInterface()
    with db.get_session() as session:
        yield session


router = APIRouter()

@router.get("/campaign")
async def campaigns(
    session: Annotated[Session, Depends(get_session)],
    address: Annotated[EmailStr | None , Query()] = None, 
    q: Annotated[list[str], Query()] = [],
    limit: int | None = None,
    *,
    token: token_dep,
):
    try:
        # recs = list_records(session,q,to,from_,limit)
        camps = list_campaigns(address, session)
        return camps 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/campaign")
async def delete_campaign(
    session: Annotated[Session, Depends(get_session)],
    id: Annotated[ int, Query()] 
    ):
    
    camp = get_campaign(id, session=session)
    if camp:
        del_campaign(camp, session) 
        return camp
    else:
        raise HTTPException(status_code=404,detail="that campaign does not exists.")

@router.post("/campaign")
async def create_campaign(
    session: Annotated[Session, Depends(get_session)],
    camp: Campaign,
    ):
    
    try:
        camp = new_campaign(camp, session)
        return camp     
    except CampaignAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    
