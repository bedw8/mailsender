from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy.orm import registry
from pydantic import EmailStr
import uuid
from ..settings import config
from .db_protocol import DBProtocol
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from mailsender.lib.errors import InvalidCredentials, TokenAlreadyExists, TokenNotFound


class Base(SQLModel, registry=registry()):
    pass

class Token(Base, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)

@dataclass
class SQLiteTokenDBInterface(DBProtocol):
    db_path = config.config_dir / config.db.name
    connect_args = {"check_same_thread": False}
    s = None

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
        if self.s is not None:
            return self.s
        self.s = Session(self._engine)
        return self.s 

    def reset_session(self):
        self.s = None
        return self.get_session()

    def new_token(self, name: str):
        # check existing entry in db
        if self.get_token_by_name(name):
            raise TokenAlreadyExists(name)

        tok = Token(name=name)
        session = self.get_session()

        session.add(tok)
        session.commit()
        session.refresh(tok)
        return tok

    def get_token(self, token: str):
        # check existing entry in db
        session = self.get_session()
        try:
            tok = session.get(Token, UUID(token))
        except ValueError:
            tok = None
        return tok

    def get_token_by_name(self, name: str):
        # check existing entry in db
        session = self.get_session()
        stmt = select(Token).where(Token.name==name)
        tok = session.exec(stmt).first()
        return tok

    def rename_token(self, token: str, new_name: str):
        # check existing entry in db
        session = self.get_session()
        tok = self.get_token(token) 
        if tok is None:
            raise TokenNotFound(token)
        
        tok.name = new_name
        session.add(tok)
        session.commit()
        session.refresh(tok)
        return tok

    def revoke_token(self, token: str):
        # check existing entry in db
        session = self.get_session()
        tok = self.get_token(token) 
        if tok is None:
            raise TokenNotFound(token)

        session.delete(tok)
        session.commit()
        return tok

    def list_tokens(self):
        # check existing entry in db
        session = self.get_session()
        stmt = select(Token)
        toks = session.exec(stmt).all()
        return toks

    def validate_token(self, token: str) -> str | Token:
        key = config.db.token_key 
        if token == key:
            return token 
        tok = self.get_token(token)
        if tok:
            return tok
        raise InvalidCredentials()
