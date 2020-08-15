from time import strftime, gmtime

import aiohttp
import discord
from discord.ext import commands

import config
from core.checks import is_tester
from hon.masterserver import Client


class Playtesting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_tester()
    async def notes(self, ctx):
        """Current testing notes."""
        author = ctx.author
        log_channel = self.bot.get_channel(config.DISCORD_NOTES_CHANNEL_ID)

        token_generator = f"https://{config.HON_ALT_DOMAIN}/site/create-access-token"
        cat_query = {"discordId": author.id, "password": config.HON_CAT_PASSWORD}

        async with aiohttp.ClientSession() as session:

            async with session.get(token_generator, params=cat_query) as resp:
                token = await resp.text()

        notes_url = f"https://{config.HON_ALT_DOMAIN}/{token}"
        await author.send(f"Current Testing Notes: {notes_url}")
        await log_channel.send(
            f'({strftime("%a, %d %b %Y, %H:%M:%S %Z", gmtime())}) {author.mention} received Testing Notes with the URL: `{notes_url}`'
        )

    @commands.command()
    @is_tester()
    async def version(self, ctx, masterserver: str = "rc"):
        """Check all client versions for <masterserver>. Defaults to RCT masterserver."""

        async with ctx.message.channel.typing():

            async with aiohttp.ClientSession() as session:
                ms = Client(masterserver, session=session)
                w_version = await ms.latest_client_version("windows")
                m_version = await ms.latest_client_version("mac")
                l_version = await ms.latest_client_version("linux")

            embed = discord.Embed(
                title=ms.client_name,
                type="rich",
                description="Client Version",
                color=ms.color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Windows", value=w_version, inline=True)
            embed.add_field(name="macOS", value=m_version, inline=True)
            embed.add_field(name="Linux", value=l_version, inline=True)
            embed.set_footer(
                text="Yes honey.", icon_url="https://i.imgur.com/q8KmQtw.png",
            )

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Playtesting(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Playtesting(bot))
    config.LOADED_EXTENSIONS.remove(__loader__.name)
