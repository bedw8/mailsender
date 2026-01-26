"""
Utility scripts for sending emails and other tasks
"""

# External modules
from pathlib import Path
from pydantic import FilePath, validate_call, Json, Field, BeforeValidator

from typing import Any, Annotated
import googleapiclient.discovery

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# import .utils.validators as validators
from .utils import validators


@validate_call
def load_credentials(
    scopes: str | list,
    credentials: str,
    port: int = 0,
    token: Annotated[
        Json[Any] | FilePath, Field(union_mode="left_to_right")
    ] = "token.json",
):
    creds = None

    if isinstance(token, Path):
        creds = Credentials.from_authorized_user_file(token, scopes)
        token_type = "file"
    else:
        creds = Credentials.from_client_secrets(token)
        token_type = "json"

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=port)
            # Save the credentials for the next run

        match token_type:
            case "file":
                with token.open(mode="w") as token_file:
                    token_file.write(creds.to_json())
            case "json":
                pass
                # TODO: save refresed token if json

    return creds


@validate_call
def get_gmail_service(
    scopes: Annotated[list[str], BeforeValidator(validators.str2list)],
    credentials: str,
    port: int = 0,
    token: Annotated[str | FilePath, Field(union_mode="left_to_right")] = "token.json",
) -> googleapiclient.discovery:
    """
    Using the googleapiclient.discovery.build method to get a service connection to the gmail API

    Parameters
    ----------
    credentials : str
        Path to the credentials.json file
    port : int, optional
        Port to use for the local server, by default 0

    Returns
    -------
    googleapiclient.discovery
        Service connection to the gmail API
    """
    # Saving arguments
    args = locals()
    # Use the local and secret
    creds = load_credentials(**args)
    service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)
    return service
