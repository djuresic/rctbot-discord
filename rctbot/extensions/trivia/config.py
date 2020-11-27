from rctbot.core.driver import DatabaseHandler, AsyncDatabaseHandler


class TriviaConfig:

    _db = DatabaseHandler.client["Trivia"]
    _collection = _db["CONFIG"]

    db = AsyncDatabaseHandler.client["Trivia"]
    collection = db["CONFIG"]
    document = {}

    @staticmethod
    def load() -> None:
        if (document := TriviaConfig._collection.find_one({})) is None:
            raise Exception("No configuration found!")
        TriviaConfig.document = document

    @staticmethod
    async def get(key: str):
        key = key.lower()
        return (await TriviaConfig.collection.find_one({}, {"_id": 0, key: 1}))[key]

    @staticmethod
    # TODO: This should allow **kwargs.
    async def set(key: str, value) -> None:
        await TriviaConfig.collection.update_one({}, {"$set": {key.lower(): value}})
        if (document := await TriviaConfig.collection.find_one({})) is None:
            raise Exception("No configuration found!")
        TriviaConfig.document = document


TriviaConfig.load()
