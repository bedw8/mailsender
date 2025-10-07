"""
Utility scripts for sending emails and other tasks
"""

# External modules
import os
from pathlib import Path
from pydantic import FilePath
import sys

# import cv2
from typing import Optional, Union, List
import numpy as np
import pandas as pd
import email.message
import googleapiclient.discovery
from base64 import urlsafe_b64encode
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def load_credentials(
    scopes: str | list,
    credentials: str,
    port: int = 0,
    tokenfile: Path | str = "token.json",
):
    creds = None

    if os.path.exists(tokenfile):
        creds = Credentials.from_authorized_user_file(tokenfile, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=port)
            # Save the credentials for the next run
        with open(tokenfile, "w") as token:
            token.write(creds.to_json())

    return creds


def get_gmail_service(
    scopes: str | list,
    credentials: str,
    port: int = 0,
    tokenfile: Path | str = "token.json",
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
    # Input checks
    scopes = str2list(scopes)
    assert isinstance(scopes, list), f"Scopes should be a list, not {type(scopes)}"
    assert Path(credentials).is_file(), f"Credentials file {credentials} does not exist"
    # Use the local and secret
    creds = load_credentials(**args)
    service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)
    return service


class Attachment:
    def __init__(self, files):
        self.files = str2list(files)

    def iter_files(self):
        for path in self.files:
            data, subtype = Attachment.get_data(path)
            yield data, subtype

    @staticmethod
    def get_data(file_path: str | Path, max_image_size: int = 1024):
        path = Path(file_path)

        subtype = path.suffix.strip(".")
        is_image = is_file_image(path)
        if is_image:
            data = image2bytes(path=path, max_size=max_image_size)
        else:
            with open(path, "rb") as fp:
                data = fp.read()

        return data, subtype


def create_message(
    message: str,
    email_from: str,
    email_to: str,
    subject: str,
    files: str | list[str] = [],
    max_image_size: int = 1024,
) -> email.message:
    """
    Edited by BE.
    ----------
    Use the email.message.EmailMessage class to create a message and return its raw base64 encoded version in a dictionary

    Parameters
    ----------
    message : str
        Message to send
    email_from : str
        Email address to send from
    email_to : str
        Email address to send to
    subject : str
        Subject line

    Returns
    -------
    dict
        Dictionary with the raw base64 encoded message
    """
    # Input checks
    assert isinstance(message, str), f"Message should be a string, not {type(message)}"
    assert isinstance(email_from, str), (
        f"Email_from should be a string, not {type(email_from)}"
    )
    assert isinstance(email_to, str), (
        f"Email_to should be a string, not {type(email_to)}"
    )
    assert isinstance(subject, str), f"Subject should be a string, not {type(subject)}"

    # Create the message
    msg = EmailMessage()
    msg.set_content(message)
    msg["To"] = email_to
    msg["From"] = email_from
    msg["Subject"] = subject
    # Add the attachments
    attchs = Attachment(files)
    for data, subtype in attchs.iter_files():
        msg.add_attachment(data, maintype="image", subtype=subtype)
    # Return the message
    return msg


def message2bytes(msg) -> dict:
    # Encode the message and save it in a dictionary
    encoded_msg = urlsafe_b64encode(msg.as_bytes()).decode()
    di_msg = {"raw": encoded_msg}
    return di_msg


def str2list(string: str | list) -> list:
    """
    Check if a string is a list, if not, make it a list

    Parameters
    ----------
    string : str or list
        String to check

    Returns
    -------
    list
        List of the string
    """
    if isinstance(string, str):
        return [string]
    else:
        return string


def press_Yn_to_continue():
    """
    Force the user to press Y to continue, n to break, or repeat options
    """
    inp = input("Press Y to continue, or n to break\n")
    print("You pressed", inp)
    while (inp != "Y") and (inp != "n"):  # Loop until it is a blank line
        print("You did not press Y or n, try again")
        inp = input()
        print("You pressed", inp)
    if inp == "n":
        sys.exit("You pressed n, breaking")


def is_file_image(path: str | Path) -> bool:
    """Check whether a file is an image"""
    # Input checks
    assert Path(path).is_file(), f"{path} does not exist"
    check = path.suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
    return check


def image2bytes(path: str | Path, max_size: int = 1024) -> bytes:
    """
    Convert an image to bytes

    Parameters
    ----------
    path : str | Path
        Path to the image
    max_size : int, optional
        Maximum size of the image, by default 1024

    Returns
    -------
    bytes
        Bytes of the image
    """
    # Check the image exists
    assert Path(path).is_file(), f"{path} does not exist"
    # Check the image is an image
    assert is_file_image(path), f"{path} is not an image"
    # Read the image
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    # Resize the image if it exceeds the maximum size
    dim_max = np.argmax(img.shape[:2])
    pixels_max = img.shape[dim_max]
    if pixels_max > max_size:
        scale = max_size / pixels_max
        img = cv2.resize(img, None, fx=scale, fy=scale)
    # Convert to bytes
    suffix = path.split(".")[-1]
    raw = cv2.imencode(f".{suffix}", img)[1].tobytes()
    assert isinstance(raw, bytes), f"Data should be bytes, not {type(raw)}"
    return raw
