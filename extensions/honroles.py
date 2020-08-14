import discord
from discord.ext import commands

import config

# NOTE: Most of it is hardcoded. It should be in MongoDB instead.

# {guild.id: {message.id: {emoji.name: role.name}}}
REACTION_ROLES = {
    740225660412362843: {
        742019802188611625: {
            "HoN": "Newerthian",
            "🇪🇺": "EU",
            "🇺🇸": "NA",
            "🇷🇺": "CIS",
            "🇦🇺": "AU",
        }
    }
}


class HoNOfficialRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_raw_reaction_add")
    async def reaction_roles(self, payload):
        if (
            payload.guild_id not in REACTION_ROLES.keys()
            or payload.message_id not in REACTION_ROLES[payload.guild_id].keys()
            or payload.emoji.name
            not in REACTION_ROLES[payload.guild_id][payload.message_id].keys()
        ):
            return
        guild = self.bot.get_guild(payload.guild_id)
        # member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        role = discord.utils.get(
            guild.roles,
            name=(
                REACTION_ROLES[payload.guild_id][payload.message_id][payload.emoji.name]
            ),
        )
        if role not in payload.member.roles:
            await payload.member.add_roles(role, reason="Reaction")

        if role in payload.member.roles:
            await payload.member.remove_roles(role, reason="Reaction")
        await message.remove_reaction(payload.emoji, payload.member)


def setup(bot):
    bot.add_cog(HoNOfficialRoles(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(HoNOfficialRoles(bot))
    config.LOADED_EXTENSIONS.remove(__loader__.name)
