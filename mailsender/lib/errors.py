class AccountNotFoundOnDB(Exception):
    def __init__(self, email: str):
        super().__init__(
            f"Account: {email} not found on databas. Please add the account."
        )
