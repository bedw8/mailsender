
from db import engine
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from typing import Optional

class CardBase(SQLModel):
    nro_tarjeta: int = Field(primary_key =True)
    url: str

class Card(CardBase, table=True):
    interkey: str | None = Field(default = None)
    sent: bool = Field(default = False)
    encuestado: Optional["Encuestado"] = Relationship(
        sa_relationship_kwargs={'uselist': False},
        back_populates="giftcard"
    )

class CardCreate(CardBase):
    pass

class CardResponse(CardBase):
    interkey: str
    sent: bool

class EncuestadoBase(SQLModel):
    interkey: str = Field(primary_key =True)
    nombre: str
    sexo: str
    mail: str

class Encuestado(EncuestadoBase, table=True):
    nro_tarjeta: int | None = Field(default=None,foreign_key="card.nro_tarjeta")
    giftcard: Card | None = Relationship(back_populates="encuestado")

class EncuestadoEmail(EncuestadoBase):
    mail: EmailStr

class EncuestadoCreate(EncuestadoBase):
    pass

class EncuestadoResponse(EncuestadoBase):
    nro_tarjeta: int | None = None

class CardEnc(CardResponse):
    encuestado: EncuestadoResponse | None = None

class EncCard(EncuestadoResponse):
    giftcard: CardResponse | None = None
