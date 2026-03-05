# External libraries
from pathlib import Path
from time import sleep

from .gmail import get_gmail_service
from ..utils import validators as validators
from ..utils.tracking import add_pixel

from .message import Message

import email.message
from pydantic import validate_call, NameEmail, EmailStr, FilePath, InstanceOf

import warnings

from ..config import cfg as config

if config.db.records_db is not None:
    from ..db.records import create_db_and_tables, Session, engine, Record

    create_db_and_tables()


class Sender:
    @validate_call
    def __init__(
        self,
        from_address: NameEmail,
        credentials: FilePath = config.credentials_file,
        token_file: FilePath | None = None,
    ):
        self._from = from_address
        self._scopes = config.sender.scopes
        self.credentials = Path(credentials)
        self._port = config.sender.port
        self._max_emails = config.sender.max_emails
        self._service = None
        self._i = 0
        self._token_file = token_file

    @property
    def service(self):
        if not self._service:
            self._service = get_gmail_service(
                scopes=self._scopes,
                credentials=self.credentials,
                port=self._port,
                token_file=self._token_file,
                account=self._from.email,
                add_account=False,
            )
        return self._service

    @validate_call
    def send(
        self,
        to: EmailStr,
        message: InstanceOf[Message],
    ):
        message.sender = self._from
        message.to = to

        # Create record before send message to add tracking pixel into the message content
        if config.db.records_db is not None:
            record = Record(
                from_=self._from.email, to=to, content=message.mroot.as_string()
            )
            with Session(engine) as session:
                session.add(record)
                session.commit()
                session.refresh(record)
        else:
            record = None

        if record:
            print(record.mid)
            add_pixel(message, mid=record.mid)

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
