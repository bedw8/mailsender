from fastapi import FastAPI
import logging

from mailsender import Settings
from importlib import resources
from fastapi.staticfiles import StaticFiles

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
from .router import unsubs


static_path = resources.files("mailsender.api").joinpath("static")

app = FastAPI()

app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(auth.router)
app.include_router(send.router)
app.include_router(tracking.router)
app.include_router(unsubs.router, prefix="/ml")
