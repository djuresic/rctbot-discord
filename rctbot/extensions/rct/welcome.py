import string
import secrets
from datetime import datetime, timezone

import discord
from discord.ext import commands


import rctbot.config
from rctbot.core.checks import is_senior


class RCTWelcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.code_len = 42
        self.alphabet = string.ascii_letters + string.digits

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.id != rctbot.config.DISCORD_RCT_GUILD_ID:
            return
        channel = guild.get_channel(rctbot.config.DISCORD_WELCOME_CHANNEL_ID)
        community = discord.utils.get(guild.roles, name="Community Member")
        tester = discord.utils.get(guild.roles, name="Tester")
        moderator = discord.utils.get(guild.roles, name="Community Moderator")
        senior = discord.utils.get(guild.roles, name="Senior Tester")

        code = "".join(secrets.choice(self.alphabet) for i in range(self.code_len))

        # This is fucky due to guild, it's fine because only RCT will use it anyway.
        log_channel = guild.get_channel(rctbot.config.DISCORD_BOT_LOG_CHANNEL_ID)
        await log_channel.send(f"[Verification] {member.mention}\n**ID:** {member.id}\n**Code:** {code}")

        embed = discord.Embed(
            title=f"Welcome {discord.utils.escape_markdown(member.display_name)} to the official Retail Candidate Testers Discord Server!",
            type="rich",
            description=f"""Please tell us your HoN username so that we can set it as your Discord nickname. Be respectful to every player and use common sense. If you have any questions, ask here on {channel.mention} or talk to a {moderator.mention} in private.
            
            If you have been accepted as a {tester.mention}, your verification code is `{code}` and your Discord ID is `{member.id}`. Please proceed as instructed in the forum PM and wait for a {senior.mention} to assign you the corresponding role so that you may access our private channels. In case you are not a tester but wish to become one, check the links below for more information.""",
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=member.display_name, icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Application Form", value="https://forums.heroesofnewerth.com/index.php?/application/", inline=True,
        )
        embed.add_field(
            name="Clan Page", value="http://clans.heroesofnewerth.com/clan/RCT", inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        await member.add_roles(community)
        await channel.send(embed=embed)

    @commands.command()
    @is_senior()
    async def omj(self, ctx):
        guild = ctx.guild
        tester = discord.utils.get(guild.roles, name="Tester")
        moderator = discord.utils.get(guild.roles, name="Community Moderator")
        senior = discord.utils.get(guild.roles, name="Senior Tester")

        code = "".join(secrets.choice(self.alphabet) for i in range(self.code_len))

        # This is fucky due to guild, it's fine because only RCT will use it anyway.
        log_channel = guild.get_channel(rctbot.config.DISCORD_BOT_LOG_CHANNEL_ID)
        await log_channel.send(f"[Verification] {ctx.author.mention}\n**ID:** {ctx.author.id}\n**Code:** {code}")

        embed = discord.Embed(
            title=f"Welcome {discord.utils.escape_markdown(ctx.author.display_name)} to the official Retail Candidate Testers Discord Server!",
            type="rich",
            description=f"""Please tell us your HoN username so that we can set it as your Discord nickname. Be respectful to every player and use common sense. If you have any questions, ask here on {ctx.channel.mention} or talk to a {moderator.mention} in private.
            
            If you have been accepted as a {tester.mention}, your verification code is `{code}` and your Discord ID is `{ctx.author.id}`. Please proceed as instructed in the forum PM and wait for a {senior.mention} to assign you the corresponding role so that you may access our private channels. In case you are not a tester but wish to become one, check the links below for more information.""",
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Application Form", value="https://forums.heroesofnewerth.com/index.php?/application/", inline=True,
        )
        embed.add_field(
            name="Clan Page", value="http://clans.heroesofnewerth.com/clan/RCT", inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        await ctx.send(embed=embed)
