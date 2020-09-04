import discord
from discord.ext import commands, tasks

import rctbot.config
from rctbot.core.mongodb import CLIENT


# {guild.id: {message.id: {emoji.name: role.name}}}
REACTION_ROLES = {
    740225660412362843: {
        "742019802188611625": {"HoN": "Newerthian", "🇺🇸": "NA", "🇪🇺": "EU", "🇧🇷": "LAT", "🇷🇺": "CIS", "🇦🇺": "AUS"}
    }
}


class HoNOfficialRoles(commands.Cog):

    guild_id_dict = {}

    def __init__(self, bot):
        self.bot = bot
        self.db_client = CLIENT
        self.db = self.db_client["hon"]
        self.config_collection = self.db["config"]
        # self.guild_id_dict = {}
        self.fetch.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.fetch.cancel()  # pylint: disable=no-member

    @tasks.loop(hours=12.0)
    async def fetch(self):
        config = await self.config_collection.find_one({})
        # NOTE: All message ID keys are strings!
        self.guild_id_dict = {config["guild_id"]: config["reaction_roles"]}

    @commands.Cog.listener("on_raw_reaction_add")
    async def reaction_roles(self, payload):
        # NOTE: All message ID keys are strings!
        if (
            payload.guild_id not in self.guild_id_dict
            or str(payload.message_id) not in self.guild_id_dict[payload.guild_id]
            or payload.emoji.name not in self.guild_id_dict[payload.guild_id][str(payload.message_id)]
        ):
            return
        guild = self.bot.get_guild(payload.guild_id)
        # member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        role = discord.utils.get(
            guild.roles, name=(self.guild_id_dict[payload.guild_id][str(payload.message_id)][payload.emoji.name]),
        )
        if role not in payload.member.roles:
            await payload.member.add_roles(role, reason="Reaction")

        if role in payload.member.roles:
            await payload.member.remove_roles(role, reason="Reaction")
        await message.remove_reaction(payload.emoji, payload.member)


def setup(bot):
    bot.add_cog(HoNOfficialRoles(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(HoNOfficialRoles(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)

