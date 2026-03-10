# External modules
from pathlib import Path
from pydantic import (
    Field,
    FilePath,
    validate_call,
    BeforeValidator,
    EmailStr,
    SkipValidation,
    ConfigDict,
)

from typing import Annotated
import googleapiclient.discovery

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# import .utils.validators as validators
from ..utils import validators
from ..settings import GmailSettings
from ..db.accounts import SQLiteAccountsDBInterface, Account, save_token_to_db
from ..db.db_protocol import DBProtocol
from .message import Message
from .errors import AccountNotFoundOnDB
from sqlmodel import select
from .service import EmailService
import json
import warnings


# @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
# def load_credentials(
#     scopes: Annotated[list[str], BeforeValidator(validators.ensure_list)] | None = None,
#     credentials: FilePath | None = None,
#     port: int = 0,
#     token_file: Path | None = None,
#     account: EmailStr | None = None,
#     token_data: Json[Any] | None = None,
#     add_account: bool = False,
#     db: SkipValidation[DBProtocol] = default_db_interface,
#     config: Settings = Field(default_factory=Settings),
# ):
#     # this is credentials file
#     credentials = credentials if credentials is not None else config.credentials_file
#     scopes = scopes if scopes is not None else config.gmail.scopes
#
#     # this is credentials object, not credentials file
#     creds = None
#
#     scopes = scopes if scopes is not None else config.gmail.scopes
#
#     if token_file:
#         assert token_file.is_file()
#         creds = Credentials.from_authorized_user_file(token_file, scopes)
#     elif token_data:
#         creds = Credentials.from_authorized_user_info(token_data)
#     elif account:
#         with db.get_session() as session:
#             stmt = select(Account.creds).where(Account.email == account)
#             token_data = json.loads(session.exec(stmt).first())
#             creds = Credentials.from_authorized_user_info(token_data)
#
#     if creds is None:
#         if add_account:
#             creds = add_account(
#                 scopes=scopes,
#                 credentials=credentials,
#                 token_file=token_file,
#                 account=account,
#                 port=port,
#                 config=config,
#             )
#         else:
#             raise Exception("Account not logged in")
#
#     # If there are no (valid) credentials available, let the user log in.
#     elif not creds.valid:
#         if creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#             save_token(token_data=creds.to_json(), to_file=token_file, to_db=account)
#     return creds


class GoogleAPIService(EmailService):
    _default_db_interface = SQLiteAccountsDBInterface()

    def __init__(
        self,
        credentials: Credentials | None = None,
        config: GmailSettings = GmailSettings(),
    ):
        self._config = config
        self._creds = credentials
        self._service = None

        if self._creds is not None:
            self._service = googleapiclient.discovery.build(
                "gmail", "v1", credentials=self._creds
            )

    def check_creds(self):
        # elif not creds.valid:
        #     if creds.expired and creds.refresh_token:
        #         creds.refresh(Request())
        #         save_token(token_data=creds.to_json(), to_file=token_file, to_db=account)
        pass

    @property
    def service(self):
        """The service property."""
        return self._service

    @service.setter
    def service(self, value):
        self._service = value

    @staticmethod
    def from_file(
        token_file: FilePath, scopes=None, config: GmailSettings = GmailSettings()
    ):
        gservice = GoogleAPIService(config)

        scopes = scopes if not None else gservice.config.scopes

        creds = Credentials.from_authorized_user_file(token_file, scopes)
        return GoogleAPIService(credentials=creds, config=config)

    @staticmethod
    def from_data(token_data: str):
        creds = Credentials.from_authorized_user_info(token_data)
        return GoogleAPIService(credentials=creds)

    @staticmethod
    def _from_db(
        account: EmailStr,
        db: SkipValidation[DBProtocol | None] = None,
    ):
        if db is None:
            db = GoogleAPIService._default_db_interface
        with db.get_session() as session:
            stmt = select(Account.creds).where(Account.email == account)
            token_str = session.exec(stmt).first()
            if not token_str:
                raise AccountNotFoundOnDB(account)
            token_data = json.loads(token_str)
            creds = Credentials.from_authorized_user_info(token_data)
            return GoogleAPIService(credentials=creds)

    @staticmethod
    def from_db(
        account: EmailStr,
        db: SkipValidation[DBProtocol | None] = None,
        add: bool = False,
        config: GmailSettings = GmailSettings(),
    ):
        if db is None:
            db = GoogleAPIService._default_db_interface

        serv = GoogleAPIService._from_db(account=account, db=db)
        if not serv and add:
            creds = add_account(
                scopes=config.scopes,
                credentials=config.credentials_file,
                account=account,
            )
            return GoogleAPIService(credentials=creds)
        return serv

    def send(
        self,
        to: EmailStr,
        message: Message,
    ):
        send_message = (
            self._service.users()
            .messages()
            .send(userId="me", body=message.to_bytes())
            .execute()
        )

        if "SENT" not in send_message["labelIds"]:
            warnings.warn(f"Email not sent to {to}")

        return send_message


# TODO: Implement a Source class and move token_file and DB to that system


# TODO: Move parameter to a single Model
@validate_call
def add_account(
    scopes: Annotated[list[str], BeforeValidator(validators.ensure_list)] | None = None,
    credentials: FilePath | None = None,
    token_file: Path | None = None,
    account: EmailStr | None = None,
    port: int | None = None,
    config: GmailSettings = Field(default_factory=GmailSettings),
):
    credentials = credentials if credentials is not None else config.credentials_file
    scopes = scopes if scopes is not None else config.scopes
    port = port if port is not None else config.port

    flow = InstalledAppFlow.from_client_secrets_file(credentials, scopes)
    creds = flow.run_local_server(port=port)

    # Save the credentials for the next run
    save_token(token_data=creds.to_json(), to_file=token_file, to_db=account)

    return creds


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def save_token(
    token_data: str,
    to_file: Path | None = None,
    to_db: str | None = None,
    db: SkipValidation[DBProtocol | None] = None,
):
    if db is None:
        db = GoogleAPIService._default_db_interface

    if to_file:
        with to_file.open(mode="w") as token_file:
            token_file.write(token_data)
    elif to_db:
        with db.get_session() as session:
            email = to_db

            save_token_to_db(token_data, email, session)
