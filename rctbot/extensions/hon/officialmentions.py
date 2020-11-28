import discord
from discord.ext import commands


class MentionsTemp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def staff_mention_listener(self, message):
        if message.guild is None or message.guild.id != 735493943025860658 or len(message.mentions) < 1:
            return

        staff = discord.utils.get(message.guild.roles, name="Frostburn Staff")
        moderator = discord.utils.get(message.guild.roles, name="Discord Moderator")
        if staff in message.author.roles or moderator in message.author.roles:
            return

        for member in message.mentions:
            if staff in member.roles:
                is_staff = True
                break
            is_staff = False

        if not is_staff:
            return

        channel = message.guild.get_channel(735562529346158623)
        await channel.send(
            (
                f"{moderator.mention}, {message.author.mention} mentioned staff in {message.channel.mention}:"
                f" {message.content}"
            )
        )
