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

import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

from extensions.checks import in_whitelist
import extensions.forums as forums

import config  # What have I done...

# dynamic
FETCH_SHEET_PASS = 0

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
    with os.scandir("extensions") as it:
        for entry in it:
            if entry.name.endswith(".py") and entry.is_file():
                extension_name = entry.name.strip(".py")
                if extension_name not in config.BOT_DISABLED_EXTENSIONS:
                    config.BOT_STARTUP_EXTENSIONS.append(f"extensions.{extension_name}")

    for extension in config.BOT_STARTUP_EXTENSIONS:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = "{}: {}".format(type(e).__name__, e)
            print("Failed to load extension {}\n{}".format(extension, exc))

    print("Loaded extensions: {}".format(", ".join(config.BOT_LOADED_EXTENSIONS)))


@bot.command()
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def dev_permission_test(ctx):
    await ctx.send("{.mention} You do have permission.".format(ctx.message.author))


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
async def on_message(message):
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


async def fetch_sheet():
    await bot.wait_until_ready()
    global FETCH_SHEET_PASS

    def get_creds():
        return ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES
        )

    gspread_client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

    count_pass = 0
    # while not bot.is_closed:
    while True:
        gspread_client = (
            await gspread_client_manager.authorize()
        )  # "This is fine." (It's actually fine, for real. gspread_asyncio has a cache.)

        # spreadsheet and worksheets
        rct_spreadsheet = await gspread_client.open("RCT Spreadsheet")
        rewards_worksheet = await rct_spreadsheet.worksheet("RCT Players and Rewards")
        trivia_worksheet = await rct_spreadsheet.worksheet("trivia_sheet")
        settings_worksheet = await rct_spreadsheet.worksheet("Settings")
        games_worksheet = await rct_spreadsheet.worksheet("Games")

        # update dynamic
        config.LIST_OF_LISTS = await rewards_worksheet.get_all_values()
        config.LIST_OF_LISTS_TRIVIA = await trivia_worksheet.get_all_values()
        config.SETTINGS = await settings_worksheet.col_values(2)
        config.PLAYER_SLASH_HERO = await games_worksheet.col_values(13)

        config.DATABASE_READY = True

        count_pass += 1
        FETCH_SHEET_PASS = count_pass
        if count_pass <= 2:
            print("fetch_sheet pass {0}".format(FETCH_SHEET_PASS))

        await asyncio.sleep(60)


bot.remove_command("help")

bot.loop.create_task(fetch_sheet())

bot.run(config.DISCORD_TOKEN)
