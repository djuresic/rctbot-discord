from typing import Tuple, Optional

import asyncio
import discord
import numpy as np
from discord.ext import commands


import rctbot.config
from rctbot.config import Configuration


def _ratio(string1: str, string2: str) -> float:
    m = len(string1) + 1
    n = len(string2) + 1
    A = np.zeros((m, n))

    for i in range(m):
        A[i, 0] = i
    for j in range(n):
        A[0, j] = j

    for i in range(1, m):
        for j in range(1, n):
            if string1[i - 1] == string2[j - 1]:
                A[i, j] = min(A[i - 1, j] + 1, A[i - 1, j - 1], A[i, j - 1] + 1)
            else:
                A[i, j] = min(A[i - 1, j] + 1, A[i - 1, j - 1] + 1, A[i, j - 1] + 1)
    distance = A[m - 1, n - 1]
    return float(max(len(string1), len(string2)) - distance) / max(len(string1), len(string2))


def _highest_ratio(string: str, strings_list: list) -> Tuple[Optional[str], float]:
    ratio = 0.0
    matches = None
    for item in strings_list:
        if (new_ratio := _ratio(string, item)) > ratio:
            ratio = new_ratio
            matches = item
    return matches, ratio


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 782535231332155392  # TODO
        self.banned_domains = ["bit.ly"]
        self.staff_names = Configuration.document["DISCORD"].get("STAFF_NAMES", [])  # TODO: These two should be a dict
        self.staff_ids = Configuration.document["DISCORD"].get("STAFF_IDS", [])
        self.guild_ids = [735493943025860658, 740244988385951884]  # TODO
        self.higher_rt = 0.9
        self.high_rt = 0.87
        self.low_rt = 0.69

    async def _log_impostor(self, member, title: str, description: str = ""):
        moderator = discord.utils.get(member.guild.roles, name="Discord Moderator")
        channel = member.guild.get_channel(self.log_channel_id)
        embed = discord.Embed(title=title, type="rich", description=description, color=0x7289DA,)
        embed.set_author(name=member, icon_url=member.avatar_url)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(moderator.mention, embed=embed)

    @commands.Cog.listener("on_member_update")
    async def kick_username_links(self, before, after):
        if after.display_name != before.display_name:
            display_name = after.display_name.replace(" ", "")
            for domain in self.banned_domains:
                if domain in display_name and "/" in display_name:
                    await after.kick(reason=f"Banned URL in display name: {display_name}")
                    break

    @commands.Cog.listener("on_member_update")
    async def kick_impostors_on_update(self, before, after):
        if (
            not after.id in self.staff_ids
            and after.display_name != before.display_name
            and after.guild.id in self.guild_ids
        ):  # TODO
            display_name = after.display_name.replace(" ", "")
            loop = asyncio.get_running_loop()
            match, ratio = await loop.run_in_executor(None, _highest_ratio, display_name, self.staff_names)
            # print(match, ratio)
            if ratio >= self.high_rt:
                await after.kick(reason=f'Impostor: {display_name} ({match}, {format(ratio*100, ".2f")}%)')
                await self._log_impostor(
                    after, "Impostor Kicked", f'{display_name} ({match}, {format(ratio*100, ".2f")}%)'
                )
            elif ratio >= self.low_rt:
                match_l = match.lower()
                display_name_l = display_name.lower()
                if (ratio_l := await loop.run_in_executor(None, _ratio, match_l, display_name_l)) > self.higher_rt:
                    await after.kick(
                        reason=f'Impostor (lowercase): {display_name_l} ({match_l}, {format(ratio_l*100, ".2f")}%)'
                    )
                    await self._log_impostor(
                        after, "Impostor Kicked", f'{display_name_l} ({match_l}, {format(ratio_l*100, ".2f")}%)'
                    )
                else:
                    await self._log_impostor(
                        after, "Potential Impostor", f'{display_name} ({match}, {format(ratio*100, ".2f")}%)'
                    )

    @commands.Cog.listener("on_member_join")
    async def kick_impostors_on_join(self, member):
        if not member.id in self.staff_ids and member.guild.id in self.guild_ids:  # TODO
            display_name = member.display_name.replace(" ", "")
            loop = asyncio.get_running_loop()
            match, ratio = await loop.run_in_executor(None, _highest_ratio, display_name, self.staff_names)
            # print(match, ratio)
            if ratio >= self.high_rt:
                await member.kick(reason=f'Impostor: {display_name} ({match}, {format(ratio*100, ".2f")}%)')
                await self._log_impostor(
                    member, "Impostor Kicked", f'{display_name} ({match}, {format(ratio*100, ".2f")}%)'
                )
            elif ratio >= self.low_rt:
                match_l = match.lower()
                display_name_l = display_name.lower()
                if (ratio_l := await loop.run_in_executor(None, _ratio, match_l, display_name_l)) > self.higher_rt:
                    await member.kick(
                        reason=f'Impostor (lowercase): {display_name_l} ({match_l}, {format(ratio_l*100, ".2f")}%)'
                    )
                    await self._log_impostor(
                        member, "Impostor Kicked", f'{display_name_l} ({match_l}, {format(ratio_l*100, ".2f")}%)'
                    )
                else:
                    await self._log_impostor(
                        member, "Potential Impostor", f'{display_name} ({match}, {format(ratio*100, ".2f")}%)'
                    )

    @commands.command(aliases=["clear", "delete"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, number: int, offender: discord.Member = None):
        channel = ctx.message.channel
        if number < 2 or number > 99:
            message = await ctx.send("Invalid number of messages.")
            await message.add_reaction("🆗")
            try:
                await self.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: user == ctx.message.author
                    and reaction.emoji == "🆗"
                    and reaction.message.id == message.id,
                    timeout=30.0,
                )
                await message.delete()
            except asyncio.TimeoutError:
                await message.delete()
            return

        if offender is not None:
            if offender == ctx.message.author:
                number += 1  # Accounting for command invoking message
            messages = []
            counter = 0
            async for message_sent in channel.history(limit=250):
                if counter == number:
                    break
                if message_sent.author == offender:
                    messages.append(message_sent)
                    counter += 1
            await channel.delete_messages(messages)
            message = await ctx.send("Deleted the last {0} messages from {1.mention}.".format(len(messages), offender))
            await message.add_reaction("🆗")
            try:
                await self.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: user == ctx.message.author
                    and reaction.emoji == "🆗"
                    and reaction.message.id == message.id,
                    timeout=30.0,
                )
                await message.delete()
            except asyncio.TimeoutError:
                await message.delete()

        else:
            # messages = await channel.history(limit=number).flatten()
            deleted = await channel.purge(limit=number + 1)  # Accounting for command invoking message
            message = await ctx.send("Deleted the last {} messages.".format(len(deleted)))
            await message.add_reaction("🆗")
            try:
                await self.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: user == ctx.message.author
                    and reaction.emoji == "🆗"
                    and reaction.message.id == message.id,
                    timeout=30.0,
                )
                await message.delete()
            except asyncio.TimeoutError:
                await message.delete()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def whois(self, ctx, member: discord.Member = None):
        if member is None:
            ctx.send("Incorrect format. The correct format is: `.info <user>`")
            return
        embed = discord.Embed(
            title="Discord Member Information", type="rich", color=0xFF6600, timestamp=ctx.message.created_at,
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.add_field(name="Status:", value=member.status, inline=False)
        embed.add_field(name="Activities:", value=member.activities, inline=False)
        embed.add_field(name="Discord ID:", value=member.id, inline=False)
        embed.add_field(name="Account created:", value=member.created_at, inline=False)
        embed.add_field(name="Server join date:", value=member.joined_at, inline=False)
        embed.set_footer(text="RCTBot", icon_url="https://i.imgur.com/Ou1k4lD.png")
        # embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png") # HoN logo
        message = await ctx.send(embed=embed)
        await message.add_reaction("🆗")
        try:
            await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.message.author
                and reaction.emoji == "🆗"
                and reaction.message.id == message.id,
                timeout=60.0,
            )
            await message.delete()
        except asyncio.TimeoutError:
            await message.delete()


def setup(bot):
    bot.add_cog(Moderation(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Moderation(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
