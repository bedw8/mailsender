from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy.orm import registry
from pydantic import EmailStr
import uuid
from ..settings import config
from .db_protocol import DBProtocol
from dataclasses import dataclass


class Base(SQLModel, registry=registry()):
    pass


@dataclass
class SQLiteAccountsDBInterface(DBProtocol):
    db_path = config.config_dir / config.db.name
    connect_args = {"check_same_thread": False}

    def __post_init__(self):
        self.create_engine()
        if self._engine is not None:
            self.create_db_and_tables()

    def create_engine(self):
        self._engine = create_engine(
            f"sqlite:///{self.db_path}", connect_args=self.connect_args
        )

    def create_db_and_tables(self):
        Base.metadata.create_all(self._engine)

    def get_session(self):
        return Session(self._engine)


class Account(Base, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(index=True)
    creds: str


def save_token_to_db(token_data: str, email: EmailStr, session: Session):
    # check existing entry in db
    stmt = select(Account).where(Account.email == email)
    acc = session.exec(stmt).first()
    if acc:
        acc.creds = token_data
    else:
        acc = Account(email=email, creds=token_data)

    session.add(acc)
    session.commit()
