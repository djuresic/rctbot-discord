import asyncio
import zipfile
from io import BytesIO
from datetime import datetime, timezone, timedelta
from time import strftime, gmtime

import aiohttp
import discord
from discord.ext import commands

import rctbot.config
from rctbot.core import checks
from rctbot.core.rct import TestingNotes
from rctbot.hon.masterserver import Client


class Playtesting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_tester()
    async def notes(self, ctx):
        """Current testing notes."""
        log_channel = self.bot.get_channel(rctbot.config.DISCORD_NOTES_CHANNEL_ID)
        notes_url = await TestingNotes().create(ctx.author.id)
        await ctx.author.send(f"Current Testing Notes: {notes_url}")
        await log_channel.send(
            f'({strftime("%a, %d %b %Y, %H:%M:%S %Z", gmtime())})'
            f" {ctx.author.mention} received Testing Notes with the URL: `{notes_url}`"
        )

    @commands.command()
    @checks.is_tester()
    async def version(self, ctx, masterserver: str = "rc"):
        """Checks all client versions and build date information for
        masterserver.
        
        Defaults to RCT masterserver.
        """

        async with ctx.message.channel.typing():

            async with aiohttp.ClientSession() as session:
                ms = Client(masterserver, session=session)
                w_version = await ms.latest_client_version("windows")
                m_version = await ms.latest_client_version("mac")
                l_version = await ms.latest_client_version("linux")

                # Get Windows client build date from hon.exe modified date.
                # Reference: https://github.com/ElementUser/Heroes-of-Newerth/blob/master/scripts/get_all_hon_patch_modified_dates/modified_date_script.py
                # Tested with 0.30.221, build date 10 August 2020, 08:07:02 AM +0800 UTC

                async def get_zip_binary_response_content(client_os_letter: str, version: str) -> bytes:
                    url = "http://dl.heroesofnewerth.com/{os}/{arch}/{version}/{file}.zip"
                    os_ = f"{client_os_letter}{ms.client_os[masterserver]}"
                    arch = {"w": "i686", "m": "universal", "l": "x86-biarch"}[client_os_letter]
                    file_ = {"w": "hon.exe", "m": "manifest.xml", "l": "manifest.xml"}[client_os_letter]
                    resp = await session.get(url.format(os=os_, arch=arch, version=version, file=file_))
                    return await resp.read()

                def get_build_datetime_from_zip(binary_response_content: bytes) -> datetime:
                    with zipfile.ZipFile(BytesIO(binary_response_content), "r") as zip_file:
                        for hon_file in zip_file.filelist:
                            # Assuming DST is no longer in use and clocks do not change in Shanghai, China.
                            shanghai = timezone(timedelta(hours=8.0))
                            return datetime(*hon_file.date_time, tzinfo=shanghai).astimezone(timezone.utc)

                loop = asyncio.get_running_loop()

                w_bytes = await get_zip_binary_response_content("w", w_version)
                w_build_datetime = await loop.run_in_executor(None, get_build_datetime_from_zip, w_bytes)
                m_bytes = await get_zip_binary_response_content("m", m_version)
                m_build_datetime = await loop.run_in_executor(None, get_build_datetime_from_zip, m_bytes)
                l_bytes = await get_zip_binary_response_content("l", l_version)
                l_build_datetime = await loop.run_in_executor(None, get_build_datetime_from_zip, l_bytes)

            embed = discord.Embed(
                title=ms.client_name,
                type="rich",
                description="Client Version & Build Information",
                color=ms.color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.add_field(
                name="Windows",
                value=(
                    f"Version: {w_version}"
                    f'\nBuild date: {w_build_datetime.strftime("%d %b %Y")}'
                    f'\nBuild time: {w_build_datetime.strftime("%I:%M:%S %p")}'
                ),
                inline=True,
            )
            embed.add_field(
                name="macOS",
                value=(
                    f"Version: {m_version}"
                    f'\nBuild date: {m_build_datetime.strftime("%d %b %Y")}'
                    f'\nBuild time: {m_build_datetime.strftime("%I:%M:%S %p")}'
                ),
                inline=True,
            )
            embed.add_field(
                name="Linux",
                value=(
                    f"Version: {l_version}"
                    f'\nBuild date: {l_build_datetime.strftime("%d %b %Y")}'
                    f'\nBuild time: {l_build_datetime.strftime("%I:%M:%S %p")}'
                ),
                inline=True,
            )
            embed.set_footer(
                text="Yes honey. All build times are in UTC.", icon_url="https://i.imgur.com/q8KmQtw.png",
            )

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Playtesting(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Playtesting(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
