import os

import pymongo
import motor.motor_asyncio

import rctbot.config


# This is passed as the host parameter. It can be a simple hostname, a MongoDB URI, or a list of hostnames or URIs.
# Ensure that any option parameters are URL encoded. NOTE: from urllib.parse import quote_plus
# NOTE: For MongoDB Atlas Cloud, database name variable must have the same database name from the connection URI.
# localhost:27017 is the default host parameter.
MONGODB_URI = os.getenv("MONGODB_URI", "localhost:27017")


class DatabaseHandler:
    client = pymongo.MongoClient(MONGODB_URI)


class AsyncDatabaseHandler:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
