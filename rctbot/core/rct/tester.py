from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass

import aiohttp
import discord

import rctbot.config
from rctbot.core.rct.models import ActivityRank, Role
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.hon.masterserver import Client


@dataclass
class TesterManagerResult:
    """Result of TesterManager methods.

    Every TesterManager method should return an instance of this data class.

    Attributes:
        accepted: A boolean indicating whether the action was accepted.
        message: A string containing the result message.
        discord_message: A string containing the result message. Wraps certain
            keywords in Discord markdown to make it look prettier when sent in
            regular or embedded messages on Discord.
    """

    accepted: bool
    discord_message: str

    @property
    def message(self) -> str:
        """Message without Discord markdown. Assumes presence of bold and
        italic text only.

        Returns:
            str: The message with the special markdown characters removed.
        """
        return self.discord_message.replace("*", "").replace("\\", "")


class TesterManager:
    """
    Interface for managing players in RCT. Not an asynchronous context manager.
    """

    def __init__(self) -> None:
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]

    async def full_add(self, nickname: str) -> NotImplementedError:
        """Adds a player to RCT.
        
        Modifies the DB, grants all permissions and accesses. Be sure to remove
        backslashes from the nick if it originates from Discord and escapes
        markdown.

        Args:
            nickname (str): Nickname of the player to be added.

        Raises:
            NotImplementedError

        Returns:
            NotImplementedError
        """
        raise NotImplementedError

    async def full_remove(self, nickname: str) -> NotImplementedError:
        """Removs a player from RCT.

        Modifies the DB, revokes all permissions and accesses, and removes
        perks. Be sure to remove backslashes from the nick if it originates
        from Discord and escapes markdown.

        Args:
            nickname (str): Nickname of the player to be removed.

        Raises:
            NotImplementedError

        Returns:
            NotImplementedError
        """
        raise NotImplementedError

    async def add(self, nickname: str) -> TesterManagerResult:
        """Adds a player to RCT.
        
        This modifies the DB only; client, forums, and portal access must be
        granted separately. Be sure to remove backslashes from the nick if it
        originates from Discord and escapes markdown.

        Args:
            nickname (str): Nickname of the player to be added.

        Returns:
            TesterManagerResult: Instance of TesterManagerResult.
        """
        async with aiohttp.ClientSession() as session:
            ac_client = Client("ac", session=session)
            ac_data = await ac_client.nick2id(nickname)
            if not ac_data:
                return TesterManagerResult(
                    False,
                    (
                        f"**Addition failed!**"
                        f" Could not find IDs for **{discord.utils.escape_markdown(nickname)}**."
                    ),
                )
            nickname = ac_data["nickname"]
            account_id = int(ac_data["account_id"])
            super_id = int((await ac_client.show_stats(nickname, "campaign"))[b"super_id"].decode())

            rc_client = Client("rc", session=session)
            rc_data = await rc_client.nick2id(nickname)
            if not rc_data:
                testing_nickname = await rc_client.id2nick(account_id)
                if not testing_nickname:
                    return TesterManagerResult(
                        False,
                        (
                            f"**Addition failed!**"
                            f" Neither **{discord.utils.escape_markdown(nickname)}** nor **{account_id}** exist"
                            f" in the test client DB. Create a new account or search by Super ID."
                        ),
                    )
                testing_account_id = account_id
            else:
                testing_nickname = rc_data["nickname"]
                testing_account_id = int(rc_data["account_id"])
            testing_super_id = int((await rc_client.show_stats(testing_nickname, "campaign"))[b"super_id"].decode())

        tester = await self.testers.find_one(
            {
                "$or": [
                    {"nickname": nickname},
                    {"account_id": account_id},
                    {"testing_account_id": testing_account_id},
                    {"super_id": super_id},
                    {"testing_super_id": testing_super_id},
                ]
            },
            {"nickname": 1, "account_id": 1, "testing_account_id": 1},
            collation={"locale": "en", "strength": 1},
        )
        if tester:
            # TODO: Reinstate using tester["nickname"] or by passing the entire projection.
            return TesterManagerResult(
                False,
                (
                    f"Retail player **{discord.utils.escape_markdown(nickname)}** ({account_id})"
                    f" already exist in DB"
                    f' as **{discord.utils.escape_markdown(tester["nickname"])}** ({tester["account_id"]})'
                    f' with RCT ID **{tester.get("testing_account_id", "None")}**.'
                ),
            )

        document = {
            "enabled": True,
            "role": "Tester",
            "role_id": Role.RCT_TESTER,
            "nickname": nickname,
            "games": 0,
            "seconds": 0,
            "bugs": 0,
            "total_games": 0,
            "total_seconds": 0,
            "total_bugs": 0,
            "tokens": 0,
            "ladder": {"games": 0, "bugs": 0, "total_games": 0, "total_bugs": 0, "tokens": 0,},
            "rank_id": ActivityRank.GOLD,
            "bonuses_given": 0,
            "extra": 0,
            "perks": "No",  # TODO: Perks IntEnum
            "signature": {"purchased": False, "url": ""},
            "joined": {"first": datetime.utcnow()},
        }
        document["awards"] = []
        document["discord_id"] = None
        document["account_id"] = account_id
        document["testing_account_id"] = testing_account_id
        document["super_id"] = super_id
        document["testing_super_id"] = testing_super_id

        # NOTE: Add future consents here.
        document["consents"] = {"sync_roles": True}

        result = await self.testers.insert_one(document)
        if result.acknowledged:
            return TesterManagerResult(
                True, f"Added **{discord.utils.escape_markdown(nickname)}** ({account_id}) to RCT."
            )
        return TesterManagerResult(
            False, f"**Addition failed!** Could not add **{discord.utils.escape_markdown(nickname)}** to RCT."
        )

    async def reinstate(self, nickname: str) -> TesterManagerResult:
        """Reinstates a player as an RCT.
        
        Re-enables their account, restores the activity rank to default, and
        sets a new join date. This modifies the DB only; client, forums, and
        portal access must be granted separately. Be sure to remove backslashes
        from the nick if it originates from Discord and escapes markdown.

        Args:
            nickname (str): Nickname of the player to be reinstated.

        Returns:
            TesterManagerResult: Instance of TesterManagerResult.
        """
        result = await self.testers.find_one_and_update(
            {"nickname": nickname},
            {"$set": {"enabled": True, "rank_id": ActivityRank.GOLD, "joined.last": datetime.utcnow(),}},
            projection={"_id": 0, "nickname": 1, "account_id": 1},
            collation={"locale": "en", "strength": 1},
        )
        if result:
            return TesterManagerResult(
                True, f'Reinstated **{discord.utils.escape_markdown(result["nickname"])}** ({result["account_id"]}).'
            )
        return TesterManagerResult(
            False, f"**Reinstatement failed!** Could not find **{discord.utils.escape_markdown(nickname)}** in DB."
        )

    async def remove(self, nickname: str) -> TesterManagerResult:
        """Removes a player from RCT.
        
        Disables their account. This modifies the DB only; client, forums, and
        (optionally) portal access must be revoked separately. Be sure to
        remove backslashes from the nick if it originates from Discord and
        escapes markdown.

        Args:
            nickname (str): Nickname of the player to be removed.

        Returns:
            TesterManagerResult: Instance of TesterManagerResult.
        """
        result = await self.testers.find_one_and_update(
            {"nickname": nickname},
            {"$set": {"enabled": False}},
            projection={"_id": 0, "nickname": 1, "account_id": 1},
            collation={"locale": "en", "strength": 1},
        )
        if result:
            return TesterManagerResult(
                True,
                f'Removed **{discord.utils.escape_markdown(result["nickname"])}** ({result["account_id"]}) from RCT.',
            )
        return TesterManagerResult(
            False, f"**Removal failed!** Could not find **{discord.utils.escape_markdown(nickname)}** in DB."
        )

    async def link_discord(self, member: discord.Member) -> TesterManagerResult:
        """Attach Discord ID to a tester in DB.

        Links member's Discord ID to a tester account with the same nickname as
        their display name. This intentionally overwrites any existing user ID,
        use with caution!

        Args:
            member (discord.Member): The tester.

        Returns:
            TesterManagerResult: Instance of TesterManagerResult.
        """
        result = await self.testers.find_one_and_update(
            {"nickname": member.display_name},
            {"$set": {"discord_id": member.id}},
            projection={"_id": 0, "nickname": 1, "account_id": 1},
            collation={"locale": "en", "strength": 1},
        )
        if result:
            return TesterManagerResult(
                True,
                (
                    f"Linked **{member}** ({member.id})"
                    f' to **{discord.utils.escape_markdown(result["nickname"])}** ({result["account_id"]}) by ID.'
                ),
            )
        return TesterManagerResult(False, f"**Linking failed!** Could not find **{member.display_name}** in DB.")
