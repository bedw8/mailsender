from sqlmodel import SQLModel, Field, create_engine

from .config import config

connect_args = {"check_same_thread": False}
db_path = config.config_path / config.db.path
engine = create_engine(
    f"sqlite:///{config.config_pathconfig.db.path}", connect_args=connect_args
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    creds: str
