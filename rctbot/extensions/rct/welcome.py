import os
import string
import secrets
from datetime import datetime, timezone

import discord
from discord.ext import commands


import rctbot.config
from rctbot.core.checks import is_senior
from rctbot.core.driver import AsyncDatabaseHandler


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
        welcome = guild.get_channel(rctbot.config.DISCORD_WELCOME_CHANNEL_ID)
        testing = guild.get_channel(rctbot.config.DISCORD_TESTING_CHANNEL_ID)
        community = discord.utils.get(guild.roles, name="Community Member")
        # tester = discord.utils.get(guild.roles, name="Tester")
        # moderator = discord.utils.get(guild.roles, name="Community Moderator")
        # senior = discord.utils.get(guild.roles, name="Senior Tester")

        # code = "".join(secrets.choice(self.alphabet) for i in range(self.code_len))

        # This is fucky due to guild, it's fine because only RCT will use it anyway.
        # log_channel = guild.get_channel(rctbot.config.DISCORD_BOT_LOG_CHANNEL_ID)
        # await log_channel.send(f"[Verification] {member.mention}\n**ID:** {member.id}\n**Code:** {code}")

        embed = discord.Embed(
            title=f"Welcome {discord.utils.escape_markdown(member.display_name)} to the official Retail Candidate Testers Discord Server!",
            type="rich",
            # description=(
            #    f"Please tell us your HoN username so that we can set it as your Discord nickname. Be respectful to every player and use common sense. If you have any questions, ask here on {channel.mention} or talk to a {moderator.mention} in private."
            #    f"If you have been accepted as a {tester.mention}, your verification code is `{code}` and your Discord ID is `{member.id}`. Please proceed as instructed in the forum PM and wait for a {senior.mention} to assign you the corresponding role so that you may access our private channels. In case you are not a tester but wish to become one, check the links below for more information."
            # ),
            description=(
                f"In order to chat here and access the rest of the server, you are required to link your Heroes of"
                f' Newerth and Discord accounts using [RCTBot]({os.getenv("DOMAIN")}/). Once connected,'
                " you will be unable to manually diconnect your Heroes of Newerth account from your current Discord"
                " account.\n\n"
                " Even though your sub-accounts will automatically be included, it is recommended to connect your"
                " primary HoN account if you are not a Tester. Testers should use the account with RCT access.\n\n"
                " For regular players, connected accounts will only be known to Frostburn Staff & RCT management."
                " Testers are able to view other testers' RCT statistics, including their HoN nickname, for the RCT"
                " account only. Information about sub-accounts and other related HoN accounts is never shown"
                " without your explicit permission.\n\n"
                " Be respectful to every player and use common sense. Keep confidential information in private channel"
                f" categories. If you have any questions, ask on {welcome.mention} or {testing.mention}, or talk to"
                " a Senior Tester in private."
            ),
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=member.display_name, icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Account Verification", value=f'{os.getenv("DOMAIN")}', inline=True,
        )
        embed.add_field(
            name="Application Form", value="https://forums.heroesofnewerth.com/index.php?/application/", inline=True,
        )
        embed.add_field(
            name="Clan Page", value="https://clans.heroesofnewerth.com/clan/RCT", inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        # TODO: Remove hardcoded database and collection names.
        collection = AsyncDatabaseHandler.client["rctbot"]["users"]
        testers_collection = AsyncDatabaseHandler.client["rct"]["testers"]
        if player := await collection.find_one({"discord_id": member.id}, {"_id": 0, "super_id": 1}):
            await member.add_roles(community, reason="HoN account already linked.")
            if await testers_collection.find_one({"enabled": True, "super_id": player["super_id"]}, {"_id": 0}):
                tester = discord.utils.get(guild.roles, name="Tester")
                if tester not in member.roles:
                    await member.add_roles(tester, reason="HoN account already linked and user is a Tester.")
        else:
            # TODO: The entire embed and its methods should go here.
            await member.send(embed=embed)

    @commands.command()
    @is_senior()
    async def omj(self, ctx):
        guild = ctx.guild
        welcome = guild.get_channel(rctbot.config.DISCORD_WELCOME_CHANNEL_ID)
        testing = guild.get_channel(rctbot.config.DISCORD_TESTING_CHANNEL_ID)
        tester = discord.utils.get(guild.roles, name="Tester")
        # moderator = discord.utils.get(guild.roles, name="Community Moderator")
        senior = discord.utils.get(guild.roles, name="Senior Tester")
        staff = discord.utils.get(guild.roles, name="Frostburn Staff")

        embed = discord.Embed(
            title="Welcome to the official Retail Candidate Testers Discord Server!",
            type="rich",
            description=(
                f"In order to chat here and access the rest of the server, you are required to link your Heroes of"
                f' Newerth and Discord accounts using [RCTBot]({os.getenv("DOMAIN")}/). Once connected,'
                " you will be unable to manually diconnect your Heroes of Newerth account from your current Discord"
                " account.\n\n"
                " Even though your sub-accounts will automatically be included, it is recommended to connect your"
                f" primary HoN account if you are not a {tester.mention}. Testers should use the account with RCT"
                " access.\n\n"
                f" For regular players, connected accounts will only be known to {staff.mention} & RCT management."
                " Testers are able to view other testers' RCT statistics, including their HoN nickname, for the RCT"
                " account only. Information about sub-accounts and other related HoN accounts is never shown"
                " without your explicit permission.\n\n"
                " Be respectful to every player and use common sense. Keep confidential information in private channel"
                f" categories. If you have any questions, ask on {welcome.mention} or {testing.mention}, or talk to"
                f" a {senior.mention} in private."
            ),
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        # embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Account Verification", value=f'{os.getenv("DOMAIN")}', inline=True,
        )
        embed.add_field(
            name="Application Form", value="https://forums.heroesofnewerth.com/index.php?/application/", inline=True,
        )
        embed.add_field(
            name="Clan Page", value="https://clans.heroesofnewerth.com/clan/RCT", inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        await ctx.send(embed=embed)
