from __future__ import annotations

# Enum, IntEnum
from enum import IntEnum
from typing import Optional, List, Set
from dataclasses import dataclass

from pydantic import BaseModel, HttpUrl, ValidationError  # pylint: disable=no-name-in-module

# TODO: Tester, Player dataclass.


# TODO: namedtuple?
@dataclass(init=False)
class TesterOld:
    def __init__(self, details: dict) -> None:
        self.details = details
        self.__set()

    # Name mangle set.
    def __set(self) -> None:
        for k, v in self.details:
            self.__setattr__(k, v)

    @property
    def signature_purchased(self) -> bool:
        return self.details["signature"]["purchased"]

    @property
    def signature_url(self) -> str:
        return self.details["signature"].get("url", "")

    @classmethod
    async def from_discord_id(cls) -> Tester:
        # MongoDB
        raise NotImplementedError


# Base class for creating enumerated constants that are also subclasses of int.
class Role(IntEnum):
    COMMUNITY_MEMBER = 0
    MEMBER = 0
    COMMUNITY_MODERATOR = 1
    COMMUNITY_MOD = 1
    MODERATOR = 1
    RCT_TESTER = 2
    TESTER = 2
    RCT_HONORED = 3
    HONORED = 3
    RCT_HOST = 4
    HOST = 4
    RCT_SENIOR = 5
    SENIOR = 5
    RCT_STAFF = 6
    STAFF = 6
    RCT_MANAGER = 7
    MANAGER = 7
    FROSTBURN_STAFF = 8
    GARENA_STAFF = 9
    SPOTLIGHT_PLAYER = 10
    SPOTLIGHT_MANAGER = 11
    SBT_TESTER = 12


class ActivityRank(IntEnum):
    IMMORTAL = 7
    LEGENDARY = 6
    DIAMOND = 5
    GOLD = 4
    SILVER = 3
    BRONZE = 2
    WARNING = 1
    UNRANKED = 0


class Perks(IntEnum):
    pass


@dataclass(init=False)
class CustomEmoji:
    def __init__(self, emojis: list):
        self.emojis = emojis
        self.__set()

    # Name mangle set.
    def __set(self):
        for emoji in self.emojis:
            self.__setattr__(emoji.name, emoji)

    # NOTE: Verify CustomEmoji([]).__dict__


class TesterLadder(BaseModel):
    games: int
    bugs: int
    total_games: int
    total_bugs: int
    tokens: int


class TesterJoined(BaseModel):
    first: str
    last: Optional[str]


class TesterSignature(BaseModel):
    purchased: bool
    url: Optional[str] = ""


class TesterConsents(BaseModel):
    sync_roles: bool


# TODO: roles: List[int], primary_role: int
class Tester(BaseModel):
    _id: str
    enabled: bool
    role: str
    nickname: str
    games: int
    seconds: int
    bugs: int
    total_games: int
    total_seconds: int
    total_bugs: int
    ladder: TesterLadder
    rank_id: int
    bonuses_given: int
    extra: int
    perks: str
    joined: TesterJoined
    signature: TesterSignature
    awards: Optional[List[str]] = list()
    discord_id: int
    account_id: int
    testing_account_id: int
    super_id: int
    testing_super_id: int
    consents: TesterConsents
