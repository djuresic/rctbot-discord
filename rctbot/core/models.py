from __future__ import annotations

from typing import Optional, List, Set

from pydantic import BaseModel, HttpUrl  # pylint: disable=no-name-in-module

# from rctbot.core.rct.models import *

# NOTE: This must contain all models.


class Signature(BaseModel):
    purchased: bool
    url: Optional[HttpUrl] = None


class User(BaseModel):
    # TODO: abc.Updatable, abc.User -> User
    id: int
    signature: Signature


# Reference: https://fastapi.tiangolo.com/tutorial/body-nested-models/
class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: Set[str] = set()
    images: Optional[List[Image]] = None


class Offer(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    items: List[Item]
