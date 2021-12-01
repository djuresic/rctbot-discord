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
                clients_dict = {
                    "w_32": {"name": "Windows", "os": "w", "bit_64": False},
                    "w_64": {"name": "Windows (64-bit)", "os": "w", "bit_64": True},
                    "m": {"name": "macOS", "os": "m", "bit_64": True},
                    "l": {"name": "Linux", "os": "l", "bit_64": False},
                }

                ms = Client(masterserver, session=session)
                for k, v in clients_dict.items():
                    try:
                        clients_dict[k]["version"] = await ms.latest_client_version(v["os"], bit_64=v["bit_64"])
                    except KeyError:
                        continue

                # Get Windows client build date from hon.exe modified date.
                # Reference: https://github.com/ElementUser/Heroes-of-Newerth/blob/master/scripts/get_all_hon_patch_modified_dates/modified_date_script.py
                # Tested with 0.30.221, build date 10 August 2020, 08:07:02 AM +0800 UTC

                async def get_zip_binary_response_content(client_os_letter: str, version: str, bit_64=False) -> bytes:
                    os_ = f"{client_os_letter}{ms.client_os[masterserver]}"
                    if not bit_64 or (bit_64 and client_os_letter == "l"):
                        url = "http://dl.heroesofnewerth.com/{os}/{arch}/{version}/{file}.zip"
                        arch = {"w": "i686", "m": "universal", "l": "x86-biarch"}[client_os_letter]
                        file_ = {"w": "hon.exe", "m": "manifest.xml", "l": "manifest.xml"}[client_os_letter]
                    else:
                        url = "http://cdn.naeu.patch.heroesofnewerth.com/{os}/{arch}/{version}/{file}.zip"
                        arch = {"w": "x86_64", "m": "universal-64"}[client_os_letter]
                        file_ = {"w": "hon_x64.exe", "m": "manifest.xml"}[client_os_letter]
                    resp = await session.get(url.format(os=os_, arch=arch, version=version, file=file_))
                    return await resp.read()

                def get_build_datetime_from_zip(binary_response_content: bytes) -> datetime:
                    with zipfile.ZipFile(BytesIO(binary_response_content), "r") as zip_file:
                        for hon_file in zip_file.filelist:
                            # Assuming DST is no longer in use and clocks do not change in Shanghai, China.
                            shanghai = timezone(timedelta(hours=8.0))
                            return datetime(*hon_file.date_time, tzinfo=shanghai).astimezone(timezone.utc)

                loop = asyncio.get_running_loop()

                for k, v in clients_dict.items():
                    if "version" not in v:
                        continue
                    zip_bytes = await get_zip_binary_response_content(v["os"], v["version"], bit_64=v["bit_64"])
                    clients_dict[k]["datetime"] = await loop.run_in_executor(
                        None, get_build_datetime_from_zip, zip_bytes
                    )

            embed = discord.Embed(
                title=ms.client_name,
                type="rich",
                description="Client Version & Build Information",
                color=ms.color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            for item in clients_dict.values():
                if "version" not in item:
                    continue
                embed.add_field(
                    name=item["name"],
                    value=(
                        f'Version: {item["version"]}'
                        f'\nBuild date: {item["datetime"].strftime("%d %b %Y")}'
                        f'\nBuild time: {item["datetime"].strftime("%I:%M:%S %p")}'
                    ),
                    inline=True,
                )
            embed.set_footer(
                text="Yes honey. All build times are in UTC.",
                icon_url="https://i.imgur.com/q8KmQtw.png",
            )

            await ctx.send(embed=embed)
