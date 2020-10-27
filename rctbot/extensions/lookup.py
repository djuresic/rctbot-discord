import re
import asyncio
from typing import Union

import aiohttp
import discord
from discord.ext import commands

import rctbot.config
from rctbot.core.checks import is_senior
from rctbot.hon.acp2 import ACPClient
from rctbot.hon.masterserver import Client
from rctbot.hon.utils import get_avatar


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["lu", "lup", "lkp", "lkup"])
    @is_senior()
    async def lookup(self, ctx, player: Union[str, int], masterserver: str = "ac", *args):
        """Yes."""
        if masterserver.startswith("-"):
            args += (masterserver,)
            masterserver = "ac"
        session = aiohttp.ClientSession()
        ms = Client(masterserver, session=session)
        if player.isdigit():
            result = await ms.id2nick(player)
            if result is not None and not isinstance(result, dict):  # Till id2nick returns nick
                player = result.lower()
            else:
                return await ctx.send(f"{ctx.author.mention} Account does not exist.")
        else:
            player = player.lower()

        upgrades = bool("-u" in args or "--upgrades" in args)
        subs = bool("-s" in args or "--sub-accounts" in args)
        avatar = bool("-a" in args or "--avatar" in args)
        suspension = bool("-r" in args or "--rap" in args)

        data = await ms.show_stats(player, "ranked")
        if b"account_id" not in data:
            return await ctx.send(f"{ctx.author.mention} Account does not exist.")

        account_id = data[b"account_id"].decode()
        super_id = data[b"super_id"].decode()

        if upgrades:
            data_ss = await ms.show_simple_stats(player)
            data_mu = await ms.show_stats(player, "mastery")

            selected_upgrades = ", ".join(
                [v.decode() for v in data_mu[b"selected_upgrades"].values() if isinstance(v, bytes)]
            )
            other_upgrades = ", ".join([v.decode() for v in data[b"my_upgrades"].values() if isinstance(v, bytes)])
        await session.close()

        if subs or suspension:
            async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
                if subs:
                    sub_accounts = await acp.get_sub_accounts(account_id)
                if suspension:
                    active_suspension = await acp.check_suspension(super_id)
                    active_suspension = (
                        active_suspension.replace("<strong>", "").replace("</strong>", "").replace("<br />", "\n")
                    )

        default_avatar = "https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png"
        if masterserver == "ac":
            if avatar:
                account_icon_url = await get_avatar(account_id)
            else:
                account_icon_url = default_avatar
        else:
            account_icon_url = default_avatar

        clan_tag_match = re.match(r"\[[0-9a-zA-Z]+\]", data[b"nickname"].decode())
        if clan_tag_match:
            clan_tag = clan_tag_match.group(0)
        else:
            clan_tag = "\u2063"

        nickname = data[b"nickname"].decode().replace(clan_tag, "")

        clan_name = data[b"name"].decode() if b"name" in data else "\u2063"
        clan_rank = data[b"rank"].decode() if b"rank" in data else "\u2063"
        if clan_rank != "\u2063" and clan_name == "\u2063" and clan_tag == "\u2063":  # Ah yes, the ghost clan.
            clan_tag = "[]"

        embed_nickname = f"{clan_tag}{nickname}"

        last_activity = (
            data[b"last_activity"].decode()
            if b"last_activity" in data and data[b"last_activity"] is not None
            else "\u2063"
        )

        account_type = rctbot.config.HON_TYPE_MAP[data[b"account_type"].decode()]
        standing = rctbot.config.HON_STANDING_MAP[data[b"standing"].decode()]

        embed = discord.Embed(
            title=ms.client_name,
            type="rich",
            description="Account Information",
            color=ms.color,
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=embed_nickname,
            url=f"https://www.heroesofnewerth.com/playerstats/ranked/{nickname}",
            icon_url=account_icon_url,
        )

        embed.add_field(name="Nickname", value=nickname, inline=True)
        embed.add_field(name="Account ID", value=account_id, inline=True)
        embed.add_field(name="Super ID", value=super_id, inline=True)

        embed.add_field(name="Created", value=data[b"create_date"].decode(), inline=True)
        embed.add_field(name="Last Activity", value=last_activity, inline=True)

        embed.add_field(name="Account Type", value=account_type, inline=True)
        embed.add_field(name="Standing", value=standing, inline=True)

        embed.add_field(name="Clan Tag", value=clan_tag, inline=True)
        embed.add_field(name="Clan Name", value=clan_name, inline=True)
        embed.add_field(name="Clan Rank", value=clan_rank, inline=True)

        embed.add_field(
            name="Level",
            value=(data[b"level"].decode() if not isinstance(data[b"level"], int) else data[b"level"]),
            inline=True,
        )
        embed.add_field(name="Level Experience", value=data[b"level_exp"], inline=True)

        if upgrades:
            embed.add_field(name="Avatars", value=data_ss[b"avatar_num"], inline=True)
            embed.add_field(name="Selected", value=selected_upgrades, inline=True)
            embed.add_field(name="Other", value=other_upgrades, inline=True)

        if subs:
            account_names = [account[1] for account in sub_accounts]
            embed.add_field(
                name=f"Accounts ({len(account_names)})",
                value=discord.utils.escape_markdown(", ".join(account_names)),
                inline=False,
            )

        if suspension:
            embed.add_field(
                name="Suspension", value=discord.utils.escape_markdown(active_suspension), inline=False,
            )

        embed.set_footer(
            text="Requested by {0} ({1}#{2}). React with 🗑️ to delete, 💾 to keep this message.".format(
                ctx.author.display_name, ctx.author.name, ctx.author.discriminator,
            ),
            icon_url="https://i.imgur.com/Ou1k4lD.png",
        )
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")

        message = await ctx.send(embed=embed)
        await message.add_reaction("🗑️")
        await message.add_reaction("💾")

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.author
                and reaction.emoji in ["🗑️", "💾"]
                and reaction.message.id == message.id,
                timeout=300.0,
            )

            if reaction.emoji == "🗑️":
                await message.delete()

        except asyncio.TimeoutError:
            await message.delete()


def setup(bot):
    bot.add_cog(Lookup(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Lookup(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
