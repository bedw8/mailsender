from sqlmodel import SQLModel, Field, create_engine, Session
from pydantic import EmailStr
from mailsender.config import cfg as config
from datetime import datetime
from smalluuid import SmallUUID
from contextlib import contextmanager
from sqlalchemy.orm import registry

db_path = config.db.records_db
engine = create_engine(f"{db_path}")


# For multiple DB management
class Base(SQLModel, registry=registry()):
    pass


def create_db_and_tables():
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


class Record(Base, table=True):
    __tablename__ = "records"
    mid: str = Field(default_factory=lambda: SmallUUID().small, primary_key=True)
    from_: EmailStr = Field(alias="from")
    to: EmailStr
    content: str
    sent_at: datetime = Field(default_factory=datetime.now)


class Track(Base, table=True):
    __tablename__ = "tracking"
    mid: str = Field(primary_key=True)
    opened_at: datetime = Field(default_factory=datetime.now)
