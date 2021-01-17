from datetime import datetime, timezone

import discord
from discord.ext import commands

import rctbot.config
from rctbot.core import checks

# TODO: Remake this...
class Extensions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="load", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _load(self, ctx, module: str):
        """Loads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
            if item.endswith(f".{module}"):
                extension = item
                break
            else:
                extension = "youredoingitwrongagainsmh"
        try:
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send("{}: {}".format(type(e).__name__, e))
        else:
            await ctx.send(f"Loaded {extension} \N{OK HAND SIGN}")

    @commands.command(name="unload", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _unload(self, ctx, module: str):
        """Unloads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
            if item.endswith(f".{module}"):
                extension = item
                break
            else:
                extension = "youredoingitwrongagainsmh"
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.send("{}: {}".format(type(e).__name__, e))
        else:
            await ctx.send(f"Unloaded {extension} \N{OK HAND SIGN}")

    @commands.command(name="reload", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _reload(self, ctx, module: str):
        """Reloads a module."""
        for item in rctbot.config.STARTUP_EXTENSIONS:
            if item.endswith(f".{module}"):
                extension = item
                break
            else:
                extension = "youredoingitwrongagainsmh"
        try:
            self.bot.reload_extension(extension)
        except Exception as e:
            await ctx.send("{}: {}".format(type(e).__name__, e))
        else:
            await ctx.send(f"Reloaded {extension} \N{OK HAND SIGN}")

    @commands.command(name="loaded", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _loaded(self, ctx):
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

    @commands.command(name="unloaded", hidden=True)
    @checks.in_whitelist(rctbot.config.DISCORD_WHITELIST_IDS)
    async def _unloaded(self, ctx):
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

    @commands.command(aliases=["info", "license"])
    async def about(self, ctx):
        description = (
            "A Discord bot with Heroes of Newerth integration. Primarily intended for"
            " use by Retail Canididate Testers, Heroes of Newerth volunteer community position."
            "\n\nCopyright © 2020–2021 Danijel Jurešić"
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
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.add_field(name="Version", value=self.bot.version, inline=True)
        resources = f"{rctbot.config.EMOJI_GITHUB} [GitHub]({self.bot.repository_url} 'GitHub Repository')"
        embed.add_field(name="Resources", value=resources, inline=True)

        embed.set_footer(
            text="<> with <3 by Lightwalker.", icon_url="https://i.imgur.com/z0auNqP.png",
        )
        # https://i.imgur.com/q8KmQtw.png HoN logo
        embed.set_thumbnail(url="https://www.gnu.org/graphics/agplv3-with-text-162x68.png")
        await ctx.send(embed=embed)


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(Extensions(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
