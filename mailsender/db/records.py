from typing import Annotated, Literal
from fastapi import Query
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, select, col, exists
from pydantic import EmailStr
from ..settings import config
from datetime import datetime
from smalluuid import SmallUUID
from sqlalchemy.orm import load_only, registry
from .db_protocol import DBProtocol
from dataclasses import dataclass
from ..lib.errors import (
    AlreadyUnsubscribed,
    CampaignAlreadyExists,
    CampaignNotFound,
    RecordColumnNotFound,
    RecordNotFound,
    NotUnsubscribed,
)

# For multiple DB management
class Base(SQLModel, registry=registry()):
    pass


@dataclass
class PgRecordsDBInterface(DBProtocol):
    db_path: str = config.db.model_dump().get("records_db")
    _engine = None

    def __post_init__(self):
        self.create_engine()
        if self._engine is not None:
            self.create_db_and_tables()

    def create_engine(self):
        self._engine = (
            None if self.db_path is None else create_engine(f"{self.db_path}")
        )

    def create_db_and_tables(self):
        Base.metadata.create_all(self._engine)

    def get_session(self):
        return Session(self._engine)

class Campaign(Base, table=True):
    __tablename__ = "campaigns"
    id: int | None = Field(default=None, primary_key=True)
    address: EmailStr | None = None
    name: str = Field(index=True,unique=True)
    unsubs: list["UnsubscribedEmail"] = Relationship(back_populates="campaign")
    records: list["Record"] = Relationship( back_populates="campaign")

class Record(Base, table=True):
    __tablename__ = "records"
    mid: str = Field(default_factory=lambda: SmallUUID().small, primary_key=True)
    from_: EmailStr = Field(alias="from")
    token: str 
    to: EmailStr
    subject: str
    content: str = ""
    sent_at: datetime = Field(default_factory=datetime.now)
    campaign_id: int | None = Field(foreign_key="campaigns.id")
    campaign: Campaign | None = Relationship(back_populates="records")
    trackings: list["Track"] = Relationship()


class Track(Base, table=True):
    __tablename__ = "tracking"
    id: int | None = Field(default=None, primary_key=True)
    mid: str = Field(index=True, foreign_key="records.mid")
    record: Record = Relationship(back_populates="trackings")
    opened_at: datetime = Field(default_factory=datetime.now)


class UnsubscribedEmail(Base, table=True):
    __tablename__ = "unsubscribed"
    id: int | None = Field(default=None,primary_key=True)
    email: EmailStr 
    date: datetime = Field(default_factory=datetime.now)
    comment: str | None = None
    campaign_id: int | None = Field(foreign_key="campaigns.id")
    campaign: Campaign | None = Relationship(back_populates="unsubs")


def list_records(session: Session, 
                 q: list[str] = [],
                 to: list[str] = [],
                 from_: list[str] = [],
                 limit: int | None = None,
                 campaign: int | None = None,
                 subject: str | None = None,
     ):
    stmt = select(Record)
    for col in q:
        try:
            stmt = stmt.options(load_only(getattr(Record,col)))
        except AttributeError as e:
            raise RecordColumnNotFound(col)
    if to:
        stmt = stmt.where(Record.to.in_(to))
    if from_:
        stmt = stmt.where(Record.from_.in_(from_))
    if limit:
        stmt = stmt.limit(limit)
    if campaign:
        stmt = stmt.where(Record.campaign_id == campaign)
    if subject:
        stmt = stmt.where(Record.subject == subject)
    stmt = stmt.order_by(Record.sent_at.desc())
    recs = session.exec(stmt).all()
    return recs

def add_record(record: Record, session: Session):
    session.add(record)
    session.commit()
    session.refresh(record)


def get_record(mid: str, session: Session):
    r = session.get(Record, mid)
    if r is None:
        raise RecordNotFound(mid)
    return r


def add_track(track: Track, session: Session):
    if session.get(Record, track.mid) is None:
        return False

    session.add(track)
    session.commit()
    return True

