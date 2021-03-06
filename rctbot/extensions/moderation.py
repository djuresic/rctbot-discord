import asyncio
import discord
from discord.ext import commands


import rctbot.config


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banned_domains = ["bit.ly"]

    @commands.Cog.listener("on_member_update")
    async def kick_username_links(self, before, after):
        if after.display_name != before.display_name:
            display_name = after.display_name.replace(" ", "")
            for domain in self.banned_domains:
                if domain in display_name and "/" in display_name:
                    await after.kick(reason=f"Banned URL in display name: {display_name}")
                    break

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
