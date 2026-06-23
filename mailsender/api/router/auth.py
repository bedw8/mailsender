from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from mailsender.db.token import SQLiteTokenDBInterface, Token
from mailsender.lib.errors import InvalidCredentials, TokenAlreadyExists, TokenNotFound
from mailsender.lib.gmail import save_token
from ..main import config
from typing import Annotated

router = APIRouter(prefix="/auth")

scopes = config.gmail.scopes
flow = Flow.from_client_secrets_file(config.gmail.credentials_file, scopes=scopes)

token_db = SQLiteTokenDBInterface()


async def validate_token(token: str, req: Request) -> str | Token:
    try: 
        tok = token_db.validate_token(token)
    except InvalidCredentials as e:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
                )

    return tok

token_dep = Annotated[ str | Token, Depends(validate_token) ] 


@router.post("/token")
async def new_token(name: str, token: token_dep):
    try: 
        tok = token_db.new_token(name)
    except TokenAlreadyExists as e:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
                )

    return tok

@router.delete("/token/{id}")
async def revoke_token(id: str, token: token_dep):
    try:
        tok = token_db.revoke_token(id)
    except TokenNotFound as e:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
                )
    return tok

@router.get("/tokens")
async def list_token(token: token_dep):
    toks = token_db.list_tokens()
    return toks

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

    # save
    save_token(token_data=creds.to_json(), to_db=email)
    return Response(content="Autenticado correctamente")
