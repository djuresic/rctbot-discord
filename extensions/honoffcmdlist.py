import discord
from discord.ext import commands

import config
from core.checks import is_senior


class HoNOfficialDiscordCommandList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_senior()
    async def botcmdlist(self, ctx):
        embed = discord.Embed(
            title="Heroes of Newerth International",
            type="rich",
            description=(
                "A list of <@681882801427316767> commands available only on Discord. Both `.` and `!` can be"
                " used as the command prefix. Commands on this list are written in the following format:"
                "\n```css\n.command subcommand [argument] {description}```"
            ),
            url="https://discord.gg/F7gQtUm",
            color=0x3CC03C,
            timestamp=ctx.message.created_at,
        )
        embed.set_author(name="Commands")
        embed.add_field(
            name="Statistics",
            value=(
                "```css"
                "\n.stats [nickname] {In-game player statistics for nickname. HoN NAEU/International only.}```"
            ),
            inline=False,
        )
        embed.add_field(
            name="Gambling", value="```css\n.roll [low] [high]```", inline=False,
        )
        embed.add_field(
            name="Miscellaneous",
            value="```css\n.signature {Purchase or configure Discord Embedded Signature.}```",
            inline=False,
        )
        # embed.add_field(name="Links (RCT Only)", value="```css\n.forums```", inline=False)
        embed.set_footer(text="RCTBot", icon_url="https://i.imgur.com/Ou1k4lD.png")
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        await ctx.send(embed=embed)
        await ctx.message.delete()


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(HoNOfficialDiscordCommandList(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
