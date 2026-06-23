from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler, http_exception_handler

from mailsender import Settings
from importlib import resources
from fastapi.staticfiles import StaticFiles

from mailsender.lib.errors import InvalidCredentials
from .middleware import AuthMissingTokenInvalidCredsError, HTTPSSchemeMiddleware

import logging

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
from .router import records 


logger.info(config)

static_path = resources.files("mailsender.api").joinpath("static")

app = FastAPI()


app.add_middleware(HTTPSSchemeMiddleware)
app.add_middleware(AuthMissingTokenInvalidCredsError)

app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(auth.router)
app.include_router(send.router)
app.include_router(tracking.router)
app.include_router(unsubs.router, prefix="/ml")
app.include_router(records.router)



