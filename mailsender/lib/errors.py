from datetime import datetime
from babel.dates import format_date


class AccountNotFoundOnDB(Exception):
    def __init__(self, email: str):
        super().__init__(
            f"Account: {email} not found on databas. Please add the account."
        )


class AlreadyUnsubsribed(Exception):
    def __init__(self, email: str, date: datetime | None = None):
        mssg = " already unsubscribed."
        if date:
            mssg = f" unsubscribed on {format_date(date)}"

        super().__init__(f"Email: {email}" + mssg)
