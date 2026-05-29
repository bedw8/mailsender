from typing import Annotated
from fastapi import Query
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, select, col
from pydantic import EmailStr
from ..settings import config
from datetime import datetime
from smalluuid import SmallUUID
from sqlalchemy.orm import load_only, registry
from .db_protocol import DBProtocol
from dataclasses import dataclass
from ..lib.errors import (
    AlreadyUnsubscribed,
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
    address: EmailStr 
    name: str
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
    email: EmailStr = Field(primary_key=True)
    date: datetime = Field(default_factory=datetime.now)
    comment: str | None = None
    campaign_id: int | None = Field(foreign_key="campaigns.id")
    campaign: Campaign | None = Relationship(back_populates="unsubs")

def list_records(session: Session, 
                 q: list[str] = [],
                 to: list[str] = [],
                 from_: list[str] = [],
                 limit: int | None = None
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

def unsubscribe(email: EmailStr, campaign: int | Campaign, session: Session):
    campaign = is_unsubscribed(email, campaign, session)
    if campaign == True:
        raise AlreadyUnsubscribed(email, campaign.name)

    email = UnsubscribedEmail(email=email, campaign_id=campaign.id)

    session.add(email)
    session.commit()
    session.refresh(email)

    return email.email


def unsubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    camp = record.campaign
    print(camp)

    return unsubscribe(record.to, camp, session)


def resubscribe(email: UnsubscribedEmail, session: Session):
    session.delete(email)
    session.commit()

    return email.email


def is_unsubscribed(email: EmailStr, 
                    campaign: int | Campaign | None,
                    session: Session
                    ):
    
    stmt = select(UnsubscribedEmail).where(UnsubscribedEmail.email == email)

    if isinstance(campaign, Campaign):
        camp = campaign 
    elif isinstance(campaign, int):
        camp = session.get(Campaign, campaign)
    
    if camp:
        stmt = stmt.where(UnsubscribedEmail.campaign == camp)

    unsub = session.exec(stmt).all()
    return unsub


def resubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    email = get_unsubscribed(record.to, record.campaign, session)

    if not email:
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
    session.add(camp)
    session.commit()
    session.refresh(camp)

    return camp

def del_campaign(camp: Campaign, session: Session):
    session.delete(camp)
    session.commit()

def get_campaign(campaign: int | Campaign | None = None, 
                 address: EmailStr | None = None, 
                 *,
                 session: Session,
                 ):

    if isinstance(campaign, Campaign):
        return campaign
    if isinstance(campaign, int):
        return session.get(Campaign, campaign)
    if not campaign:
        if not address:
            raise Exception('Debe ingresar address si campaign es None')
        
        stmt = select(Campaign)\
                .where(Campaign.address == address)\
                .where(Campaign.name == 'default')

        default =  session.exec(stmt).first()
        if not default:
            default = Campaign(address=address, name='default')
            session.add(default)
            session.commit()
            session.refresh(default)
        return default

def list_campaigns(address: EmailStr, session: Session):
    stmt = select(Campaign).where(Campaign.address == address)
    camps = session.exec(stmt).all()
    return camps

def list_unsubs(camp_id: int | list[int] | None = None, *,session: Session):
    stmt = select(UnsubscribedEmail)
    if isinstance(camp_id, int):
        camp_id = [camp_id]

    if camp_id:
        stmt = stmt.where(col(UnsubscribedEmail.campaign_id).in_(camp_id))

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
    


    

