from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import mailsender.config as config
from mailsender.lib.gmail import save_token

router = APIRouter(prefix="/auth")

scopes = config.gmail.scopes
flow = Flow.from_client_secrets_file(config.credentials_file, scopes=scopes)


@router.get("/add_account")
async def login(request: Request):
    flow.redirect_uri = request.url_for("auth_callback")
    google_auth_url, _ = flow.authorization_url()

    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
async def auth_callback(code: str, request: Request):
    flow.fetch_token(code=code)
    creds = flow.credentials

    serv = build("oauth2", "v2", credentials=creds)
    email = serv.userinfo().get().execute().get("email")

    print(email)
    # save
    save_token(token_data=creds.to_json(), to_db=email)
    return Response(content="Autenticado correctamente")
