import math

import aiohttp
import discord

import config
from core.mongodb import CLIENT

from hon.masterserver import Client
from hon.portal import VPClient

# TODO: Typing. Remove copy pasta code.


class DatabaseManager:
    def __init__(self, session=None):
        self.url = config.HON_VP_URL
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.token = None

        # Database
        self.db = CLIENT[config.MONGO_DATABASE_NAME]
        self.testers = self.db[config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_cycles = self.db[config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

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
        for row in config.LIST_OF_LISTS[2:]:
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
                "ladder": {
                    "games": 0,
                    "bugs": 0,
                    "total_games": 0,
                    "total_bugs": 0,
                    "tokens": 0,
                },
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
                        (
                            await Client("rc", session=session).show_simple_stats(
                                nickname
                            )
                        )[b"account_id"].decode()
                    )
                except:
                    testing_account_id = None
            print(testing_account_id, nickname)
            await self.testers.update_one(
                {"nickname": nickname},
                {"$set": {"testing_account_id": testing_account_id}},
            )


# TODO: Change static methods.


class MatchManipulator:
    def __init__(self, masterserver="rc", session=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.client = Client(masterserver, session=self.session)
        self.db_client = CLIENT
        self.db = self.db_client[config.MONGO_DATABASE_NAME]
        self.testing_games = self.db[config.MONGO_TESTING_GAMES_COLLECTION_NAME]

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
        print(match_stats)

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
        game_mode = summary[b"gamemode"].decode()
        url = summary[b"url"].decode()
        s3_url = summary[b"s3_url"].decode()
        winning_team = summary[b"winning_team"] if b"winning_team" in summary else 0

        if b"match_player_stats" not in match_stats:
            return None

        player_stats = match_stats[b"match_player_stats"][match_id]
        players = player_stats.values()
        participants = []
        for player in players:
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
        collection = CLIENT[config.MONGO_DATABASE_NAME][
            config.MONGO_TESTING_GAMES_COLLECTION_NAME
        ]
        match_id = int(match_id)
        match = await collection.find_one({"match_id": match_id})
        if match is None:
            result = await collection.insert_one(
                {
                    "retrieved": False,
                    "watched": False,
                    "match_id": match_id,
                    "match_name": "some generic name",
                }
            )
        else:
            result = f"{match_id} already exists"
        return print(result)

    @staticmethod
    async def update_match(match_id, match_data: dict):
        "Update match data for exisitng match ID."
        match_id = int(match_id)
        # TODO: This branch could probably go
        if "match_id" not in match_data or match_id != match_data["match_id"]:
            return "Match ID does not match match data! You are not allowed to change match ID."
        collection = CLIENT[config.MONGO_DATABASE_NAME][
            config.MONGO_TESTING_GAMES_COLLECTION_NAME
        ]
        match = await collection.find_one({"match_id": match_id})
        if match is None:
            return print(f"{match_id} doesn't exist")
        else:
            result = await collection.update_one(
                {"match_id": match_id}, {"$set": match_data}
            )
            return print(result)


# TODO: Handle only enabled accounts
# Rename to Cycle
class CycleManager:
    "Interface for managing testing cycles."

    def __init__(self, session=None):
        self.url = config.HON_VP_URL
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.token = None

        # Database
        self.db = CLIENT[config.MONGO_DATABASE_NAME]
        self.testers = self.db[config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_cycles = self.db[config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

        # Tokens per activity:
        self.game = 10
        self.second = 0.003725
        self.ten = 75
        self.twenty = 225
        self.fifty = 750
        self.multiplier = (0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5)
        self.keep = (0, 1, 1, 3, 5, 7, 10, 0)
        self.advance = (0, 3, 5, 8, 10, 12, 0, 0)
        self.artificial = 3.5
        self.bug = 100

        # Match processor
        # self.mp = MatchProcessor()

    # async def __aenter__(self) -> "CycleManager":
    async def __aenter__(self):
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        """Coroutine. Close the session."""
        await self.session.close()

    async def new_cycle(self):
        values = {
            "games": 0,
            "seconds": 0,
            "bugs": 0,
            "tokens": 0,
            "ladder": {
                "games": 0,
                "bugs": 0,
                "total_games": 0,
                "total_bugs": 0,
                "tokens": 0,
            },
            "extra": 0,
        }
        async for document in self.testers.find({}):
            # TODO: Change this to account_id after fetching all IDs.
            bonus_last_cycle = math.floor(
                (document["total_games"] / 50) - document["bonuses_given"]
            )
            values["bonuses_given"] = document["bonuses_given"] + bonus_last_cycle
            await self.testers.update_one(
                {"nickname": document["nickname"]}, {"$set": values}
            )

    async def update_games_and_seconds(self):
        # TODO: This should rely more on MongoDB rather than the application itself.
        participants = []
        async for document in self.testing_games.find({"retrieved": True}):
            participants.extend(document["participants"])

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
        print(players)
        # TODO: Remove players list and do update in the loop instead.
        for player in players:
            await self.testers.update_one(
                {"testing_account_id": player[0]},
                {"$set": {"games": player[1], "seconds": player[2]}},
            )

    async def update_bugs(self):
        # TODO
        pass

    async def update_total(self):
        async for document in self.testers.find({}):
            # TODO: Change this to account_id after fetching all IDs.
            await self.testers.update_one(
                {"nickname": document["nickname"]},
                {
                    "$inc": {
                        "total_games": document["games"],
                        "total_seconds": document["seconds"],
                        "total_bugs": document["bugs"],
                    }
                },
            )

    async def delete_unretrieved(self):
        pass

    async def update_cycle(self):
        # TODO
        pass

    async def update_ranks(self):
        # TODO: Filter in query to return needed only.
        async for tester in self.testers.find({"enabled": True}):
            rank_id = tester["rank_id"]
            games = tester["games"]
            bugs = tester["bugs"]
            # Ignore testers with absence field and Gold and below rank.
            if "absence" in tester and rank_id <= 4:
                pass
            # Unranked < current rank < Legendary
            if 0 < rank_id < 6:
                if (games + bugs) >= self.advance[rank_id]:
                    # TODO: Change to account_id
                    await self.testers.update_one(
                        {"nickname": tester["nickname"]}, {"$inc": {"rank_id": 1}}
                    )
                elif (games + bugs) < self.keep[rank_id]:
                    await self.testers.update_one(
                        {"nickname": tester["nickname"]}, {"$inc": {"rank_id": -1}}
                    )
                else:
                    pass

    async def update_tokens(self):
        async for tester in self.testers.find({}):
            games = tester["games"]
            bonus = math.floor((tester["total_games"] / 50) - tester["bonuses_given"])

            tokens = round(
                (
                    games * self.game
                    + tester["seconds"] * self.second
                    + (self.ten if games >= 10 else 0)
                    + (self.twenty if games >= 20 else 0)
                )
                * (self.multiplier[tester["rank_id"]] + self.artificial)
                + bonus * self.fifty
                + tester["bugs"] * self.bug
                + (tester["extra"])
            )
            await self.testers.update_one(
                {"account_id": tester["account_id"]}, {"$set": {"tokens": tokens}},
            )

    async def distribute_tokens(self):
        "coro Modify tokens using the current values from DB and return tuple (success, error)."
        mod_input = []
        async for tester in self.testers.find(
            {"enabled": True, "tokens": {"$gt": 0}},
            {"nickname": 1, "tokens": 1},
            sort=list({"tokens": -1}.items()),
        ):
            mod_input.append(f'{tester["nickname"]} {tester["tokens"]}')
        async with VPClient() as portal:
            return await portal.mod_tokens(mod_input)


# pylint: disable=unused-argument
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
