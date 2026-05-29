# External libraries
from time import sleep

from mailsender.db.token import SQLiteTokenDBInterface

from .gmail import GoogleAPIService
from ..utils import validators as validators
from ..utils.tracking import add_pixel
from ..utils.mailinglist import add_unsubs_footer, gen_us_link
from ..utils.replace import replace

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
from ..db.records import Campaign, PgRecordsDBInterface, Record, add_record, get_campaign, is_unsubscribed
from .errors import UnsubscribedAddress


# TODO: Change to Pydantic BaseModel and remove @validate_call
class Sender:
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        from_address: NameEmail,
        account: EmailStr | None = None,
        token: str | None = None,
        verify_token: bool = False,
        *,
        service: SkipValidation[EmailService] | None = None,
        config: Settings = Field(default_factory=Settings),
        records_db: SkipValidation[DBProtocol | None] = Field(
            default_factory=PgRecordsDBInterface
        ),
        token_db: SkipValidation[DBProtocol | None] = Field(
            default_factory=SQLiteTokenDBInterface
        ),
        add:bool =False,
    ):
        self._config = config

        self._token = token
        self._token_db = token_db

        if verify_token and token_db:
            self._token_db.verify_token(self._token) # if invalid, raise exception

        self._from = from_address
        self._account = self._from.email if not account else account
        self._add_new = add
        self._max_emails = self._config.sender.max_emails

        self._db = records_db
        self._i = 0

        if service:
            self._service = service
        else:
            self._service = GoogleAPIService.from_db(
                account=self._account,
                add=self._add_new,
                config=self._config.gmail,
            )

    @property
    def service(self):
        return self._service

    @validate_call
    def send(
        self,
        to: EmailStr,
        message: InstanceOf[Message],
        us_footer: bool = True,
        us_link: bool = False,
        tracking: bool = True,
        campaign: int | Campaign | None = None,
    ):
        message = message # 
        message.sender = self._from
        message.to = to

        record = None
        if self._db._engine is not None:
            with self._db.get_session() as session:
                campaign = get_campaign(campaign=campaign,
                                    address=self._from.email,
                                    session=session)
                
                if len(is_unsubscribed(email=to,
                                   campaign=campaign,
                                   session=session))>0:
                    raise UnsubscribedAddress(email=str(to),campaign_name=campaign.name)

                # Create record before send message to add tracking pixel into the message content
                record = Record(
                    from_=self._from.email, 
                    to=to, 
                    subject=message.mroot["Subject"],
                    content=message.mroot.as_string(),
                    campaign=campaign,
                )

        # Create record before send message to add tracking pixel into the message content
            record = Record(
                from_=self._from.email,
                to=to,
                subject=message.mroot['Subject'],
                # content=message.mroot.as_string(),
                token=self._token,
            )

            if tracking:
                add_pixel(message, mid=record.mid)
            if us_footer:
                add_unsubs_footer(message, mid=record.mid)
            if us_link:
                _us_link = gen_us_link(mid=record.mid)
                replace(message,key="us_link",value=_us_link)


        send_message = (
            self.service.service.users()
            .messages()
            .send(userId="me", body=message.to_bytes())
            .execute()
        )

        if "SENT" not in send_message["labelIds"]:
            warnings.warn(f"Email not sent to {email}")
        elif (self._db._engine is not None) and (record is not None):
            with self._db.get_session() as session:
                add_record(record, session)

        if (self._i + 1) % self._max_emails == 0:
            warnings.warn(f"Pausing for 1 second after sending {self._i + 1} emails")
            sleep(1)

        self._i += 1

        if record:
            return record
