# External libraries
from time import sleep

from .gmail import GoogleAPIService
from ..utils import validators as validators
from ..utils.tracking import add_pixel

from .message import Message
from .service import EmailService

import email.message
from pydantic import (
    Field,
    validate_call,
    NameEmail,
    EmailStr,
    InstanceOf,
    SkipValidation,
    ConfigDict,
)

import warnings
from ..settings import Settings
from ..db.db_protocol import DBProtocol
from ..db.records import PgRecordsDBInterface, Record, add_record


# TODO: Change to Pydantic BaseModel and remove @validate_call
class Sender:
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        from_address: NameEmail,
        *,
        service: SkipValidation[EmailService] | None = None,
        config: Settings = Field(default_factory=Settings),
        records_db: SkipValidation[DBProtocol | None] = Field(
            default_factory=PgRecordsDBInterface
        ),
        add=False,
    ):
        self._config = config

        self._from = from_address
        self._add_new = add
        self._max_emails = self._config.sender.max_emails
        self._service = service
        self._db = records_db
        self._i = 0

    @property
    def service(self):
        if not self._service:
            self._service = GoogleAPIService.from_db(
                account=self._from.email,
                add=self._add_new,
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
        record = None
        if self._db._engine is not None:
            record = Record(
                from_=self._from.email, to=to, content=message.mroot.as_string()
            )
            with self._db.get_session() as session:
                add_record(record, session)

                print(record.mid)
                add_pixel(message, mid=record.mid)

        send_message = (
            self.service.service.users()
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
