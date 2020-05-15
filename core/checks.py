import discord
from discord.ext import commands

import core.perseverance
import core.config as config
import core.errors

# Needs an update


def database_ready():
    # ctx mandatory positional argument
    async def database_ready_check(ctx):
        if not config.DATABASE_READY:
            raise core.errors.DatabaseNotReady("Database is not ready!")
        return True
        # return config.DATABASE_READY

    return commands.check(database_ready_check)


def in_whitelist(whitelist):
    async def in_whitelist_check(ctx):
        if ctx.author.id not in whitelist:
            raise core.errors.NotInWhiteList("You're not on the whitelist!")
        return True

    return commands.check(in_whitelist_check)


def is_tester():
    async def is_tester_check(ctx):
        if not config.DATABASE_READY:
            raise core.errors.DatabaseNotReady("Database is not ready!")

        found_id = False
        verified = False

        def verify(selected):
            return selected.lower() in ("tester", "senior", "staff")

        for x in config.LIST_OF_LISTS:
            if x[32] == str(ctx.author.id):
                found_id = True
                verified = verify(x[0])
                break

        return found_id and verified

    return commands.check(is_tester_check)


def is_senior():
    async def is_senior_check(ctx):
        if not config.DATABASE_READY:
            raise core.errors.DatabaseNotReady("Database is not ready!")

        found_id = False
        verified = False

        def verify(selected):
            return selected.lower() in ("senior", "staff")

        for x in config.LIST_OF_LISTS:
            if x[32] == str(ctx.author.id):
                found_id = True
                verified = verify(x[0])
                break

        return found_id and verified

    return commands.check(is_senior_check)


def is_authenticated():  # Expensive, keeping for now though
    async def is_authenticated_check(ctx):
        for masterserver in ["ac", "rc", "tc"]:
            if not config.HON_MASTERSERVER_INFO[masterserver]["authenticated"]:
                raise core.errors.NotMasterserverAuthenticated(
                    f"{config.HON_MASTERSERVER_INFO[masterserver]['short']} not authenticated! Please inform a Senior Tester."
                )
        return True

    return commands.check(is_authenticated_check)


def guild_only():  # TO DO: this annoyance
    async def guild_only_check(ctx):
        if ctx.message.guild is None:
            raise core.errors.GuildOnlyCommand("Not allowed in Direct Message!")
        return True

    return commands.check(guild_only_check)


def setup(bot):
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
