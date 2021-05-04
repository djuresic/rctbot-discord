from __future__ import annotations

import math
import collections
from typing import Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

import rctbot.config
from rctbot.core.rct.models import ActivityRank
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.hon.portal import VPClient


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
    artificial: float = 5.5
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
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_bugs = self.db[rctbot.config.MONGO_TESTING_BUGS_COLLECTION_NAME]
        self.testing_cycles = self.db[rctbot.config.MONGO_TESTING_CYCLES_COLLECTION_NAME]
        self.testing_extra = self.db[rctbot.config.MONGO_TESTING_EXTRA_COLLECTION_NAME]

        self.values = CycleValues()

        # Match processor
        # self.mp = MatchProcessor()

    async def archive_cycle(self, version):
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
        bugs = await (self.testing_bugs.find({})).to_list(length=None)
        extra = await (self.testing_extra.find({})).to_list(length=None)
        if 0 in (len(games), len(testers)):
            # TODO: Result
            print("len games testers 0")
            return False

        start = datetime.fromtimestamp(games[0]["timestamp"])
        if not (last_cycle := await self.testing_cycles.find_one({}, {"_id": 1}, sort=list({"_id": -1}.items()))):
            id_ = 1
        else:
            id_ = last_cycle["_id"] + 1
        result = await self.testing_cycles.insert_one(
            {
                "_id": id_,
                "version": version,
                "games": games,
                "bugs": bugs,
                "extra": extra,
                "participants": testers,
                "start": start,
                "end": datetime.now(timezone.utc),
                "artificial": CycleValues.artificial,
            }
        )
        if not result.acknowledged:
            return False
        result_g = await self.testing_games.delete_many({})
        result_b = await self.testing_bugs.delete_many({})
        result_e = await self.testing_extra.delete_many({})
        return result_g.acknowledged and result_b.acknowledged and result_e.acknowledged

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

        # Using set comprehension to remove duplicates. Account ID is from the testing database.
        account_ids = {entry["account_id"] for entry in participants}
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
        bugs_docs = await (self.testing_bugs.find({})).to_list(length=None)
        reporters = [document["reporter"]["testing_account_id"] for document in bugs_docs]
        reporters = collections.Counter(reporters)

        acknowledged = 0
        async for tester in self.testers.find({}, {"_id": 0, "testing_account_id": 1}):
            bugs = reporters.get(tester["testing_account_id"], 0)
            result = await self.testers.update_one(
                {"testing_account_id": tester["testing_account_id"]}, {"$set": {"bugs": bugs}},
            )
            if result.acknowledged:
                acknowledged += 1

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
                continue
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
        """Update tokens for all testers.

        Updates both tokens and extra fields in the database.
        """
        extra_docs = await (self.testing_extra.find({})).to_list(length=None)
        extra = collections.Counter()
        for document in extra_docs:
            extra.update({document["tester"]["account_id"]: document["amount"]})

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
                + (extra[tester["account_id"]])
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
        return "Could not update perks status!"

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
