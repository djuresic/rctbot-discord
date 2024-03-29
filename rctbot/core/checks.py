from discord.ext import commands

import rctbot.config
import rctbot.core.errors
from rctbot.core.driver import AsyncDatabaseHandler

# TODO: Rename to in_allowlist
def in_whitelist(whitelist):
    async def in_whitelist_check(ctx):
        if ctx.author.id not in whitelist:
            raise rctbot.core.errors.NotInWhiteList("You're not on the allowlist!")
        return True

    return commands.check(in_whitelist_check)


def is_tester():
    async def is_tester_check(ctx):
        user = await AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME][
            rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME
        ].find_one({"discord_id": ctx.author.id}, {"enabled": 1, "role": 1})
        if not user or not user["enabled"]:
            raise rctbot.core.errors.NotATester("You are not a tester!")
        return user["role"].lower() in ("tester", "senior", "staff")

    return commands.check(is_tester_check)


def is_senior():
    async def is_senior_check(ctx):
        user = await AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME][
            rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME
        ].find_one({"discord_id": ctx.author.id}, {"enabled": 1, "role": 1})
        if not user or not user["enabled"]:
            raise rctbot.core.errors.NotATester("You are not a tester!")
        return user["role"].lower() in ("senior", "staff")

    return commands.check(is_senior_check)


def guild_is_rct():
    async def guild_is_rct_check(ctx):
        if ctx.message.guild is None or ctx.message.guild.id != rctbot.config.DISCORD_RCT_GUILD_ID:
            raise rctbot.core.errors.NotRCTGuild("Not allowed outside the official RCT Discord!")
        return True

    return commands.check(guild_is_rct_check)


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
