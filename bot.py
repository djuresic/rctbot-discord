#!/usr/bin/env python

"""
RCTBot

Copyright (c) 2020 Danijel Jurešić

Licensed under the MIT License.
"""

import os
import platform
from time import time, gmtime, strftime

import asyncio
import aiohttp
import discord
from discord.ext import commands

import core.perseverance
import core.config as config
from core.checks import in_whitelist

import hon.forums as forums

winter_solstice = """Some say the world will end in fire,
Some say in ice.
From what I’ve tasted of desire
I hold with those who favor fire.
But if it had to perish twice,
I think I know enough of hate
To say that for destruction ice
Is also great
And would suffice.

- Robert Frost"""


bot = commands.Bot(command_prefix=["!", "."], description=winter_solstice)


if __name__ == "__main__":
    for directory in core.perseverance.EXTENSIONS_DIRECTORIES:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.name.endswith(".py") and entry.is_file():
                    module = entry.name[:-3]
                    if module not in core.perseverance.DISABLED_EXTENSIONS:
                        core.perseverance.STARTUP_EXTENSIONS.append(
                            f"{directory}.{module}"
                        )

    for extension in core.perseverance.STARTUP_EXTENSIONS:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = "{}: {}".format(type(e).__name__, e)
            print(f"Failed to load {extension}\n{exc}")

    print(
        "Loaded modules: {}".format(
            ", ".join(
                [
                    extension.split(".")[-1]
                    for extension in core.perseverance.LOADED_EXTENSIONS
                ]
            )
        )
    )


@bot.command()
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def dev_permission_test(ctx):
    await ctx.send("{.mention} You do have permission.".format(ctx.message.author))


@bot.command(name="load", hidden=True)
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def _load(ctx, module: str):
    """Loads a module."""
    for item in core.perseverance.STARTUP_EXTENSIONS:
        if item.endswith(f".{module}"):
            extension = item
            break
        else:
            extension = "youredoingitwrongagainsmh"
    try:
        bot.load_extension(extension)
    except Exception as e:
        await ctx.send("{}: {}".format(type(e).__name__, e))
    else:
        await ctx.send(f"Loaded {extension} \N{OK HAND SIGN}")


@bot.command(name="unload", hidden=True)
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def _unload(ctx, module: str):
    """Unloads a module."""
    for item in core.perseverance.STARTUP_EXTENSIONS:
        if item.endswith(f".{module}"):
            extension = item
            break
        else:
            extension = "youredoingitwrongagainsmh"
    try:
        bot.unload_extension(extension)
    except Exception as e:
        await ctx.send("{}: {}".format(type(e).__name__, e))
    else:
        await ctx.send(f"Unloaded {extension} \N{OK HAND SIGN}")


@bot.command(name="reload", hidden=True)
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def _reload(ctx, module: str):
    """Reloads a module."""
    for item in core.perseverance.STARTUP_EXTENSIONS:
        if item.endswith(f".{module}"):
            extension = item
            break
        else:
            extension = "youredoingitwrongagainsmh"
    try:
        bot.reload_extension(extension)
    except Exception as e:
        await ctx.send("{}: {}".format(type(e).__name__, e))
    else:
        await ctx.send(f"Reloaded {extension} \N{OK HAND SIGN}")


@bot.command(name="loaded", hidden=True)
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def _loaded(ctx):
    """Lists loaded modules."""
    message = []
    for directory in core.perseverance.EXTENSIONS_DIRECTORIES:
        loaded = ", ".join(
            sorted(
                [
                    extension.split(f"{directory}.")[1]
                    for extension in core.perseverance.LOADED_EXTENSIONS
                    if f"{directory}." in extension
                ]
            )
        )
        message.append(f"Loaded modules from {directory}: {loaded}")
    await ctx.send("\n".join(message))


@bot.command(name="unloaded", hidden=True)
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def _unloaded(ctx):
    """Lists unloaded modules."""
    message = []
    for directory in core.perseverance.EXTENSIONS_DIRECTORIES:
        unloaded = ", ".join(
            sorted(
                [
                    extension.split(f"{directory}.")[1]
                    for extension in core.perseverance.STARTUP_EXTENSIONS
                    if extension not in core.perseverance.LOADED_EXTENSIONS
                    and f"{directory}." in extension
                ]
            )
        )
        message.append(f"Unloaded modules from {directory}: {unloaded}")
    await ctx.send("\n".join(message))


@bot.event
async def on_ready():
    print(
        "{0} ({0.id}) reporting for duty from {1}! All shall respect the law that is my {2}!".format(
            bot.user, platform.platform(), config.CONFIG_FILE
        )
    )
    watching = discord.Activity(
        name="Heroes of Newerth", type=discord.ActivityType.watching
    )
    # streaming = discord.Streaming(platform="Twitch", name="Heroes of Newerth", game="Heroes of Newerth", url="https://www.twitch.tv/", twitch_name="")
    await bot.change_presence(activity=watching, status=discord.Status.dnd, afk=False)
    print("------")


@bot.event
async def on_message(message):  # Move to a cog
    ctx = await bot.get_context(message)

    if message.guild is None and ctx.valid:  # TO DO: with guild_only and dm_allowed
        # print([f.__name__ for f in ctx.command.checks])
        if ctx.command.name not in config.DISCORD_DM_COMMANDS:
            print(
                "{0.name}#{0.discriminator} ({0.id}) tried to invoke {1} in Direct Message: {2}".format(
                    message.author, ctx.command, message.content
                )
            )
            return

    # if ctx.valid:
    #     if ctx.command in config.DISCORD_DM_COMMANDS and message.author.id not in config.DISCORD_WHITELIST_IDS:
    #         await message.author.send("You do not have permission.")
    #     else:
    #         await bot.process_commands(message)
    # else:
    #     pass

    if message.channel.id == config.DISCORD_ANNOUNCEMENTS_CHANNEL_ID:
        if config.DISCORD_FORUMS_ROLE_ID in message.raw_role_mentions:

            async with aiohttp.ClientSession() as session:

                await forums.login(session)

                content = message.content.split(f"{config.DISCORD_FORUMS_ROLE_ID}>")[
                    1
                ].strip(" ")
                announcement = "{0}\n\n\nMade by: [COLOR=#00cc99]{1.display_name}[/COLOR] ({1.name}#{1.discriminator})".format(
                    content, message.author
                )

                await forums.new_reply(
                    session, config.HON_FORUM_ANNOUNCEMENTS_THREAD_ID, announcement
                )

    await bot.process_commands(message)


bot.remove_command("help")

bot.run(config.DISCORD_TOKEN)
