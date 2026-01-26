from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

from io import BinaryIO
from base64 import urlsafe_b64encode

import re

from pydantic import FilePath, validate_call, BeforeValidator, NameEmail
from typing import Annotated

from .utils import validators

StrBuffer = tuple[str, BinaryIO]


class Message:
    @validate_call
    def __init__(
        self,
        subject: str,
        message: str,
        img: StrBuffer | list[StrBuffer] | None = None,
        files: StrBuffer | list[StrBuffer] | None = None,
        html: bool = False,
        fields: dict = {},
        max_image_size: int = 1024,
    ):
        """ """

        # Create the message
        self.mroot = MIMEMultipart()

        for key in fields:
            message = re.sub("{" + key + "}", str(fields[key]), message)

        mtype = "html" if html else "plain"
        mtext = MIMEText(message, mtype)

        self.mroot.attach(mtext)
        self.mroot["Subject"] = subject

        # Add the attachments
        if img:
            InlineImage(img).attach(self)

        if files:
            Attachment(img).attach(self)

    def to_bytes(self) -> dict:
        # Encode the message and save it in a dictionary
        encoded = urlsafe_b64encode(self.mroot.as_bytes()).decode()
        return {"raw": encoded}

    @property
    def sender(self):
        """The sender property."""
        return self.mroot["From"]

    @sender.setter
    def sender(self, value: NameEmail):
        self.mroot["From"] = str(value)


StrBufferList = Annotated[list[StrBuffer], BeforeValidator(validators.ensure_list)]


class Attachment:
    @validate_call
    def __init__(self, input: StrBufferList):
        self._inputlist = input

        self._load()

    def _load_single(self, file: StrBuffer):
        name, f = file
        self._mimelist.append(MIMEApplication(f.read(), Name=name))

    def _load(self):
        self._mimelist = []
        for file in self._inputlist:
            self._load_single(file)

    def attach(self, multipart: MIMEMultipart):
        for attachment in self._mimelist:
            multipart.attach(attachment)


class InlineImage(Attachment):
    def _load_single(self, img: StrBuffer):
        cid, data = img
        img = MIMEImage(data.read())
        img.add_header("Content-ID", f"<{cid}>")
        self._mimelist.append(img)


class AttachmentLegacy:
    @validate_call
    def __init__(
        self,
        files: Annotated[list[str], BeforeValidator(validators.ensure_list)],
    ):
        self.files = files

    def iter_files(self):
        for path in self.files:
            data, subtype = AttachmentLegacy.get_data(path)
            yield data, subtype

    @validate_call
    @staticmethod
    def get_data(path: FilePath, max_image_size: int = 1024):
        subtype = path.suffix.strip(".")
        is_image = validators.is_file_image(path)
        if is_image:
            data = validators.image2bytes(path=path, max_size=max_image_size)
        else:
            with open(path, "rb") as fp:
                data = fp.read()

        return data, subtype
