from datetime import datetime
from babel.dates import format_date


class AccountNotFoundOnDB(Exception):
    def __init__(self, email: str):
        super().__init__(
            f"Account: {email} not found on databas. Please add the account."
        )


class AlreadyUnsubscribed(Exception):
    def __init__(self, email: str, date: datetime | None = None):
        mssg = " already unsubscribed."
        if date:
            mssg = f" unsubscribed on {format_date(date)}"

        super().__init__(f"Email: {email}" + mssg)


class RecordNotFound(Exception):
    def __init__(self, mid: int):
        super().__init__(f"Record with message id (mid): {mid} not found.")


class UnsubscribedAddress(Exception):
    def __init__(self, email: str):
        super().__init__(f"Email: {email} is unsubscribed.")


class NotUnsubscribed(Exception):
    def __init__(self, email: str):
        super().__init__(f"Email: {email} is not unsubscribed.")
