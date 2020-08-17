# from discord.ext import commands

import rctbot.config


async def record_usage(origin_class, ctx):
    print(ctx.author, ctx.author.id, "used", ctx.command, "at", ctx.message.created_at)


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
