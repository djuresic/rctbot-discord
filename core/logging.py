# from discord.ext import commands

import config

# TODO: Activate in discord.py 1.4


async def record_usage(ctx):
    print(ctx.author, "used", ctx.command, "at", ctx.message.created_at)


# pylint: disable=unused-argument
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
