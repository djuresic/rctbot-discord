#!/usr/bin/env python

"""
RCTBot A simple Discord bot with some Heroes of Newerth integration.
Copyright (C) 2020  Danijel Jurešić

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# TODO: Configuration variables for emojis and URLs.

from datetime import datetime, timezone

import discord
from dotenv import load_dotenv

import rctbot
from rctbot.core import checks


# bot = commands.AutoShardedBot(
#     command_prefix=["!", "."],
#     description=BOT_DESCRIPTION,
#     shard_count=3,
#     shard_ids=[0, 1, 2],
# )


if __name__ == "__main__":
    load_dotenv()
    bot = rctbot.get_bot()

    @bot.command()
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def dev_permission_test(ctx):
        await ctx.send("{.mention} You do have permission.".format(ctx.message.author))

    @bot.command(name="load", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _load(ctx, module: str):
        """Loads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
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
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _unload(ctx, module: str):
        """Unloads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
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
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _reload(ctx, module: str):
        """Reloads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
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
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _loaded(ctx):
        """Lists loaded modules."""
        message = []
        for directory in rctbot.config.EXTENSIONS_DIRECTORIES:
            loaded = ", ".join(
                sorted(
                    [
                        extension.split(f"{directory}.")[1]
                        for extension in rctbot.config.LOADED_EXTENSIONS
                        if f"{directory}." in extension
                    ]
                )
            )
            message.append(f"Loaded modules from {directory}: {loaded}")
        await ctx.send("\n".join(message))

    @bot.command(name="unloaded", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _unloaded(ctx):
        """Lists unloaded modules."""
        message = []
        for directory in rctbot.config.EXTENSIONS_DIRECTORIES:
            unloaded = ", ".join(
                sorted(
                    [
                        extension.split(f"{directory}.")[1]
                        for extension in rctbot.config.STARTUP_EXTENSIONS
                        if extension not in rctbot.config.LOADED_EXTENSIONS and f"{directory}." in extension
                    ]
                )
            )
            message.append(f"Unloaded modules from {directory}: {unloaded}")
        await ctx.send("\n".join(message))

    @bot.command(aliases=["info", "license"])
    async def about(ctx):
        repository_url = "https://github.com/djuresic/rctbot-discord"
        description = (
            "A simple Discord bot with some Heroes of Newerth integration. Primarily intended for"
            " use by Retail Canididate Testers, Heroes of Newerth volunteer community position."
            "\n\nCopyright © 2020 Danijel Jurešić"
            "\n\nThis program is free software: you can redistribute it and/or modify"
            " it under the terms of the GNU Affero General Public License as published"
            " by the Free Software Foundation, either version 3 of the License, or"
            " (at your option) any later version."
            "\n\nThis program is distributed in the hope that it will be useful,"
            " but WITHOUT ANY WARRANTY; without even the implied warranty of"
            " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the"
            " GNU Affero General Public License for more details."
            "\n\nYou should have received a copy of the GNU Affero General Public License"
            " along with this program. If not, see <https://www.gnu.org/licenses/>."
        )
        embed = discord.Embed(
            title="RCTBot", type="rich", description=description, color=0x663366, timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=bot.user.name, icon_url=bot.user.avatar_url)
        embed.add_field(name="Version", value=bot.version, inline=True)
        resources = f"{rctbot.config.EMOJI_GITHUB} [GitHub]({repository_url} 'GitHub Repository')"
        embed.add_field(name="Resources", value=resources, inline=True)

        embed.set_footer(
            text="<> with <3 by Lightwalker.", icon_url="https://i.imgur.com/z0auNqP.png",
        )
        # https://i.imgur.com/q8KmQtw.png HoN logo
        embed.set_thumbnail(url="https://www.gnu.org/graphics/agplv3-with-text-162x68.png")
        await ctx.send(embed=embed)

    @bot.event
    async def on_ready():
        print(
            "{0} ({0.id}) reporting for duty from {1}! All shall respect the law that is my {2}!".format(
                bot.user, bot.platform, rctbot.config.CONFIG_FILE
            )
        )
        watching = discord.Activity(name="Heroes of Newerth", type=discord.ActivityType.watching)
        # streaming = discord.Streaming(platform="Twitch", name="Heroes of Newerth", game="Heroes of Newerth", url="https://www.twitch.tv/", twitch_name="")
        await bot.change_presence(activity=watching, status=discord.Status.dnd, afk=False)
        print("------")

    @bot.event
    async def on_message(message):
        # ctx = await bot.get_context(message)
        await bot.process_commands(message)

    bot.run()

