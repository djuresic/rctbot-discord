import aiohttp

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.hon.masterserver import Client

# TODO: Change static methods.


class MatchManipulator:
    def __init__(self, masterserver="rc", session=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.client = Client(masterserver, session=self.session)
        self.db_client = AsyncDatabaseHandler.client
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
        collection = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME][
            rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME
        ]
        match_id = int(match_id)
        if (await collection.find_one({"match_id": match_id})) is None:
            return f"Match ID {match_id} already inserted!"
        result = await collection.insert_one(
            {"retrieved": False, "counted": False, "watched": False, "match_id": match_id}
        )
        if not result.acknowledged:
            return f"Could not insert {match_id}."
        return f"Inserted {match_id}."

    @staticmethod
    async def update_match(match_id, match_data: dict):
        "Update match data for exisitng match ID."
        match_id = int(match_id)
        # TODO: This branch could probably go
        # print(match_id, match_data)
        if not match_data or "match_id" not in match_data or match_id != match_data["match_id"]:
            return "Match ID does not match match data! You are not allowed to change match ID."
        collection = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME][
            rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME
        ]
        match = await collection.find_one({"match_id": match_id})
        if match is None:
            return f"{match_id} doesn't exist!"

        result = await collection.update_one({"match_id": match_id}, {"$set": match_data})
        if result.acknowledged:
            return f"Updated {match_id}."
        return f"Failed to update {match_id}!"
