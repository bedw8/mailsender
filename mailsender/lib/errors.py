from datetime import datetime
from babel.dates import format_date

class AccountNotFoundOnDB(Exception):
    def __init__(self, email: str):
        super().__init__(
            f"Account: {email} not found on databas. Please add the account."
        )


class AlreadyUnsubscribed(Exception):
    def __init__(self, email: str, campaign_name: str| None = None, date: datetime | None = None):
        mssg = " already unsubscribed."
        if date:
            mssg = f"unsubscribed on {format_date(date)}"
        
        if campaign_name is not None:
            camp = f"campaign {campaign_name}"
        else:
            camp = "default campaign"

        super().__init__(f"Email: {email}" + mssg+ f" for {camp}.")


class RecordNotFound(Exception):
    def __init__(self, mid: int):
        super().__init__(f"Record with message id (mid): {mid} not found.")

class RecordColumnNotFound(Exception):
    def __init__(self, col: str):
        super().__init__(f"Records do not have {repr(col)} attribute.")


class UnsubscribedAddress(Exception):
    def __init__(self, email: str, campaign_name: str | None):
        if campaign_name is not None:
            name = f"campaign {campaign_name}"
        else:
            name = f"default campaign" 

        super().__init__(f"Email: {email} is unsubscribed for {name}.")


class NotUnsubscribed(Exception):
    def __init__(self, email: str, campaign_name: str):
        super().__init__(f"Email: {email} is not unsubscribed to campaign {repr(campaign_name)}.")

class TokenNotFound(Exception):
    def __init__(self, token: str):
        super().__init__(f"Token: {token} does not exist.")

class InvalidCredentials(Exception):
    def __init__(self):
        super().__init__("Invalid credentials.")

class TokenAlreadyExists(Exception):
    def __init__(self, name: str):
        super().__init__(f"Token with name: {name} already exists.")

class CampaignAlreadyExists(Exception):
    def __init__(self, name: str):
        super().__init__(f"Campaign with name: {repr(name)} already exists.")

class CampaignNotFound(Exception):
    def __init__(self, id: int):
        super().__init__(f"Campaign with id: {repr(id)} does not exist.")

