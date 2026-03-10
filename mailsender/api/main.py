from fastapi import FastAPI
import logging

from mailsender import Settings

config = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)

from .router import auth
from .router import send
from .router import tracking


app = FastAPI()


app.include_router(auth.router)
app.include_router(send.router)
app.include_router(tracking.router)
