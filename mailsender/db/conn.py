from sqlmodel import SQLModel, Field, create_engine, Session
from sqlalchemy.orm import registry
from pydantic import EmailStr
import uuid
from mailsender.config import cfg as config
from contextlib import contextmanager

connect_args = {"check_same_thread": False}
db_path = config.config_dir / config.db.name
engine = create_engine(f"sqlite:///{db_path}", connect_args=connect_args)


class Base(SQLModel, registry=registry()):
    pass


def create_db_and_tables():
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


class Account(Base, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(index=True)
    creds: str
