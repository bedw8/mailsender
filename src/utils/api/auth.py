from fastapi import AppRouter, Request, RedirectResponse
from google_auth_oauthlib.flow import Flow

router = AppRouter(prefix="/auth")

scopes = ["https://www.googleapis.com/auth/gmail.send"]
flow = Flow.from_client_secrets_file("../stuff/creds/credentials.json", scopes=scopes)


@router.get("/add_account")
async def login(request: Request):
    flow.redirect_uri = request.url_for("auth_callback")
    google_auth_url, _ = flow.authorization_url()

    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
async def auth_callback(code: str, request: Request):
    flow.fetch_token(code=code)
    creds = flow.credentials

    # save
    creds.to_json()
