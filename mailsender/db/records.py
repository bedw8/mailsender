from sqlmodel import SQLModel, Field, create_engine, Session
from pydantic import EmailStr
from ..settings import config
from datetime import datetime
from smalluuid import SmallUUID
from sqlalchemy.orm import registry
from .db_protocol import DBProtocol
from dataclasses import dataclass
from ..lib.errors import AlreadyUnsubsribed


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
    content: str
    sent_at: datetime = Field(default_factory=datetime.now)


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


def add_record(record: Record, session: Session):
    session.add(record)
    session.commit()
    session.refresh(record)


def add_track(track: Track, session: Session):
    # if session.get(Track, track.mid) is not None:
    #     return

    session.add(track)
    session.commit()


def unsubscribe(email: UnsubscribedEmail, session: Session):
    if session.get(UnsubscribedEmail, email.email):
        raise AlreadyUnsubsribed(email.email)

    session.add(email)
    session.commit()
    session.refresh(email)


def resubscribe(email: UnsubscribedEmail, session: Session):
    session.delete(email)
    session.commit()
