from typing import Protocol
from pydantic import EmailStr
from .message import Message


class EmailService(Protocol):
    def send(
        self,
        to: EmailStr,
        message: Message,
    ):
        pass
