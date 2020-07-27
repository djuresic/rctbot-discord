import pymongo
import motor.motor_asyncio


import config


# TODO: Yeah, this...

CLIENT = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_HOST_PARAMETER)


# pylint: disable=unused-argument
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
