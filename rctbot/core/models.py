from __future__ import annotations

from enum import Enum, IntEnum
from dataclasses import dataclass

import rctbot.config

# TODO: Tester, Player dataclass.


# TODO: namedtuple?
@dataclass(init=False)
class Tester:
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


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