def unsubscribe(email: EmailStr, campaign: int | None, session: Session):
    unsub = list_unsubs(email, campaign, session=session)
    if unsub:
        unsub = unsub[0]
        camp_name = None if unsub.campaign is None else unsub.campaign.name 
        raise AlreadyUnsubscribed(email, camp_name)

    camp = get_campaign(campaign, session=session) 
    email = UnsubscribedEmail(email=email, campaign_id=None if camp is None else camp.id)

    session.add(email)
    session.commit()
    session.refresh(email)

    return email.email


def unsubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    camp_id = record.campaign_id

    return unsubscribe(record.to, camp_id, session)


def resubscribe(email: UnsubscribedEmail, session: Session):
    session.delete(email)
    session.commit()

    return email.email


def get_unsub(email: EmailStr, 
                    campaign: int | Campaign | None,
                    session: Session
                    ):
    
    stmt = select(UnsubscribedEmail).where(UnsubscribedEmail.email == email)
    
    if isinstance(campaign, Campaign):
        camp = campaign 
    elif isinstance(campaign, int):
        camp = session.get(Campaign, campaign)
    else:
        raise CampaignNotFound(id=id)
    
    if camp:
        stmt = stmt.where(UnsubscribedEmail.campaign == camp)

    unsub = session.exec(stmt).all()
    return unsub


def resubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    email = list_unsubs(record.to, record.campaign_id, session=session)
    if email:
        email = email[0]
    else:
        raise NotUnsubscribed(record.to, record.campaign.name)

    return resubscribe(email, session)


def add_comment(email: UnsubscribedEmail, comment: str, session: Session):
    email.comment = comment
    session.add(email)
    session.commit()


def add_comment_from_record(record: Record | str, comment: str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    email = get_unsubscribed(email=record.to, 
                             campaign=record.campaign_id,
                             session=session)
    add_comment(email, comment, session)



def new_campaign(camp: Campaign, session: Session):
    exists = get_campaign(campaign=None, name=camp.name, session=session)
    if exists:
        raise CampaignAlreadyExists(camp.name)
    
    session.add(camp)
    session.commit()
    session.refresh(camp)

    return camp

def del_campaign(camp: Campaign, session: Session):
    session.delete(camp)
    session.commit()

def campaign_exists(id: int, session: Session):
    # stmt = select(Campaign).where(Campaign.id==id).exists()
    stmt = select(exists(Campaign)).where(Campaign.id==id)
    if x:=session.exec(stmt).first():
        return x
    raise CampaignNotFound(id=id)

def get_campaign(campaign: int | None, 
                 name: str | None = None,
                 *,
                 session: Session,
                 ):
    if name:
        return session.exec(select(Campaign.name == name)).first()
    if campaign:
        return session.get(Campaign, campaign)

def list_campaigns(address: EmailStr | None | Literal["none"] == None, session: Session):
    stmt = select(Campaign)
    
    if address == "none":
        stmt = stmt.where(Campaign.address.is_(None))
    elif address:
        stmt = stmt.where(Campaign.address == address, Campaign.address.is_(None))

    camps = session.exec(stmt).all()
    return camps

def list_unsubs(email: EmailStr | None = None, camp_id: int | list[int] | None = None, *,session: Session):
    stmt = select(UnsubscribedEmail)
    if isinstance(camp_id, int):
        camp_id = [camp_id]

    if camp_id:
        for id in camp_id:
            campaign_exists(id,session)

        stmt = stmt.where(col(UnsubscribedEmail.campaign_id).in_(camp_id))
    
    if email:
        stmt = stmt.where(UnsubscribedEmail.email == email)

    unsubs = session.exec(stmt).all()

    return unsubs

def list_trackings(sender: EmailStr | None = None, subject: str | None = None, campaign_id: int | None = None,*, session: Session):

    stmt = select(Track)
    ## select(Track.id, Track.mid, Record.from_, Record.to, Record.subject , Track.opened_at).join()
    if sender:
        stmt = stmt.where(Track.record.has(Record.from_ == sender))
    if subject:
        stmt = stmt.where(Track.record.has(Record.subject == subject))
    if campaign_id:
        stmt = stmt.where(Track.record.has(Record.campaign_id == campaign_id))

    trackings = session.exec(stmt).all()

    return trackings
    


    

