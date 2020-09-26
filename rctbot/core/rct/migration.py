import random
from datetime import datetime, timezone

import aiohttp

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.hon.masterserver import Client


class DatabaseManager:
    def __init__(self, session=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

        # Database
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
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
