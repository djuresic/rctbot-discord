import math
import timeit
import asyncio
import collections
from io import BytesIO
from typing import Tuple

import aiohttp
import discord
from discord.ext import commands
from PIL import Image

import rctbot.config

# from core.logging import record_usage NOTE: discord.py 1.4
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.core.checks import guild_is_rct
from rctbot.core.rct import ActivityRank, CycleValues
from rctbot.core.utils import dhms, ordinal
from rctbot.hon.masterserver import Client
from rctbot.hon.portal import VPClient
from rctbot.hon.acp2 import ACPClient
from rctbot.hon.utils import get_name_color, get_avatar
from rctbot.extensions.rct.matchtools import MatchTools


class RCTStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_bugs = self.db[rctbot.config.MONGO_TESTING_BUGS_COLLECTION_NAME]
        self.testing_extra = self.db[rctbot.config.MONGO_TESTING_EXTRA_COLLECTION_NAME]
        self.cycle_values = CycleValues()

    # TODO: Match stats command.

    async def _get_full_nickname(self, nickname: str) -> Tuple[str, str, int]:
        try:
            # timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                simple_stats = await Client("ac", session=session).show_simple_stats(nickname)
                if simple_stats and b"nickname" in simple_stats:
                    nick_with_clan_tag = simple_stats[b"nickname"].decode()
                    name_color = await get_name_color(simple_stats)
                    if "]" in nick_with_clan_tag:
                        clan_tag = f"{nick_with_clan_tag.split(']')[0]}]"
                    else:
                        clan_tag = ""
                else:
                    nick_with_clan_tag = nick
                    clan_tag = None
                    name_color = 0xFFFFFF
        except:
            nick_with_clan_tag = nickname
            clan_tag = None
            name_color = 0xFFFFFF
        return nick_with_clan_tag, clan_tag, name_color

    async def _get_db_rnk(self, account_id: int) -> Tuple[str, str, str, str]:
        """Database leaderboard ranking for a user.

        Args:
            testing_account_id (int): Account ID of the user.

        Returns:
            Tuple[str, str, str, str]: Positions on the ladder as ordinal number strings in a tuple odered as follows:
                games, total games, bug reports, total bug reports.
        """

        def create_pipeline(field: str):
            return [
                # Sort in descending order.
                {"$sort": {field: -1}},
                # _id value is constant so it calculates accumulated values for all the input documents as a whole.
                {"$group": {"_id": 1, "users": {"$push": {"account_id": "$account_id", field: f"${field}"}}}},
                # Use index to later calculate ranking.
                {"$unwind": {"path": "$users", "includeArrayIndex": "ranking"}},
                # Find the user by account_id.
                {"$match": {"users.account_id": account_id}},
                # Add 1 to ranking (index) and project it.
                {"$project": {"ranking": {"$add": ["$ranking", 1]}}},
            ]

        ranking_games = ordinal(
            (await (self.testers.aggregate(create_pipeline("games"))).to_list(length=None))[0]["ranking"]
        )
        ranking_total_games = ordinal(
            (await (self.testers.aggregate(create_pipeline("total_games"))).to_list(length=None))[0]["ranking"]
        )
        ranking_bugs = ordinal(
            (await (self.testers.aggregate(create_pipeline("bugs"))).to_list(length=None))[0]["ranking"]
        )
        ranking_total_bugs = ordinal(
            (await (self.testers.aggregate(create_pipeline("total_bugs"))).to_list(length=None))[0]["ranking"]
        )
        return ranking_games, ranking_total_games, ranking_bugs, ranking_total_bugs

    async def _get_rt_rnk(self, testing_account_id: int) -> Tuple[str, str, str, str]:
        """Real time leaderboard ranking for a user.

        Args:
            testing_account_id (int): Testing account ID of the user.

        Returns:
            Tuple[str, str, str, str]: Positions on the ladder as ordinal number strings in a tuple odered as follows:
                games, total games, bug reports, total bug reports.
        """
        pipeline = [{"$unwind": "$participants"}, {"$project": {"_id": 0, "participants.account_id": 1}}]
        games_docs = await (self.testing_games.aggregate(pipeline)).to_list(length=None)
        participants = [document["participants"]["account_id"] for document in games_docs]
        participants = collections.Counter(participants)
        # participants = [participant for participant in participants]

        # TODO: Approved and unapproved bugs.
        bugs_docs = await (self.testing_bugs.find({})).to_list(length=None)
        reporters = [document["reporter"]["testing_account_id"] for document in bugs_docs]
        reporters = collections.Counter(reporters)

        # Unlike the previous method with list of tuples sorted by tuple elements, this method solves the prolem of
        # testers with the same "score" not sharing the same place on the ladder.

        # Create empty lists for all required fields.
        games_list = []
        total_games_list = []
        bugs_list = []
        total_bugs_list = []
        # Tuple for the tester in question.
        tester_tuple = None
        async for tester in self.testers.find(
            {}, {"_id": 0, "testing_account_id": 1, "total_games": 1, "total_bugs": 1}
        ):
            games = participants.get(tester["testing_account_id"], 0)
            total_games = tester["total_games"] + games
            games_list.append(games)
            total_games_list.append(total_games)

            bugs = reporters.get(tester["testing_account_id"], 0)
            total_bugs = tester["total_bugs"] + bugs
            bugs_list.append(bugs)
            total_bugs_list.append(total_bugs)

            if tester["testing_account_id"] == testing_account_id:
                tester_tuple = (tester["testing_account_id"], games, total_games, bugs, total_bugs)

        # All lists to descending order.
        lbd_games = sorted(games_list, reverse=True)
        lbd_total_games = sorted(total_games_list, reverse=True)
        lbd_bugs = sorted(bugs_list, reverse=True)
        lbd_total_bugs = sorted(total_bugs_list, reverse=True)

        # Ranking as the index of the element + 1.
        rnk_games = ordinal(lbd_games.index(tester_tuple[1]) + 1)
        rnk_total_games = ordinal(lbd_total_games.index(tester_tuple[2]) + 1)
        rnk_bugs = ordinal(lbd_bugs.index(tester_tuple[3]) + 1)
        rnk_total_bugs = ordinal(lbd_total_bugs.index(tester_tuple[4]) + 1)
        return rnk_games, rnk_total_games, rnk_bugs, rnk_total_bugs

    @commands.command(aliases=["rank2", "sheet2"])
    @guild_is_rct()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(10, per=commands.BucketType.guild, wait=False)
    async def rct2(self, ctx, member: str = ""):
        start = timeit.default_timer()
        if member == "":
            discord_id = ctx.author.id
        elif len(ctx.message.raw_mentions) > 0:
            discord_id = ctx.message.raw_mentions[0]
        else:
            discord_id = None

        if discord_id is not None:
            user = await self.testers.find_one({"discord_id": discord_id})
        else:
            member = member.replace("\\", "")
            user = await self.testers.find_one({"nickname": member.lower()}, collation={"locale": "en", "strength": 1})

        requester_discord_id = ctx.author.id
        requester = await self.testers.find_one({"discord_id": requester_discord_id})
        if requester is not None:
            requester_name = requester["nickname"]
            requester_verified = True  # TODO: Better solution for this.
        else:
            requester_name = ctx.author.display_name
            requester_verified = False
            requester_discord_id = None

        # print(user)
        if user is None:
            return await ctx.send(
                f"{ctx.author.mention} That player is neither former nor past RCT member.",
                delete_after=10.0,
            )

        nick_with_clan_tag, _, name_color = await self._get_full_nickname(user["nickname"])

        games_list = await (self.testing_games.find({"participants.account_id": user["testing_account_id"]})).to_list(
            length=None
        )
        games = len(games_list)
        total_games = user["total_games"] + games
        seconds = sum([game["length"] for game in games_list])
        total_seconds = user["total_seconds"] + seconds
        game_time = dhms(seconds)
        total_game_time = dhms(total_seconds)

        bugs = await self.testing_bugs.count_documents({"reporter.testing_account_id": user["testing_account_id"]})
        total_bugs = user["total_bugs"] + bugs

        # Leaderboard in real time. NOTE: This does some of the queries already performed by the command. Refactor?
        rnk_games, rnk_total_games, rnk_bugs, rnk_total_bugs = await self._get_rt_rnk(user["testing_account_id"])

        # Reset 50 games bonus values so that the current token calculations are accurate.
        bonus_last_cycle = math.floor((user["total_games"] / 50) - user["bonuses_given"])
        bonuses_given = user["bonuses_given"] + bonus_last_cycle
        current_bonus = math.floor((total_games / 50) - bonuses_given)

        rank_id = user["rank_id"]
        # skipcq: PTC-W0048
        if ("absence" not in user or user["absence"] is None) or ("absence" in user and rank_id > ActivityRank.GOLD):
            if ActivityRank.UNRANKED < rank_id < ActivityRank.LEGENDARY:  # skipcq: PTC-W0048
                if (games + bugs) >= self.cycle_values.advance[rank_id]:
                    rank_id += 1
                elif (games + bugs) < self.cycle_values.keep[rank_id]:
                    rank_id -= 1
        # Should've just put 1000 games requirement for advancing to Immortal... Keeping this for now.
        if rank_id >= ActivityRank.LEGENDARY and (games + bugs) < self.cycle_values.keep[rank_id]:
            rank_id -= 1

        final_multiplier = self.cycle_values.multiplier[rank_id] + self.cycle_values.artificial
        extra = await (self.testing_extra.find({"tester.account_id": user["account_id"]})).to_list(length=None)
        extra = sum([document["amount"] for document in extra])
        tokens = round(
            (
                games * self.cycle_values.game
                + seconds * self.cycle_values.second
                + (self.cycle_values.ten if games >= 10 else 0)
                + (self.cycle_values.twenty if games >= 20 else 0)
            )
            * final_multiplier
            + current_bonus * self.cycle_values.fifty
            + bugs * self.cycle_values.bug
            + extra
        )

        bonuses = []
        for number in 10, 20:
            if games >= number:
                bonuses.append(str(number))
        if current_bonus > 0:
            bonuses.append("50")
        bonuses = ", ".join(bonuses) + " games" if len(bonuses) > 0 else "None"

        ranks = {
            7: {
                "name": "Immortal",
                "icon_url": "https://i.imgur.com/dpugisO.png",
                "icon_emoji": rctbot.config.EMOJI_IMMORTAL_RANK,
                "chest_emoji": rctbot.config.EMOJI_IMMORTAL_CHEST,
            },
            6: {
                "name": "Legendary",
                "icon_url": "https://i.imgur.com/59Jighv.png",
                "icon_emoji": rctbot.config.EMOJI_LEGENDARY_RANK,
                "chest_emoji": rctbot.config.EMOJI_LEGENDARY_CHEST,
            },
            5: {
                "name": "Diamond",
                "icon_url": "https://i.imgur.com/AZYAK39.png",
                "icon_emoji": rctbot.config.EMOJI_DIAMOND_RANK,
                "chest_emoji": rctbot.config.EMOJI_DIAMOND_CHEST,
            },
            4: {
                "name": "Gold",
                "icon_url": "https://i.imgur.com/ZDLUlqs.png",
                "icon_emoji": rctbot.config.EMOJI_GOLD_RANK,
                "chest_emoji": rctbot.config.EMOJI_GOLD_CHEST,
            },
            3: {
                "name": "Silver",
                "icon_url": "https://i.imgur.com/xxxlPAq.png",
                "icon_emoji": rctbot.config.EMOJI_SILVER_RANK,
                "chest_emoji": rctbot.config.EMOJI_SILVER_CHEST,
            },
            2: {
                "name": "Bronze",
                "icon_url": "https://i.imgur.com/svAUm00.png",
                "icon_emoji": rctbot.config.EMOJI_BRONZE_RANK,
                "chest_emoji": rctbot.config.EMOJI_BRONZE_CHEST,
            },
            1: {
                "name": "Warning",
                "icon_url": "https://i.imgur.com/svAUm00.png",
                "icon_emoji": rctbot.config.EMOJI_BRONZE_RANK,
                "chest_emoji": rctbot.config.EMOJI_BRONZE_CHEST,
            },
            0: {
                "name": "Unranked",
                "icon_url": "https://i.imgur.com/ys2UBNW.png",
                "icon_emoji": rctbot.config.EMOJI_UNRANKED_RANK,
                "chest_emoji": rctbot.config.EMOJI_UNRANKED_CHEST,
            },
        }

        embed = discord.Embed(
            title="Retail Candidate Testers",
            type="rich",
            description=f'Information for {user["role"]} {discord.utils.escape_markdown(user["nickname"])}.',
            url="https://forums.heroesofnewerth.com/index.php?/forum/18-rct/",
            color=name_color,
            timestamp=MatchTools.last_fetched,
        )
        embed.set_author(
            name=nick_with_clan_tag,
            # url=f'https://forums.heroesofnewerth.com/member.php?{user["account_id"]}',
            icon_url=(await get_avatar(user["account_id"])),
        )
        enabled = user["enabled"]
        auto_reveal_tokens = user["consents"].get("auto_reveal_tokens", None)
        if enabled:
            embed.add_field(name="Games", value=f"{games} ({rnk_games})", inline=True)
            embed.add_field(name="Game Time", value=game_time, inline=True)
            embed.add_field(name="Bug Reports", value=f"{bugs} ({rnk_bugs})", inline=True)
        embed.add_field(name="Total Games", value=f"{total_games} ({rnk_total_games})", inline=True)
        embed.add_field(name="Total Game Time", value=total_game_time, inline=True)
        embed.add_field(name="Total Bug Reports", value=f"{total_bugs} ({rnk_total_bugs})", inline=True)
        if enabled:
            embed.add_field(name="Earned Tokens", value=tokens, inline=True)

            if requester_name.lower() == user["nickname"].lower() and requester_verified:
                if not auto_reveal_tokens:
                    owned_tokens_message = f"React with {rctbot.config.EMOJI_GOLD_COINS} to reveal."
                else:
                    async with VPClient() as portal:
                        owned_tokens_message = await portal.get_tokens(user["account_id"])
            else:
                owned_tokens_message = (
                    f'Available when used by {discord.utils.escape_markdown(user["nickname"])} only!'
                )

            embed.add_field(name="Owned Tokens", value=owned_tokens_message, inline=True)
            embed.add_field(name="Bonuses", value=bonuses, inline=True)
            embed.add_field(
                name="Activity Rank",
                value=f'{ranks[user["rank_id"]]["icon_emoji"]} {ranks[user["rank_id"]]["name"]}',
                inline=True,
            )
            embed.add_field(
                name="Activity Rank Trend",
                value=f'{ranks[rank_id]["icon_emoji"]} {ranks[rank_id]["name"]}',
                inline=True,
            )
            embed.add_field(
                name="Multiplier",
                value=f'{ranks[rank_id]["chest_emoji"]} {final_multiplier}x',
                inline=True,
            )
        embed.add_field(
            name="Join Date",
            value=user["joined"].get("last", user["joined"]["first"]).strftime("%A, %B %d, %Y"),
            inline=False,
        )
        if user["signature"]["purchased"]:
            if user["signature"]["url"] != "":
                embed.set_image(url=user["signature"]["url"])
            else:
                embed.add_field(
                    name="You own a Discord Embedded Signature!",
                    value="Set it up using the `.signature` command to make Merrick even more jealous of you.",
                    inline=False,
                )
        embed.set_thumbnail(url=ranks[user["rank_id"]]["icon_url"])
        message = await ctx.send(embed=embed)
        stop = timeit.default_timer()
        print(stop - start)

        if requester_name.lower() == user["nickname"].lower() and requester_verified and not auto_reveal_tokens:
            await message.add_reaction(rctbot.config.EMOJI_GOLD_COINS)

        # Compare reaction emojis, clear all on timeout.
        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.author
                and str(reaction.emoji) in [rctbot.config.EMOJI_GOLD_COINS]
                and reaction.message.id == message.id,
                timeout=300.0,
            )

            if (
                str(reaction.emoji) == rctbot.config.EMOJI_GOLD_COINS
                and requester_name.lower() == user["nickname"].lower()
                and requester_verified
            ):
                await message.clear_reactions()
                async with VPClient() as portal:
                    tokens = await portal.get_tokens(user["account_id"])
                embed.set_field_at(index=7, name="Owned Tokens", value=tokens, inline=True)
                await message.edit(embed=embed)
                await message.add_reaction("🗑️")
                await message.add_reaction("💾")

                # Allow the message containing owned tokens info to be deleted.
                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: user == ctx.author
                        and str(reaction.emoji) in ["🗑️", "💾"]
                        and reaction.message.id == message.id,
                        timeout=300.0,
                    )

                    if reaction.emoji == "🗑️":
                        await message.delete()

                except asyncio.TimeoutError:
                    await message.delete()

        except asyncio.TimeoutError:
            await message.clear_reactions()

    @commands.command(aliases=["rank", "sheet"])
    @guild_is_rct()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(10, per=commands.BucketType.guild, wait=False)
    async def rct(self, ctx, member: str = ""):
        # TODO: Assign some values to variables
        start = timeit.default_timer()
        if member == "":
            discord_id = ctx.author.id
        elif len(ctx.message.raw_mentions) > 0:
            discord_id = ctx.message.raw_mentions[0]
        else:
            discord_id = None

        if discord_id is not None:
            user = await self.testers.find_one({"discord_id": discord_id})
        else:
            member = member.replace("\\", "")
            user = await self.testers.find_one({"nickname": member.lower()}, collation={"locale": "en", "strength": 1})

        requester_discord_id = ctx.author.id
        requester = await self.testers.find_one({"discord_id": requester_discord_id})
        if requester is not None:
            requester_name = requester["nickname"]
        else:
            requester_name = ctx.author.display_name
            requester_discord_id = None

        # print(user)
        if user is None:
            return await ctx.send(
                f"{ctx.author.mention} That player is neither former nor past RCT member.",
                delete_after=10.0,
            )

        nick_with_clan_tag, clan_tag, name_color = await self._get_full_nickname(user["nickname"])

        enabled = user["enabled"]
        # TODO: dict to tuples
        ranks = {
            7: {
                "name": "Immortal",
                "icon_url": "https://i.imgur.com/dpugisO.png",
                "icon_emoji": rctbot.config.EMOJI_IMMORTAL_RANK,
                "chest_emoji": rctbot.config.EMOJI_IMMORTAL_CHEST,
                "multiplier": 2.5,
            },
            6: {
                "name": "Legendary",
                "icon_url": "https://i.imgur.com/59Jighv.png",
                "icon_emoji": rctbot.config.EMOJI_LEGENDARY_RANK,
                "chest_emoji": rctbot.config.EMOJI_LEGENDARY_CHEST,
                "multiplier": 2.0,
            },
            5: {
                "name": "Diamond",
                "icon_url": "https://i.imgur.com/AZYAK39.png",
                "icon_emoji": rctbot.config.EMOJI_DIAMOND_RANK,
                "chest_emoji": rctbot.config.EMOJI_DIAMOND_CHEST,
                "multiplier": 1.75,
            },
            4: {
                "name": "Gold",
                "icon_url": "https://i.imgur.com/ZDLUlqs.png",
                "icon_emoji": rctbot.config.EMOJI_GOLD_RANK,
                "chest_emoji": rctbot.config.EMOJI_GOLD_CHEST,
                "multiplier": 1.5,
            },
            3: {
                "name": "Silver",
                "icon_url": "https://i.imgur.com/xxxlPAq.png",
                "icon_emoji": rctbot.config.EMOJI_SILVER_RANK,
                "chest_emoji": rctbot.config.EMOJI_SILVER_CHEST,
                "multiplier": 1.25,
            },
            2: {
                "name": "Bronze",
                "icon_url": "https://i.imgur.com/svAUm00.png",
                "icon_emoji": rctbot.config.EMOJI_BRONZE_RANK,
                "chest_emoji": rctbot.config.EMOJI_BRONZE_CHEST,
                "multiplier": 1.0,
            },
            1: {
                "name": "Warning",
                "icon_url": "https://i.imgur.com/svAUm00.png",
                "icon_emoji": rctbot.config.EMOJI_BRONZE_RANK,
                "chest_emoji": rctbot.config.EMOJI_BRONZE_CHEST,
                "multiplier": 0.5,
            },
            0: {
                "name": "Unranked",
                "icon_url": "https://i.imgur.com/ys2UBNW.png",
                "icon_emoji": rctbot.config.EMOJI_UNRANKED_RANK,
                "chest_emoji": rctbot.config.EMOJI_UNRANKED_CHEST,
                "multiplier": 0.0,
            },
        }

        # This cycle. TODO: fucking yikes
        seconds = user["seconds"]
        dhms = ""
        for scale in 86400, 3600, 60:
            result, seconds = divmod(seconds, scale)
            if dhms != "" or result > 0:
                dhms += "{0:02d}:".format(result)
        dhms += "{0:02d}".format(seconds)

        gametime = f"{dhms}"

        # Total.
        seconds_total = user["total_seconds"]
        dhms_total = ""
        for scale_total in 86400, 3600, 60:
            result_total, seconds_total = divmod(seconds_total, scale_total)
            if dhms_total != "" or result_total > 0:
                dhms_total += "{0:02d}:".format(result_total)
        dhms_total += "{0:02d}".format(seconds_total)

        gametime_total = f"{dhms_total}"

        games = user["games"]
        bonus = []
        if games >= 10:
            bonus.append("10")
        if games >= 20:
            bonus.append("20")
        if math.floor((user["total_games"] / 50) - user["bonuses_given"]) > 0:
            bonus.append("50")
        if len(bonus) == 0:
            bonus.append("None")
            bonus = ", ".join(bonus)
        else:
            bonus = ", ".join(bonus) + " games"

        unconfirmed_games = await self.testing_games.count_documents(
            {"participants.account_id": user["testing_account_id"]}
        )

        embed = discord.Embed(
            title="Retail Candidate Testers",
            type="rich",
            description=f'Information for {user["role"]} {discord.utils.escape_markdown(user["nickname"])}.',
            url="https://forums.heroesofnewerth.com/forumdisplay.php?209-Retail-Candidate-Testers",
            color=name_color,
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=nick_with_clan_tag,
            url=f'https://forums.heroesofnewerth.com/member.php?{user["account_id"]}',
            icon_url=(await get_avatar(user["account_id"])),
        )
        if enabled:
            embed.add_field(name="Unconfirmed games", value=unconfirmed_games, inline=True)
            # embed.add_field(name=u"\u2063", value=u"\u2063", inline=True)
            embed.add_field(
                name="Games",
                value=f'{user["games"]} ({ordinal(user["ladder"]["games"])})',
                inline=True,
            )
        if enabled:
            embed.add_field(
                name="Total games",
                value=f'{user["total_games"]} ({ordinal(user["ladder"]["total_games"])})',
                inline=True,
            )
        else:
            embed.add_field(name="Total games", value=user["total_games"], inline=True)
        if enabled:
            embed.add_field(name="Game time", value=gametime, inline=True)
        embed.add_field(name="Total game time", value=gametime_total, inline=True)
        if enabled:
            embed.add_field(
                name="Bug reports",
                value=f'{user["bugs"]} ({ordinal(user["ladder"]["bugs"])})',
                inline=True,
            )
        if enabled:
            embed.add_field(
                name="Total bug reports",
                value=f'{user["total_bugs"]} ({ordinal(user["ladder"]["total_bugs"])})',
                inline=True,
            )
        else:
            embed.add_field(
                name="Total bug reports",
                value=user["total_bugs"],
                inline=True,
            )
        if enabled:
            embed.add_field(
                name="Tokens earned",
                value=f'{user["tokens"]} ({ordinal(user["ladder"]["tokens"])})',
                inline=True,
            )

            if requester_name.lower() == user["nickname"].lower():
                owned_tokens_message = f"React with {rctbot.config.EMOJI_GOLD_COINS} to reveal."
            else:
                owned_tokens_message = (
                    f'Available when used by {discord.utils.escape_markdown(user["nickname"])} only!'
                )
            embed.add_field(
                name="Tokens owned",
                value=owned_tokens_message,
                inline=True,
            )

            embed.add_field(
                name="Activity rank",
                value=f'{ranks[user["rank_id"]]["icon_emoji"]} {ranks[user["rank_id"]]["name"]}',
                inline=True,
            )
            # FIXME: Move Artificial Multiplier
            final_multiplier = self.cycle_values.multiplier[user["rank_id"]] + self.cycle_values.artificial
            embed.add_field(
                name="Multiplier",
                value=f'{ranks[user["rank_id"]]["chest_emoji"]} {final_multiplier}x',
                inline=True,
            )
            embed.add_field(name="Bonuses", value=bonus, inline=True)

            embed.add_field(name="Perks", value=user["perks"], inline=True)
            embed.add_field(name="Absence", value="Yes" if "absence" in user else "No", inline=True)
        embed.add_field(
            name="Join date",
            value=user["joined"].get("last", user["joined"]["first"]).strftime("%A, %B %d, %Y"),
            inline=True,
        )
        # embed.add_field(name="Trivia points", value=trivia_points, inline=True)
        if not enabled and "removal_reason" in user:
            embed.add_field(name="Reason for removal", value=user["removal_reason"], inline=False)
        if len(user["awards"]) > 0:
            embed.add_field(name="Awards", value="\u2063" + " ".join(user["awards"]), inline=True)

        if user["perks"] == "Pending" and requester_name.lower() == user["nickname"].lower():
            if clan_tag is not None:
                if clan_tag == "[RCT]":
                    perks_message = f"React with {rctbot.config.EMOJI_RCT} to claim your rewards now! Note that it may take several minutes for them to show up in your vault."
                    perks_ready_to_claim = True
                elif clan_tag in ["[FB]", "[GM]"]:
                    perks_message = "However, you likely own other volunteer or staff perks. Contact an SRCT if you don't want this message to show again."
                    perks_ready_to_claim = False
                else:
                    perks_message = "Unfortunately, you are not in the RCT clan. Please contact an SRCT to join the clan if you wish to claim your rewards."
                    perks_ready_to_claim = False
            else:
                perks_message = "Unfortunately, we could not retireve your clan tag. Please contact an SRCT if HoN servers are operational and you see this messsage."
                perks_ready_to_claim = False

            embed.add_field(
                name="Congratulations! You are eligible for the RCT Chat Symbol and Name Color!",
                value=perks_message,
                inline=False,
            )
        else:
            perks_ready_to_claim = False

        if user["perks"] == "Requested" and requester_name.lower() == user["nickname"].lower():
            embed.add_field(
                name="Did you receive your RCT Chat Symbol and Name Color?",
                value=f"React with {rctbot.config.EMOJI_YAY} if they are in your vault or with {rctbot.config.EMOJI_NAY} if they are not.",
                inline=False,
            )
        if requester_discord_id is not None:
            embed.set_footer(
                text=f"Requested by {requester_name} (✓). React with 🗑️ to delete or with 💾 to preserve this message. No action results in deletion after 5 minutes.",
                icon_url="https://i.imgur.com/q8KmQtw.png",
            )
        else:
            embed.set_footer(
                text="Requested by {.display_name} ({.name}#{.discriminator}). React with 🗑️ to delete or with 💾 to preserve this message. No action results in deletion after 5 minutes.".format(
                    ctx.author
                ),
                icon_url="https://i.imgur.com/q8KmQtw.png",
            )
        # embed.set_footer(text="React with 🆗 to delete this message.", icon_url="https://i.imgur.com/Ou1k4lD.png")
        # embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        embed.set_thumbnail(url=ranks[user["rank_id"]]["icon_url"])
        # embed.set_image(url="https://i.imgur.com/PlO2rtf.png") # Hmmm
        if user["signature"]["purchased"]:
            if user["signature"]["url"] != "":
                embed.set_image(url=user["signature"]["url"])
            else:
                embed.add_field(
                    name="You own a Discord Embedded Signature!",
                    value="Set it up using the `.signature` command to make Merrick even more jealous of you.",
                    inline=False,
                )
        message = await ctx.send(embed=embed)
        stop = timeit.default_timer()
        print(stop - start)
        await message.add_reaction("🗑️")
        await message.add_reaction("💾")
        if requester_name.lower() == user["nickname"].lower():
            await message.add_reaction(rctbot.config.EMOJI_GOLD_COINS)
        if perks_ready_to_claim and requester_name.lower() == user["nickname"].lower():
            await message.add_reaction(rctbot.config.EMOJI_RCT)
        if user["perks"] == "Requested" and requester_name.lower() == user["nickname"].lower():
            await message.add_reaction(rctbot.config.EMOJI_YAY)
            await message.add_reaction(rctbot.config.EMOJI_NAY)

        async def set_perks_status(status):
            return await self.testers.update_one(
                {"nickname": user["nickname"]},
                {"$set": {"perks": status}},
                collation={"locale": "en", "strength": 1},
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.author
                and str(reaction.emoji)
                in [
                    "🗑️",
                    "💾",
                    rctbot.config.EMOJI_GOLD_COINS,
                    rctbot.config.EMOJI_RCT,
                    rctbot.config.EMOJI_YAY,
                    rctbot.config.EMOJI_NAY,
                ]
                and reaction.message.id == message.id,
                timeout=300.0,
            )

            if reaction.emoji == "🗑️":
                await message.delete()

            if (
                str(reaction.emoji) == rctbot.config.EMOJI_RCT
                and perks_ready_to_claim
                and requester_name.lower() == user["nickname"].lower()
            ):
                async with ACPClient(admin=ctx.author, masterserver="ac") as acp:
                    if not await acp.add_perks(user["account_id"]):
                        return await ctx.send(f"{ctx.author.mention} Uh oh, something went wrong.")
                await set_perks_status("Requested")
                await ctx.send(
                    f"{ctx.author.mention} Done! Please use this command again to confirm whether you received the RCT Chat Symbol and Name Color after checking your in-game vault."
                )

            if (
                str(reaction.emoji) == rctbot.config.EMOJI_YAY
                and user["perks"] == "Requested"
                and requester_name.lower() == user["nickname"].lower()
            ):
                await set_perks_status("Yes")
                await ctx.send(f"{ctx.author.mention} Awesome! Thanks for using RCTBot.")

            if (
                str(reaction.emoji) == rctbot.config.EMOJI_NAY
                and user["perks"] == "Requested"
                and requester_name.lower() == user["nickname"].lower()
            ):
                await set_perks_status("Pending")
                await ctx.send(
                    f"{ctx.author.mention} Perks status set to Pending. You should be able to use the same command and request rewards again."
                )

            if (
                str(reaction.emoji) == rctbot.config.EMOJI_GOLD_COINS
                and requester_name.lower() == user["nickname"].lower()
            ):
                await message.clear_reactions()
                async with VPClient() as portal:
                    tokens = await portal.get_tokens(user["account_id"])
                embed.set_field_at(index=8, name="Tokens owned", value=tokens, inline=True)
                await message.edit(embed=embed)
                await message.add_reaction("🗑️")
                await message.add_reaction("💾")

                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: user == ctx.author
                        and str(reaction.emoji) in ["🗑️", "💾"]
                        and reaction.message.id == message.id,
                        timeout=300.0,
                    )

                    if reaction.emoji == "🗑️":
                        await message.delete()

                except:
                    await message.delete()

        except asyncio.TimeoutError:
            await message.delete()

    # FIXME: Command raised an exception: NotFound: 404 Not Found (error code: 10008): Unknown Message
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def signature(self, ctx):
        "Signature options"
        price = 1
        # member_discord_id = str(ctx.author.id)
        user = await self.testers.find_one({"discord_id": ctx.author.id})
        if not user:
            return await ctx.send(
                f"{ctx.author.mention} Signature is only available to registered RCT volunteers.",
                delete_after=7.5,
            )

        async def set_signature(url=None, purchase=False):
            if purchase:
                return await self.testers.update_one(
                    {"nickname": user["nickname"]},
                    {"$set": {"signature.purchased": True}},
                    collation={"locale": "en", "strength": 1},
                )
            if url is not None:
                return await self.testers.update_one(
                    {"nickname": user["nickname"]},
                    {"$set": {"signature.url": url}},
                    collation={"locale": "en", "strength": 1},
                )

        purchased = user["signature"]["purchased"]
        signature_url = user["signature"]["url"]

        if not purchased:
            desc = f"You do not own a Discord Embedded Signature.\n\nDue to it beings somewhat intrusive and breaking the layout of stats display in some cases, it costs {price} Volunteer Tokens. This is a one time purchase and it is purely cosmetic. It does not give any other benefits other than adding a personal touch to your RCT stats display."
        else:
            desc = "Options"

        embed = discord.Embed(
            title="Discord Embedded Signature",
            type="rich",
            description=desc,
            color=0xFF6600,
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=user["nickname"],
            icon_url=ctx.author.avatar_url,
        )

        if purchased:
            embed.add_field(name="Upload", value="⬆️", inline=True)
            if signature_url != "":
                embed.add_field(name="Clear", value="🗑️", inline=True)
                embed.set_image(url=signature_url)
        else:
            embed.add_field(name="Purchase", value="🛒", inline=True)

        embed.add_field(name="Cancel", value="❌", inline=True)
        embed.set_footer(
            text="Unlike Custom Account Icons, you may reupload your Discord Embedded Signature at no additional cost. Supports images up to 900 x 150 pixels, which means you can use the same signature for (or from) the Heroes of Newerth forums. Recommended image dimensions are 285 x 95 pixels.",
            icon_url="https://i.imgur.com/q8KmQtw.png",
        )

        message = await ctx.send(embed=embed)
        if purchased:
            await message.add_reaction("⬆️")
            if signature_url != "":
                await message.add_reaction("🗑️")
        else:
            await message.add_reaction("🛒")
        await message.add_reaction("❌")

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.author
                and str(reaction.emoji) in ["❌", "🗑️", "⬆️", "🛒"]
                and reaction.message.id == message.id,
                timeout=300.0,
            )
            await message.delete()

            if reaction.emoji == "🗑️" and signature_url != "":
                await set_signature("")
                await ctx.send(
                    f"{ctx.author.mention} Signature cleared! It may take up to a minute for changes to apply.",
                    delete_after=15.0,
                )

            if reaction.emoji == "🛒" and not purchased:
                confirmation = "I AM ABSOLUTELY SURE I WANT TO PURCHASE DISCORD EMBEDDED SIGNATURE"
                purchase_prompt = await ctx.send(
                    f"{ctx.author.mention} Are you **absolutely sure** you want to purchase **Discord Embedded Signature** for **{price} Volunteer Tokens**? This is irreversible and could leave you with negative tokens.\n\n Type `{confirmation}` to confirm this order, or anything else to cancel."
                )
                purchase_confirmation = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                )
                await purchase_prompt.delete()
                if purchase_confirmation.content != confirmation:
                    await purchase_confirmation.delete()
                    return await ctx.send(
                        f"{ctx.author.mention} Order cancelled.",
                        delete_after=15.0,
                    )
                await purchase_confirmation.delete()
                try:
                    async with VPClient() as portal:
                        await portal.mod_tokens(f'{user["nickname"]} -{price}')
                    await set_signature(purchase=True)
                    return await ctx.send(
                        f"{ctx.author.mention} Successfully purchased Discord Embedded Signature! Note that it may take up to a minute for the command to reflect changes.",
                        delete_after=30.0,
                    )
                except:
                    return await ctx.send(
                        f"{ctx.author.mention} Something went wrong, please try again.",
                        delete_after=15.0,
                    )

            if reaction.emoji == "⬆️" and purchased:
                do_it_now = await ctx.send(
                    f"{ctx.author.mention} Upload your signature as a message attachment in your next Discord message here."
                )
                # Needs timeout
                signature_message = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                )
                await do_it_now.delete()
                if len(signature_message.attachments) == 0:
                    return await ctx.send(
                        f"{ctx.author.mention} You did not attach an image! Use `.signature` to retry.",
                        delete_after=15.0,
                    )
                attachment = signature_message.attachments[0]
                # print(attachment.url)
                async with aiohttp.ClientSession() as session, session.get(attachment.url) as resp:
                    image_b = await resp.read()
                image_bio = BytesIO(image_b)
                try:
                    with Image.open(image_bio) as image_pil:
                        width, height = image_pil.size
                        print(width, height)
                        if width > 900 or height > 150:
                            await signature_message.delete()
                            return await ctx.send(
                                (
                                    f"{ctx.author.mention} Image exceeds maximum allowed dimensions of 900 x 150 pixels!"
                                    f" Use `.signature` to retry."
                                    f"\n\nRecommended dimensions: `285 x 95 pixels`"
                                    f"\nYour image dimensions: `{width} x {height} pixels`"
                                ),
                                delete_after=25.0,
                            )
                except:
                    await signature_message.delete()
                    return await ctx.send(
                        f"{ctx.author.mention} Unsupported file type! Use `.signature` to retry.",
                        delete_after=15.0,
                    )
                image_bio.seek(0)
                sigantures_channel = self.bot.get_channel(718465776172138497)
                uploaded_signature_message = await sigantures_channel.send(
                    f'{discord.utils.escape_markdown(user["nickname"])}',
                    file=discord.File(image_bio, filename=attachment.filename),
                )
                image_bio.close()
                await signature_message.delete()
                uploaded_signature_url = uploaded_signature_message.attachments[0].url
                await set_signature(uploaded_signature_url)
                await ctx.send(
                    f"{ctx.author.mention} Signature set!",
                    delete_after=15.0,
                )

        except:
            await message.delete()
