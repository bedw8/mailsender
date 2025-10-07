#!/usr/bin/env python
# coding: utf-8

import os
import sys

import jmespath
from google.oauth2.credentials import Credentials

# from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


from sqlmodel import col

gc_path = "/Users/bedw/Documents/work/giftcards/"
sys.path.insert(0, gc_path)

from dotenv import load_dotenv

load_dotenv(gc_path + ".env")

from db import Session, engine, select

from models import Encuestado

sc = ["https://www.googleapis.com/auth/gmail.modify"]

# sc = ["https://www.googleapis.com/auth/gmail.modify"]
# flow = InstalledAppFlow.from_client_secrets_file('credentials2.json',sc)
# creds = flow.run_local_server(port=0)

# with open("token_getBA.json", "w") as token:
#    token.write(creds.to_json())

if os.path.exists("token_getBA.json"):
    creds = Credentials.from_authorized_user_file("token_getBA.json", sc)

service = build("gmail", "v1", credentials=creds)


def getPage(listParams, token=None):
    return service.users().threads().list(**listParams, pageToken=token).execute()


def getThread(tid):
    return (
        service.users().threads().get(userId="me", id=tid, format="metadata").execute()
    )


def _getAddresses(listparams):
    threads = []
    token = None
    while True:
        page = getPage(listparams, token)
        ids = jmespath.search("threads[].id", page)
        ids = ids if ids else []
        token = jmespath.search("nextPageToken", page)
        threads += ids
        print(token)
        if token is None:
            break

    addresses = {}
    for i, tid in enumerate(threads):
        t = getThread(tid)
        addresses[tid] = jmespath.search(
            "messages[0].payload.headers[?name==`To`].value", t
        )[0].lower()
        print(i + 1, end="\r")

    return addresses


def _getEnc_db(addresses, session):
    st = select(Encuestado).where(col(Encuestado.mail).in_(addresses.values()))
    ee = session.exec(st).all()
    return ee


def _archiveThread(tid, archiveParams):
    return (
        service.users()
        .threads()
        .modify(userId="me", id=tid, body=archiveParams)
        .execute()
    )


def archiveMails(addresses, dbUpdateParams, archiveParams, session):
    encDB = _getEnc_db(addresses, session)

    ## Update DB
    for e in [e for e in encDB if not e.skip]:
        for attr, value in dbUpdateParams.items():
            if attr is not None:
                setattr(e, attr, value)
        s.add(e)

    s.commit()

    for e in encDB:
        s.refresh(e)

    #####
    #####

    toArchive = [
        addr for addr in addresses if addresses[addr] in [e.mail for e in encDB]
    ]

    ## Archive
    tN = len(toArchive)
    for i, tid in enumerate(toArchive):
        _archiveThread(tid, archiveParams)
        print(i + 1, "/", tN, end="\r")


def _get_labels_ids(label):
    labelsRequest = service.users().labels().list(userId="me").execute()
    jmespath.search(f"labels[?name==`{label}`].id", labelsRequest)


s = Session(engine)

## Fix api limit rebound - params
# dict(
#     userId="me", q="Has llegado al límite de mensajes que puedes enviar label:INBOX"
# ),
# dict(sent_email=False, skip=False, skip_desc=""),
# #fixed - Label_235808472490382251
# dict(addLabelIds=["Label_235808472490382251"], removeLabelIds=labelsToRemove)


labelsToRemove = (["INBOX", "UNREAD", "CATEGORY_UPDATES"],)
params = (  # searchParams, dbUpdateParams, archiveParams
    (
        dict(userId="me", q="No se ha encontrado la dirección label:INBOX"),
        dict(sent_email=False, skip=True, skip_desc="Mail no existe"),
        # mail-no-existe - Label_235808472490382251
        dict(addLabelIds=["Label_235808472490382251"], removeLabelIds=labelsToRemove),
    ),
    (
        dict(
            userId="me",
            q='"postmaster" OR "No se ha completado la entrega" OR "El mensaje no se ha podido enviar" OR "La bandeja de entrada del destinatario está llena" label:INBOX',
        ),
        dict(sent_email=False, skip=True, skip_desc="Error al enviar"),
        # otro-error - Label_8534569595574788589
        dict(addLabelIds=["Label_8534569595574788589"], removeLabelIds=labelsToRemove),
    ),
)


def loop():
    i = 0
    for sParams, u, a in params:
        i += 1
        addresses = _getAddresses(sParams)

        archiveMails(addresses, u, a, s)
        print(i)


if __name__ == "__main__":
    loop()
