"""
RCTBot A simple Discord bot with some Heroes of Newerth integration.
Copyright (C) 2020  Danijel Jurešić

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Tuple

import aiohttp
import discord

import rctbot.config
from rctbot.core.mongodb import CLIENT
from rctbot.core.models import Role, ActivityRank

from rctbot.hon.masterserver import Client
from rctbot.hon.portal import VPClient

# TODO: Typing. Remove copy pasta code.


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
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
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


# To models.
@dataclass
class CycleValues:

    # Tokens per activity:
    bug: int = 100
    game: int = 10
    second: float = 0.003725
    ten: int = 75
    twenty: int = 225
    fifty: int = 750
    # Multipliers:
    multiplier: Tuple[float, ...] = (0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5)
    artificial: float = 3.5
    # Game requirement per rank:
    keep: Tuple[int, ...] = (0, 1, 1, 3, 5, 7, 10, 0)
    advance: Tuple[int, ...] = (0, 3, 5, 8, 10, 12, 0, 0)


class CycleManagerResult:
    pass


# TODO: Handle only enabled accounts
class CycleManager:
    """
    Interface for managing RCT testing cycles. Not an asynchronous context manager.
    """

    def __init__(self):
        # Database
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_cycles = self.db[rctbot.config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

        self.values = CycleValues()

        # Match processor
        # self.mp = MatchProcessor()

    async def archive_cycle(self):
        testers = await (
            self.testers.find(
                {"enabled": True, "tokens": {"$gt": 0}},
                {
                    "role": 1,
                    "role_id": 1,
                    "nickname": 1,
                    "games": 1,
                    "seconds": 1,
                    "bugs": 1,
                    "total_games": 1,
                    "total_seconds": 1,
                    "total_bugs": 1,
                    "tokens": 1,
                    "ladder": 1,
                    "rank_id": 1,
                    "bonuses_given": 1,
                    "extra": 1,
                    "perks": 1,
                    "joined": 1,
                    "awards": 1,
                    "discord_id": 1,
                    "account_id": 1,
                    "testing_account_id": 1,
                    "super_id": 1,
                    "testing_super_id": 1,
                },
                sort=list({"tokens": -1}.items()),
            )
        ).to_list(length=None)
        games = await (self.testing_games.find({"retrieved": True}, sort=list({"match_id": 1}.items()))).to_list(
            length=None
        )
        if len(games) == 0 or len(testers) == 0:
            # TODO: Result
            print("len games testers 0")
            return False
        start = datetime.fromtimestamp(games[0]["timestamp"])
        if not (last_cycle := await self.testing_cycles.find_one({}, {"_id": 1}, sort=list({"_id": -1}.items()))):
            id_ = 1
        else:
            id_ = last_cycle["_id"] + 1
        result = await self.testing_cycles.insert_one(
            {"_id": id_, "games": games, "participants": testers, "start": start, "end": datetime.now(timezone.utc)}
        )
        if not result.acknowledged:
            return False
        result = await self.testing_games.delete_many({})
        return result.acknowledged

    async def new_cycle(self):
        values = {
            "games": 0,
            "seconds": 0,
            "bugs": 0,
            "tokens": 0,
            "ladder": {"games": 0, "bugs": 0, "total_games": 0, "total_bugs": 0, "tokens": 0,},
            "extra": 0,
        }
        async for document in self.testers.find({}, {"account_id": 1, "total_games": 1, "bonuses_given": 1}):
            # TODO: Change this to account_id after fetching all IDs.
            bonus_last_cycle = math.floor((document["total_games"] / 50) - document["bonuses_given"])
            values["bonuses_given"] = document["bonuses_given"] + bonus_last_cycle
            await self.testers.update_one({"account_id": document["account_id"]}, {"$set": values})

    async def update_games_and_seconds(self):
        # TODO: This should rely more on MongoDB rather than the application itself.
        participants = []
        retrieved = 0
        async for document in self.testing_games.find({"retrieved": True}):
            participants.extend(document["participants"])
            retrieved += 1

        # TODO: collections.defaultdict

        # Using set() to remove duplicates. Account ID is from the testing database.
        account_ids = list(set([entry["account_id"] for entry in participants]))
        players = []
        for account_id in account_ids:
            games = 0
            seconds = 0
            for entry in participants:
                if entry["account_id"] == account_id:
                    games += 1
                    seconds += entry["seconds"]
            players.append((account_id, games, seconds))
        # print(players)
        # TODO: Remove players list and do update in the loop instead.
        acknowledged = 0
        for player in players:
            result = await self.testers.update_one(
                {"testing_account_id": player[0]}, {"$set": {"games": player[1], "seconds": player[2]}},
            )
            if result.acknowledged:
                acknowledged += 1

    async def update_bugs(self):
        # TODO
        raise NotImplementedError

    async def update_total(self):
        # NOTE: fine
        found = 0
        acknowledged = 0
        async for document in self.testers.find({}, {"account_id": 1, "games": 1, "seconds": 1, "bugs": 1}):
            found += 1
            result = await self.testers.update_one(
                {"account_id": document["account_id"]},
                {
                    "$inc": {
                        "total_games": document["games"],
                        "total_seconds": document["seconds"],
                        "total_bugs": document["bugs"],
                    }
                },
            )
            if result.acknowledged:
                acknowledged += 1

    async def update_ranks(self):
        # NOTE: fine
        found = 0  # TODO
        async for tester in self.testers.find(
            {"enabled": True}, {"account_id": 1, "rank_id": 1, "games": 1, "bugs": 1}
        ):
            rank_id = tester["rank_id"]
            games = tester["games"]
            bugs = tester["bugs"]
            # Ignore testers with absence field and Gold and below rank.
            if "absence" in tester and rank_id <= ActivityRank.GOLD:
                pass
            if ActivityRank.UNRANKED < rank_id < ActivityRank.LEGENDARY:
                if (games + bugs) >= self.values.advance[rank_id]:
                    await self.testers.update_one({"account_id": tester["account_id"]}, {"$inc": {"rank_id": 1}})
                elif (games + bugs) < self.values.keep[rank_id]:
                    await self.testers.update_one({"account_id": tester["account_id"]}, {"$inc": {"rank_id": -1}})
                else:
                    pass
            # Should've just put 1000 games requirement for advancing to Immortal... Keeping this for now.
            if rank_id >= ActivityRank.LEGENDARY and (games + bugs) < self.values.keep[rank_id]:
                await self.testers.update_one({"account_id": tester["account_id"]}, {"$inc": {"rank_id": -1}})

    async def update_tokens(self):
        async for tester in self.testers.find({}):
            games = tester["games"]
            bonus = math.floor((tester["total_games"] / 50) - tester["bonuses_given"])

            tokens = round(
                (
                    games * self.values.game
                    + tester["seconds"] * self.values.second
                    + (self.values.ten if games >= 10 else 0)
                    + (self.values.twenty if games >= 20 else 0)
                )
                * (self.values.multiplier[tester["rank_id"]] + self.values.artificial)
                + bonus * self.values.fifty
                + tester["bugs"] * self.values.bug
                + (tester["extra"])
            )
            await self.testers.update_one(
                {"account_id": tester["account_id"]}, {"$set": {"tokens": tokens}},
            )

    async def update_perks(self) -> str:
        result = await self.testers.update_many(
            {
                "enabled": True,
                "perks": "No",
                "$or": [{"total_games": {"$gte": 25}}, {"total_bugs": {"$gte": 25}}],
                "discord_id": {"$not": {"$eq": None}},
            },
            {"$set": {"perks": "Pending"}},
        )
        if result.acknowledged:
            return f"Found {result.matched_count} and updated {result.modified_count} members' perks status."
        return f"Could not update perks status!"

    async def distribute_tokens(self):
        """
        coro Modify tokens using the current values from DB and return
        tuple (success, error).
        """
        mod_input = []
        async for tester in self.testers.find(
            {"enabled": True, "tokens": {"$gt": 0}}, {"nickname": 1, "tokens": 1}, sort=list({"tokens": -1}.items()),
        ):
            mod_input.append(f'{tester["nickname"]} {tester["tokens"]}')
        async with VPClient() as portal:
            return await portal.mod_tokens(mod_input)


class DatabaseManager:
    def __init__(self, session=None):
        self.url = rctbot.config.HON_VP_URL
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.token = None

        # Database
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_cycles = self.db[rctbot.config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

    # async def __aenter__(self) -> "DatabaseManager":
    async def __aenter__(self):
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        """Coroutine. Close the session."""
        await self.session.close()

    async def fix_discord_id(self, member):
        await self.testers.update_one(
            {"nickname": member.display_name},
            {"$set": {"discord_id": member.id}},
            collation={"locale": "en", "strength": 1},
        )

    async def migrate_spreadsheet_data(self):
        ranks = {
            "Immortal": 7,
            "Legendary": 6,
            "Diamond": 5,
            "Gold": 4,
            "Silver": 3,
            "Bronze": 2,
            "Warning": 1,
            "No rank": 0,
        }
        purchased = {"No": False, "Yes": True}
        documents = []
        for row in rctbot.config.LIST_OF_LISTS[2:]:
            document = {
                "enabled": bool(row[0] != "None"),
                "role": row[0],
                "nickname": row[1],
                "games": int(row[2]),
                "seconds": int(row[3]),
                "bugs": int(row[4]),
                "total_games": int(row[5]),
                "total_seconds": int(row[6]),
                "total_bugs": int(row[7]),
                "tokens": int(row[8]),
                "ladder": {"games": 0, "bugs": 0, "total_games": 0, "total_bugs": 0, "tokens": 0,},
                "rank_id": ranks[row[10]],
                "bonuses_given": int(row[15]),
                "extra": int(row[18]),
                "perks": row[19],
                "joined": row[20],
                "signature": {"purchased": purchased[row[35]], "url": row[36]},
            }
            if row[21] != "":
                document["absence"] = row[21]
            if row[22] != "":
                document["removal_reason"] = row[22]

            if row[31] != "":
                document["awards"] = [row[31]]
            else:
                document["awards"] = []

            if row[32] != "":
                document["discord_id"] = int(row[32])
            else:
                document["discord_id"] = None

            if row[33] != "":
                document["account_id"] = int(row[33])
            else:
                document["account_id"] = None
            print(document)
            documents.append(document)
        result = await self.testers.insert_many(documents)
        return "Inserted %d documents." % (len(result.inserted_ids),)

    async def set_testing_account_id(self):
        # print("entered")
        async for tester in self.testers.find({}):
            # print(tester)
            nickname = tester["nickname"]
            async with aiohttp.ClientSession() as session:
                try:
                    testing_account_id = int(
                        (await Client("rc", session=session).show_simple_stats(nickname))[b"account_id"].decode()
                    )
                except:
                    testing_account_id = None
            print(testing_account_id, nickname)
            await self.testers.update_one(
                {"nickname": nickname}, {"$set": {"testing_account_id": testing_account_id}},
            )

    async def set_super_id(self):
        # trash but works
        async def retrieve_super_id(session, account_id, masterserver):
            client = Client(masterserver, session=session)
            nickname = await client.id2nick(account_id)
            return int((await client.show_stats(nickname, "ranked"))[b"super_id"].decode())

        async for tester in self.testers.find(
            {"$or": [{"super_id": None}, {"testing_super_id": None}]},
            {"nickname": 1, "account_id": 1, "testing_account_id": 1},
        ):
            # print(tester)
            async with aiohttp.ClientSession() as session:
                try:
                    super_id = await retrieve_super_id(session, tester["account_id"], "ac")
                except AttributeError:
                    super_id = None
                try:
                    testing_super_id = await retrieve_super_id(session, tester["testing_account_id"], "rc")
                except AttributeError:
                    testing_super_id = None
            print(tester["nickname"], super_id, testing_super_id)
            await self.testers.update_one(
                {"account_id": tester["account_id"]},
                {"$set": {"super_id": super_id, "testing_super_id": testing_super_id}},
            )

    async def standardize_joined(self) -> str:
        found = 0
        acknowledged = 0
        async for tester in self.testers.find({}):
            found += 1
            nickname = tester["nickname"]
            join_date_string = tester["joined"]

            def date_dBY_dbY(date_string):
                try:
                    return datetime.strptime(date_string, "%d %B %Y")
                except ValueError:
                    return datetime.strptime(date_string, "%d %b %Y")

            if "/" in join_date_string:
                date = datetime.strptime(join_date_string, "%m/%d/%Y")
            elif "," in join_date_string:
                date = datetime.strptime(join_date_string, "%B %d, %Y")
            elif "st August " in join_date_string:
                join_date_string = join_date_string.replace("st August ", " August ")
                date = date_dBY_dbY(join_date_string)
            elif "st " in join_date_string and "ust " not in join_date_string:
                join_date_string = join_date_string.replace("st ", " ")
                date = date_dBY_dbY(join_date_string)
            elif "nd " in join_date_string:
                join_date_string = join_date_string.replace("nd ", " ")
                date = date_dBY_dbY(join_date_string)
            elif "rd " in join_date_string:
                join_date_string = join_date_string.replace("rd ", " ")
                date = date_dBY_dbY(join_date_string)
            elif "th " in join_date_string:
                join_date_string = join_date_string.replace("th ", " ")
                date = date_dBY_dbY(join_date_string)
            elif "20" in join_date_string and "-" in join_date_string and "T" in join_date_string:
                date = datetime.fromisoformat(join_date_string)
            else:
                date = datetime.fromisoformat("2016-06-30")

            iso_date = datetime(
                date.year,
                date.month,
                date.day,
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=random.randint(0, 999999),
                tzinfo=timezone.utc,
            )

            # date = date.astimezone(tz=timezone.utc).isoformat() if not isinstance(date, str) else date
            print(f"{nickname} {iso_date}")
            result = await self.testers.update_one({"nickname": nickname}, {"$set": {"joined": {"first": iso_date}}})
            if result.acknowledged:
                acknowledged += 1
        return f"Found {found} and updated {acknowledged}."


# TODO: Change static methods.


class MatchManipulator:
    def __init__(self, masterserver="rc", session=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.client = Client(masterserver, session=self.session)
        self.db_client = CLIENT
        self.db = self.db_client[rctbot.config.MONGO_DATABASE_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        """Coroutine. Close the session."""
        await self.session.close()

    async def match_data(self, match_id):
        """Return basic match data dictionary for match ID."""
        match_id = int(match_id)
        match_stats = await self.client.get_match_stats(match_id)
        # print(match_stats)

        summary = match_stats[b"match_summ"][match_id]
        if b"mname" not in summary:
            return None
        match_name = summary[b"mname"].decode()
        timestamp = summary[b"timestamp"]
        length = int(summary[b"time_played"].decode())
        server_id = int(summary[b"server_id"].decode())
        server_name = summary[b"name"].decode()
        version = summary[b"version"].decode()
        map_name = summary[b"map"].decode()
        game_mode = summary[b"gamemode"].decode() if b"gamemode" in summary else None
        url = summary[b"url"].decode()
        s3_url = summary[b"s3_url"].decode()
        winning_team = summary[b"winning_team"] if b"winning_team" in summary else 0

        if b"match_player_stats" not in match_stats:
            return None

        player_stats = match_stats[b"match_player_stats"][match_id]
        players = player_stats.values()
        participants = []
        for player in players:
            if player is None:
                continue
            nickname = (
                (player[b"nickname"].decode()).split("]")[1]
                if "]" in player[b"nickname"].decode()
                else player[b"nickname"].decode()
            )
            player_data = {
                "account_id": int(player[b"account_id"].decode()),
                "nickname": nickname,
                "team": int(player[b"team"].decode()),
                "hero_id": int(player[b"hero_id"].decode()),
                "hero": player[b"cli_name"].decode(),
                "alt_avatar": player[b"alt_avatar_name"].decode(),
                "seconds": int(player[b"secs"].decode()),
                "disconnects": int(player[b"discos"].decode()),
                "kicked": int(player[b"kicked"].decode()),
                "concede_votes": int(player[b"concedevotes"].decode()),
            }
            participants.append(player_data)

        match_data = {
            "retrieved": True,
            "match_id": match_id,
            "match_name": match_name,
            "timestamp": timestamp,
            "length": length,
            "server_id": server_id,
            "server_name": server_name,
            "version": version,
            "map": map_name,
            "game_mode": game_mode,
            "url": url,
            "s3_url": s3_url,
            "winning_team": winning_team,
            "participants": participants,
        }
        return match_data

    @staticmethod
    async def insert_match(match_id):
        collection = CLIENT[rctbot.config.MONGO_DATABASE_NAME][rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        match_id = int(match_id)
        if (await collection.find_one({"match_id": match_id})) is None:
            result = await collection.insert_one(
                {"retrieved": False, "counted": False, "watched": False, "match_id": match_id}
            )
            if result.acknowledged:
                return f"Inserted {match_id}."
            return f"Could not insert {match_id}."
        else:
            return f"Match ID {match_id} already inserted!"

    @staticmethod
    async def update_match(match_id, match_data: dict):
        "Update match data for exisitng match ID."
        match_id = int(match_id)
        # TODO: This branch could probably go
        # print(match_id, match_data)
        if not match_data or "match_id" not in match_data or match_id != match_data["match_id"]:
            return "Match ID does not match match data! You are not allowed to change match ID."
        collection = CLIENT[rctbot.config.MONGO_DATABASE_NAME][rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        match = await collection.find_one({"match_id": match_id})
        if match is None:
            return f"{match_id} doesn't exist!"
        else:
            result = await collection.update_one({"match_id": match_id}, {"$set": match_data})
            if result.acknowledged:
                return f"Updated {match_id}."
            return f"Failed to update {match_id}!"


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
