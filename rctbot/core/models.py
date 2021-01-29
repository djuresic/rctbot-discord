from __future__ import annotations

from pydantic import BaseModel  # pylint: disable=no-name-in-module

# from rctbot.core.rct.models import *

# NOTE: This must contain all models.


class User(BaseModel):
    # abc.Updatable, abc.User -> User
    id: int
    signature: Signature


class Signature(BaseModel):
    purchased: bool
    url: str = None
