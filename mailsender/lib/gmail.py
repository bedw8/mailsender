# External modules
from pathlib import Path
from pydantic import (
    FilePath,
    validate_call,
    Json,
    BeforeValidator,
    EmailStr,
    InstanceOf,
)

from typing import Any, Annotated, ContextManager
import googleapiclient.discovery

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# import .utils.validators as validators
from ..utils import validators
from ..config import cfg as config
from ..db.conn import Session, get_session, Account, create_db_and_tables
from sqlmodel import select
import json

create_db_and_tables()


@validate_call
def add_account(
    scopes: Annotated[list[str], BeforeValidator(validators.ensure_list)],
    credentials: FilePath = config.credentials_file,
    token_file: Path | None = None,
    account: EmailStr | None = None,
    port: int = 0,
):
    flow = InstalledAppFlow.from_client_secrets_file(credentials, scopes)
    creds = flow.run_local_server(port=port)

    # Save the credentials for the next run
    save_token(token_data=creds.to_json(), to_file=token_file, to_db=account)

    return creds


@validate_call
def save_token(
    token_data: str,
    to_file: Path | None = None,
    to_db: str | None = None,
    db_session: InstanceOf[ContextManager[Session]] = get_session,
):
    with db_session() as session:
        if to_file:
            with to_file.open(mode="w") as token_file:
                token_file.write(token_data)
        elif to_db:
            email = to_db

            # check existing entry in db
            stmt = select(Account).where(Account.email == email)
            acc = session.exec(stmt).first()
            if acc:
                acc.creds = token_data
            else:
                acc = Account(email=email, creds=token_data)

            session.add(acc)
            session.commit()


@validate_call
def load_credentials(
    scopes: Annotated[list[str], BeforeValidator(validators.ensure_list)],
    credentials: FilePath = config.credentials_file,
    port: int = 0,
    token_file: Path | None = None,
    account: EmailStr | None = None,
    token_data: Json[Any] | None = None,
    add_account: bool = False,
    db_session: InstanceOf[ContextManager[Session]] = get_session,
):
    creds = None

    if token_file:
        assert token_file.is_file()
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    elif token_data:
        creds = Credentials.from_authorized_user_info(token_data)
    elif account:
        with db_session() as session:
            stmt = select(Account.creds).where(Account.email == account)
            token_data = json.loads(session.exec(stmt).first())

            if token_data:
                creds = Credentials.from_authorized_user_info(token_data)
            else:
                creds = None

    if creds is None:
        if add_account:
            creds = add_account(
                scopes=scopes,
                credentials=credentials,
                token_file=token_file,
                account=account,
                port=port,
            )
        else:
            raise Exception("Account not logged in")

    # If there are no (valid) credentials available, let the user log in.
    elif not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_token(token_data=creds.to_json(), to_file=token_file, to_db=account)
    return creds


@validate_call
def get_gmail_service(
    scopes: Annotated[list[str], BeforeValidator(validators.ensure_list)],
    credentials: FilePath = config.credentials_file,
    port: int = 0,
    token_file: FilePath | None = None,
    account: EmailStr | None = None,
    add_account: bool = False,
) -> googleapiclient.discovery:
    # Saving arguments
    args = locals()
    # Use the local and secret
    creds = load_credentials(**args)
    service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)
    return service


# TODO: Implement a Source class and move token_file and DB to that system
