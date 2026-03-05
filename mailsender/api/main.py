import os
from fastapi import FastAPI, Depends
from mailsender.db.conn import Session, get_session
from typing import Annotated
import logging

os.environ.setdefault("RUNTIME", "uvicorn")

from .router import auth
from .router import send
from .router import tracking

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)


app = FastAPI()

SessionDep = Annotated[Session, Depends(get_session)]

app.include_router(auth.router)
app.include_router(send.router)
app.include_router(tracking.router)
