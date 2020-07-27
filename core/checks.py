from discord.ext import commands

import config
import core.errors
from core.mongodb import CLIENT


def in_whitelist(whitelist):
    async def in_whitelist_check(ctx):
        if ctx.author.id not in whitelist:
            raise core.errors.NotInWhiteList("You're not on the whitelist!")
        return True

    return commands.check(in_whitelist_check)


def is_tester():
    async def is_tester_check(ctx):
        user = await CLIENT[config.MONGO_DATABASE_NAME][
            config.MONGO_TESTING_PLAYERS_COLLECTION_NAME
        ].find_one({"discord_id": ctx.author.id}, {"enabled": 1, "role": 1})
        if not user or not user["enabled"]:
            raise core.errors.NotATester("You are not a tester!")
        return user["role"].lower() in ("tester", "senior", "staff")

    return commands.check(is_tester_check)


def is_senior():
    async def is_senior_check(ctx):
        user = await CLIENT[config.MONGO_DATABASE_NAME][
            config.MONGO_TESTING_PLAYERS_COLLECTION_NAME
        ].find_one({"discord_id": ctx.author.id}, {"enabled": 1, "role": 1})
        if not user or not user["enabled"]:
            raise core.errors.NotATester("You are not a tester!")
        return user["role"].lower() in ("senior", "staff")

    return commands.check(is_senior_check)


def guild_is_rct():
    async def guild_is_rct_check(ctx):
        if (
            ctx.message.guild is None
            or ctx.message.guild.id != config.DISCORD_RCT_GUILD_ID
        ):
            raise core.errors.NotRCTGuild(
                "Not allowed outside the official RCT Discord!"
            )
        return True

    return commands.check(guild_is_rct_check)


# pylint: disable=unused-argument
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
