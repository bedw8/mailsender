from typing import Annotated
from fastapi import Query
from sqlmodel import SQLModel, Field, create_engine, Session, select
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


class Record(Base, table=True):
    __tablename__ = "records"
    mid: str = Field(default_factory=lambda: SmallUUID().small, primary_key=True)
    from_: EmailStr = Field(alias="from")
    to: EmailStr
    subject: str
    content: str = ""
    sent_at: datetime = Field(default_factory=datetime.now)
    token: str 


class Track(Base, table=True):
    __tablename__ = "tracking"
    id: int | None = Field(default=None, primary_key=True)
    mid: str = Field(index=True)
    opened_at: datetime = Field(default_factory=datetime.now)


class UnsubscribedEmail(Base, table=True):
    __tablename__ = "unsubscribed"
    email: EmailStr = Field(primary_key=True)
    date: datetime = Field(default_factory=datetime.now)
    comment: str | None = None


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

def unsubscribe(email: EmailStr, session: Session):
    if get_unsubscribed(email, session):
        raise AlreadyUnsubscribed(email)

    email = UnsubscribedEmail(email=email)
    session.add(email)
    session.commit()
    session.refresh(email)

    return email.email


def unsubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    return unsubscribe(record.to, session)


def resubscribe(email: UnsubscribedEmail, session: Session):
    session.delete(email)
    session.commit()

    return email.email


def get_unsubscribed(email: EmailStr, session: Session):
    return session.get(UnsubscribedEmail, email)


def resubscribe_from_record(record: Record | str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    email = get_unsubscribed(record.to, session)

    if not email:
        raise NotUnsubscribed(record.to)

    return resubscribe(email, session)


def add_comment(email: UnsubscribedEmail, comment: str, session: Session):
    email.comment = comment
    session.add(email)
    session.commit()


def add_comment_from_record(record: Record | str, comment: str, session: Session):
    if isinstance(record, str):
        record = get_record(record, session)

    email = get_unsubscribed(record.to, session)
    add_comment(email, comment, session)
