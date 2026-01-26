# External libraries
from pathlib import Path
from time import sleep

from .lib import get_gmail_service
from .utils import validators as validators

from .message import Message

import email.message
from pydantic import (
    validate_call,
    NameEmail,
    EmailStr,
    FilePath,
)

import warnings

from .config import config


class Sender:
    @validate_call
    def __init__(
        self, from_address: NameEmail, credentials: FilePath = config.credentials_path
    ):
        self._from = from_address
        self._scopes = config.sender.scopes
        self.credentials = Path(credentials)
        self._port = config.sender.port
        self._max_emails = config.sender.max_emails
        self._service = None
        self._i = 0

    @property
    def service(self):
        if not self._service:
            self._service = get_gmail_service(
                scopes=self._scopes, credentials=self.credentials, port=self._port
            )
        return self._service

    @validate_call
    def send(self, to: EmailStr, message: Message):
        message.sender = self._from

        send_message = (
            self.service.users()
            .messages()
            .send(userId="me", body=message.to_bytes())
            .execute()
        )
        if "SENT" not in send_message["labelIds"]:
            warnings.warn(f"Email not sent to {email}")
        if (self._i + 1) % self._max_emails == 0:
            warnings.warn(f"Pausing for 1 second after sending {self._i + 1} emails")
            sleep(1)
        self._i += 1
