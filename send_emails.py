# External libraries
from pathlib import Path
from time import sleep

# Internal config and utility files
from utils import get_gmail_service, message2bytes

import email.message
from typing import BinaryIO
import pydantic

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

import re


class Sender:
    def __init__(self, from_address, credentials="credentials.json"):
        self._from = from_address
        self._scopes = ["https://www.googleapis.com/auth/gmail.send"]
        self.credentials = Path(credentials)
        self._port = 0
        self._max_emails = 100
        self._service = None
        self._i = 0
        assert self.credentials.is_file(), "El archivo de credenciales no existe"

    @property
    def service(self):
        if not self._service:
            self._service = get_gmail_service(
                scopes=self._scopes, credentials=self.credentials, port=self._port
            )
        return self._service

    def send(self, to: pydantic.EmailStr, message):
        ## message is a message object. Not the text.
        del message["To"]
        message["To"] = to
        # Convert the message to a raw byte
        raw_message = message2bytes(message)

        # Send the message
        send_message = (
            self.service.users()
            .messages()
            .send(userId="me", body=raw_message)
            .execute()
        )
        if "SENT" not in send_message["labelIds"]:
            print(f"Email not sent to {email}")
        if (self._i + 1) % self._max_emails == 0:
            print(f"Pausing for 1 second after sending {self._i + 1} emails")
            sleep(1)
        self._i += 1

    def send_bulk(self, iterable):
        pass

    def create_message(
        self,
        subject: str,
        message: str,
        img: BinaryIO | list[BinaryIO] | None = None,
        files: BinaryIO | list[BinaryIO] | None = None,
        html: bool = False,
        fields: dict = {},
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
        subject : str
            Subject line

        Returns
        -------
        dict
            Dictionary with the raw base64 encoded message
        """
        # Input checks
        assert isinstance(message, str), (
            f"Message should be a string, not {type(message)}"
        )
        assert isinstance(subject, str), (
            f"Subject should be a string, not {type(subject)}"
        )

        # Create the message
        # msg = EmailMessage()
        mroot = MIMEMultipart()

        for key in fields:
            message = re.sub("{" + key + "}", str(fields[key]), message)

        if not html:
            mtext = MIMEText(message)
        else:
            mtext = MIMEText(message, "html")

        mroot.attach(mtext)
        # msg['To'] = email_to
        mroot["From"] = self._from
        mroot["Subject"] = subject
        # Add the attachments

        if img:

            def attach(cid, data):
                img = MIMEImage(data.read())
                img.add_header("Content-ID", f"<{cid}>")
                mroot.attach(img)

            if not isinstance(img, list):
                attach(*img)
            else:
                for i in img:
                    attach(*i)

        if files:
            #    files = utils.str2list(files)
            #    for path in files:
            #        is_image = utils.is_file_image(path)
            #        subtype = path.suffix.strip('.')
            #        if is_image:
            #            data = utils.image2bytes(path=path, max_size=max_image_size)
            #        else:
            #            with open(path, 'rb') as fp:
            #                data = fp.read()
            #        msg.add_attachment(data, maintype='image', subtype=subtype)
            # Return the message
            def attach(name, f):
                attachment = MIMEApplication(f.read(), Name=name)
                mroot.attach(attachment)

            if not isinstance(files, list):
                attach(*files)
            else:
                for f in files:
                    attach(*f)

        return mroot


######

sender = Sender("Encuesta ELSOC <bedwards@fen.uchile.cl>")


def send(email, subject, mssg_content, sender=sender, **kwargs):
    mssg = sender.create_message(subject, mssg_content, **kwargs)
    sender.send(email, mssg)
    print(f"SENT - {email}")


if __name__ == "__main__":
    pass
