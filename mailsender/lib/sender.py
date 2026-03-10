# External libraries
from time import sleep

from .gmail import get_gmail_service, GoogleAPIService
from ..utils import validators as validators
from ..utils.tracking import add_pixel

from .message import Message
from .service import EmailService

import email.message
from pydantic import validate_call, NameEmail, EmailStr, InstanceOf

import warnings

from ..settings import config, Settings

if config.db.records_db is not None:
    from ..db.records import create_db_and_tables, Session, engine, Record

    create_db_and_tables()


class Sender:
    @validate_call
    def __init__(
        self,
        from_address: NameEmail,
        *,
        service: EmailService | None = None,
        config: Settings = Settings(),
    ):
        self._config = config

        self._from = from_address
        self._max_emails = self.config.sender.max_emails
        self._service = service
        self._i = 0

    @property
    def service(self):
        if not self._service:
            self._service = GoogleAPIService.from_db(
                account=self._from.email,
                add_account=False,
                config=self._config.gmail,
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
