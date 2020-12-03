import discord
from discord.ext import commands

# TODO: Remove hardcoded and put in DB instead.


class MentionsTemp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.excluded_channels = [
            776395558460981279,
            777190927399649312,
            776395711599607838,
            776395734224076840,
            776395750800228362,
            735520263554465823,
            735562300697608286,
            752153227780423681,
            783731099028160542,
        ]

    @commands.Cog.listener("on_message")
    async def staff_mention_listener(self, message):
        if (
            message.guild is None
            or message.guild.id != 735493943025860658
            or message.author.bot
            or len(message.mentions) < 1
            or message.channel.id in self.excluded_channels
        ):
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

        channel = message.guild.get_channel(782535231332155392)
        embed = discord.Embed(
            title="Staff Mention",
            type="rich",
            description=message.clean_content,
            color=0x7289DA,
            timestamp=message.created_at,
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        embed.add_field(name="Message", value=f"[Jump]({message.jump_url})", inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.set_footer(text=f"Author: {message.author.id} • Message: {message.id}")
        await channel.send(moderator.mention, embed=embed)
