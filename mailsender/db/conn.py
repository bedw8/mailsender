from sqlmodel import SQLModel, Field, create_engine, Session
from pydantic import EmailStr
import uuid
from mailsender.config import cfg as config

connect_args = {"check_same_thread": False}
db_path = config.config_dir / config.db.name
engine = create_engine(f"sqlite:///{db_path}", connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


class Account(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(index=True)
    creds: str
