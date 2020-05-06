from datetime import datetime, timezone

import discord
from discord.ext import commands

import config
from extensions.checks import is_senior


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        channel = guild.get_channel(406902132424441857)  # This
        tester = discord.utils.get(guild.roles, name="Tester")
        moderator = discord.utils.get(guild.roles, name="Community Moderator")
        senior = discord.utils.get(guild.roles, name="Senior Tester")

        embed = discord.Embed(
            title=f"Welcome {member.display_name} to the official Retail Candidate Testers Discord Server!",
            type="rich",
            description=f"""Please tell us your HoN username so that we can set it as your Discord nickname. Be respectful to every player and use common sense. If you have any questions, ask here on {channel.mention} or talk to a {moderator.mention} in private.
            
            If you have been accepted as a {tester.mention}, please wait for a {senior.mention} to assign you the corresponding role so that you may access our private channels. In case you are not a tester but wish to become one, check the links below for more information.""",
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=member.display_name, icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Application Form",
            value="https://forums.heroesofnewerth.com/index.php?/application/",
            inline=True,
        )
        embed.add_field(
            name="Clan Page",
            value="http://clans.heroesofnewerth.com/clan/RCT",
            inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        await channel.send(embed=embed)

    @commands.command()
    @is_senior()
    async def omj(self, ctx):
        guild = ctx.guild
        # channel = guild.get_channel(406902132424441857)
        tester = discord.utils.get(guild.roles, name="Tester")
        moderator = discord.utils.get(guild.roles, name="Community Moderator")
        senior = discord.utils.get(guild.roles, name="Senior Tester")

        embed = discord.Embed(
            title=f"Welcome {ctx.author.display_name} to the official Retail Candidate Testers Discord Server!",
            type="rich",
            description=f"""Please tell us your HoN username so that we can set it as your Discord nickname. Be respectful to every player and use common sense. If you have any questions, ask here on {ctx.channel.mention} or talk to a {moderator.mention} in private.
            
            If you have been accepted as a {tester.mention}, please wait for a {senior.mention} to assign you the corresponding role so that you may access our private channels. In case you are not a tester but wish to become one, check the links below for more information.""",
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/ys2UBNW.png")
        embed.add_field(
            name="Application Form",
            value="https://forums.heroesofnewerth.com/index.php?/application/",
            inline=True,
        )
        embed.add_field(
            name="Clan Page",
            value="http://clans.heroesofnewerth.com/clan/RCT",
            inline=True,
        )

        embed.set_footer(
            text="And another one!", icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Welcome(bot))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
