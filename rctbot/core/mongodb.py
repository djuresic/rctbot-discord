import pymongo
import motor.motor_asyncio


import rctbot.config


# TODO: Yeah, this...

CLIENT = motor.motor_asyncio.AsyncIOMotorClient(rctbot.config.MONGO_HOST_PARAMETER)


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
