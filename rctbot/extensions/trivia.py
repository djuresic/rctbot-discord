# (c) 2020 ziep

import os
import json
import random
import asyncio
import datetime

import discord
from discord.ext import commands
import pymongo

import rctbot.config
from rctbot.core import checks
from rctbot.core.driver import AsyncDatabaseHandler, DatabaseHandler
from rctbot.core.utils import chunks, ordinal
from rctbot.core.paginator import EmbedPaginatorSession

from rctbot.extensions.trivia_config import TriviaConfig

os.environ["PYTHONASYNCIODEBUG"] = "1"
# pylint: disable=no-member
podium = ["🥇", "🥈", "🥉"]
ICONS = {
    "matches": "https://i.imgur.com/NYNZqKl.png",
    "most_kills": "https://i.imgur.com/J4lHd7N.png",
    "most_assists": "https://i.imgur.com/zjPs1Fd.png",
    "ladder": "https://i.imgur.com/e3Kenf0.png",
}


class TriviaGame(commands.Cog):
    db = DatabaseHandler.client["Trivia"]
    QUESTIONS = [x for x in (db["QUESTIONS"].find({"enabled": True}))]

    def __init__(self, bot):
        self.bot = bot
        self.db_client = AsyncDatabaseHandler.client
        self.db = self.db_client["Trivia"]
        self.question = ""
        self.answers = []
        self.has_answered = []
        self.bot_prefixes = []
        self.current_round = 0
        self.rounds = 1
        self.loop = None
        self.scoreboard = {}
        self.game_fut = None
        self.round_fut = None
        self.stats = {}
        self.length = 60
        self.pause = 5
        self.attempts = 2
        self.player_stats = {}
        self.game_stats = {"rounds": []}
        self.channel = None
        self.name = "Trivia"
        self.delay = 60.0

    @commands.group(aliases=["tr"], invoke_without_command=True)
    async def trivia(self, ctx):
        await ctx.send_help("trivia")

    @trivia.command()
    # Roles can be names or IDs.
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def setdate(self, ctx):
        await ctx.send("Enter the date in the following format: dd/mm/yyyy  hh:mm")

        def check(m):
            return m.author == ctx.author

        try:
            data = (await self.bot.wait_for("message", timeout=120.0, check=check)).content
        except asyncio.TimeoutError:
            return
        new_date = datetime.datetime.strptime(f"{data}:00", "%d/%m/%Y %H:%M:%S")
        time_to = new_date - datetime.datetime.now()
        await ctx.send(str(time_to))

    @trivia.command()
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def quick(self, ctx):
        await self.get_prefixes(ctx)
        self.channel = ctx.channel
        self.delay = 5.0
        self.length = 20
        self.rounds = 5
        if await self.confirm_options(ctx):

            self.loop = asyncio.get_event_loop()
            self.game_fut = asyncio.ensure_future(self.game())

            try:
                await self.game_fut
                await self.record_stats()
            except asyncio.CancelledError:
                pass
                """ try:
                    await self.record_stats()
                except:
                    print("Failed to record stats for cancelled game")"""
        else:
            await ctx.send("Aborting..")

    @trivia.command(aliases=["s"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    @commands.max_concurrency(1)
    async def start(self, ctx, channel: discord.TextChannel = None, delay: float = 60.0):
        """Starts a game of trivia"""
        self.delay = delay
        self.game_reset()
        if type(channel) == discord.channel.TextChannel:
            self.channel = channel
        else:
            self.channel = ctx.channel
            await ctx.send(f"Channel selected is {self.channel.mention}")
        await ctx.send("Name of the Trivia (No answer within 1 min sets the name to `Trivia`)")

        def check(m):
            return m.author == ctx.author

        try:
            self.name = (await self.bot.wait_for("message", timeout=60.0, check=check)).content
        except asyncio.TimeoutError:
            self.name = "Trivia"

        await ctx.send("Number of questions (max 50)")

        def round_check(m):
            try:
                return (
                    not m.author.bot
                    and not m.content[0] in self.bot_prefixes
                    and not m.content.startswith("//")
                    and not m.content.startswith(self.bot.user.mention)
                    and m.author.id == ctx.author.id
                    and 1 <= int(m.content) <= 50
                    and m.channel == ctx.channel
                )
            except:
                return False

        try:
            self.rounds = int((await self.bot.wait_for("message", timeout=30.0, check=round_check)).content)
        except asyncio.TimeoutError:
            self.rounds = 3
        self.current_round = 0
        # check if there are enough questions left
        if len(TriviaGame.QUESTIONS) < self.rounds:
            TriviaGame.QUESTIONS = await (self.db["QUESTIONS"].find({"enabled": True})).to_list(length=None)
        await ctx.send("Time per round in seconds (10-360)")

        def len_check(m):
            try:
                return (
                    not m.author.bot
                    and not m.content[0] in self.bot_prefixes
                    and not m.content.startswith("//")
                    and not m.content.startswith(self.bot.user.mention)
                    and m.author.id == ctx.author.id
                    and 10 <= int(m.content) <= 360
                    and m.channel == ctx.channel
                )
            except:
                return False

        try:
            self.length = int((await self.bot.wait_for("message", timeout=30.0, check=len_check)).content)
        except asyncio.TimeoutError:
            self.length = 60
        await ctx.send("Time **between** rounds in seconds (1-120)")

        def pause_check(m):
            try:
                return (
                    not m.author.bot
                    and not m.content[0] in self.bot_prefixes
                    and not m.content.startswith("//")
                    and not m.content.startswith(self.bot.user.mention)
                    and m.author.id == ctx.author.id
                    and 1 <= int(m.content) <= 120
                    and m.channel == ctx.channel
                )
            except:
                return False

        try:
            self.pause = int((await self.bot.wait_for("message", timeout=30.0, check=pause_check)).content)
        except asyncio.TimeoutError:
            self.pause = 3
        await ctx.send("Number of attemps per round (1-10)")

        def attempts_check(m):
            try:
                return (
                    not m.author.bot
                    and not m.content[0] in self.bot_prefixes
                    and not m.content.startswith("//")
                    and not m.content.startswith(self.bot.user.mention)
                    and m.author.id == ctx.author.id
                    and 1 <= int(m.content) <= 10
                    and m.channel == ctx.channel
                )
            except:
                return False

        try:
            self.attempts = int((await self.bot.wait_for("message", timeout=30.0, check=attempts_check)).content)
        except asyncio.TimeoutError:
            self.attempts = 1
        await self.get_prefixes(ctx)
        if await self.confirm_options(ctx):

            self.loop = asyncio.get_event_loop()
            self.game_fut = asyncio.ensure_future(self.game())
            try:
                await self.game_fut
                await self.record_stats()
            except asyncio.CancelledError:
                pass
                """ try:
                    await self.record_stats()
                except:
                    print("Failed to record stats for cancelled game")"""
        else:
            await ctx.send("Aborting..")

    @trivia.command()
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def setattempts(self, ctx, attempts: int):
        """Change the number of attempts per question and player"""
        self.attempts = int(attempts)
        await ctx.message.add_reaction("👌")

    @trivia.command(aliases=["pausetime"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def setpause(self, ctx, pause_time: int):
        """Adjust the pause time"""
        self.pause = int(pause_time)
        await ctx.message.add_reaction("👌")

    @trivia.command()
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def stop(self, ctx):
        """Exits the current game"""
        self.round_fut.cancel()
        self.game_fut.cancel()
        self.game_reset()
        await ctx.message.add_reaction("🆗")

    @trivia.command(name="answer", aliases=["a"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def current_state(self, ctx):
        """Take a peak at the answer"""
        a = self.answers if self.answers else "None"
        await ctx.send(a)

    @trivia.command()
    async def stats(self, ctx, member: discord.Member = None):
        """Stats for a player"""
        if not member:
            member = ctx.author
        if (player_stats := await self.fetch_player_stats(member)) :
            embed = discord.Embed(title="Player Stats", timestamp=ctx.message.created_at)
            embed.add_field(name="Games", value=player_stats["total_games"])
            embed.add_field(name="Points", value=player_stats["points"])
            embed.add_field(name="Rounds", value=player_stats["total_rounds"])
            embed.add_field(name="Wrong Answers", value=player_stats["wrong"])
            embed.set_author(name=member.display_name, icon_url=member.avatar_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't find that member.")

    @trivia.command(aliases=["ladder", "lbd", "ldr", "lb", "ld"])
    async def leaderboard(self, ctx, leaderboard="points"):
        """Player performance leaderboards."""
        # These words don't conflict so this approach is fine.
        games = leaderboard.lower() == "games"
        rounds = leaderboard.lower() == "rounds"
        points = leaderboard.lower() == "points"
        if points:
            title = "Points Leaderboard"
            find = {"active": True}
            key = "points"
            icon = ICONS["most_kills"]
        elif games:
            title = "Games Leaderboard"
            find = {"active": True}
            key = "total_games"
            icon = ICONS["matches"]
        elif rounds:
            title = "Rounds Leaderboard"
            find = {"active": True}
            key = "total_rounds"
            icon = ICONS["most_assists"]

        async def get_documents(find: dict, key: str) -> list:
            return await (self.db["PLAYERSTATS"].find(find).sort(key, pymongo.DESCENDING).to_list(length=None))

        documents = await get_documents(find, key)
        # Set comprehension to remove duplicates.
        values = [x[key] for x in documents]
        for i, val in enumerate(values):
            if val in values[:i]:
                values[i] = -1
        doc_chunks = chunks(documents, 20)
        embeds = []
        for chunk in doc_chunks:
            placements = []
            names = []
            amounts = []
            for player in chunk:
                place = ordinal(values.index(player[key]) + 1)
                name = f"<@!{player['_id']}>"
                amount = str(player[key])
                lines = ["", "", ""]
                lines[0] = place
                lines[1] = name
                lines[2] = amount
                placements.append(lines[0])
                names.append(lines[1])
                amounts.append(lines[2])
            placements = "\n" + "\n".join(placements) + ""
            names = "\n" + "\n".join(names) + ""
            amounts = "\n" + "\n".join(amounts) + ""
            embed = discord.Embed(title=title, type="rich", color=0xFF6600, timestamp=ctx.message.created_at,)
            embed.add_field(name="Rank", value=placements)
            embed.add_field(name="Player", value=names)
            embed.add_field(name=key, value=amounts)

            embed.set_author(name="Heroes of Newerth Trivia", icon_url="https://i.imgur.com/q8KmQtw.png")
            embed.set_thumbnail(url=icon)
            embed.set_footer(icon_url=ICONS["ladder"])
            embeds.append(embed)

        session = EmbedPaginatorSession(self.bot, ctx, *embeds)
        await session.run()

    """ @commands.command()
    async def t(self, ctx, times: int = 1):
        player_stats_collection = self.db["PLAYERSTATS"]
        for _ in range(times):
            ident = random.randint(266, 100000)
            points = random.randint(0, 25)
            wrong = random.randint(0, 25)
            total_rounds = random.randint(2, 36)
            total_games = points+wrong
            await player_stats_collection.insert_one({"_id": ident, "active": True, "points": points, "wrong": wrong, "total_rounds":
                                                      total_rounds, "total_games": total_games})
            return
            embed = discord.Embed(title="LEADERBOARD",
                                  timestamp=datetime.datetime.now())
        leaderboard_points = await self.fetch_leaderboard()
        leaderboard_games = await self.fetch_leaderboard(attr="total_games")
        leaderboard_rounds = await self.fetch_leaderboard(attr="total_rounds")
        points = " ,".join(
            [f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_points)]).replace(",", "")
        points_num = " ,".join(
            [f"**{x['points']}**\n" for i, x in enumerate(leaderboard_points)]).replace(",", "")
        games = " ,".join(
            [f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_games)]).replace(",", "")
        games_num = " ,".join(
            [f"**{x['total_games']}**\n" for i, x in enumerate(leaderboard_points)]).replace(",", "")
        rounds = " ,".join(
            [f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_rounds)]).replace(",", "")
        rounds_num = " ,".join(
            [f"**{x['total_rounds']}**\n" for i, x in enumerate(leaderboard_points)]).replace(",", "")
        embed.add_field(name="Points", value=points)
        embed.add_field(name="\u2063", value=points_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.add_field(name="Games", value=games)
        embed.add_field(name="\u2063", value=games_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.add_field(name="Rounds", value=rounds)
        embed.add_field(name="\u2063", value=rounds_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.set_author(name="Heroes of Newerth Trivia",
                         icon_url="https://i.imgur.com/q8KmQtw.png")
        embed.set_footer(text="Last updated ",)
        embed.set_thumbnail(
            url=ICONS["ladder"])
        await ctx.send(embed=embed) """

    async def game(self):
        while self.current_round < self.rounds:
            scoreboard_msg = ""
            leaderboard_msg = ""
            next_round_msg = await self.channel.send(f"Next round starting in {self.pause}..")
            await asyncio.sleep(1)
            i = 1
            while i < self.pause:
                await next_round_msg.edit(content=f"Next round starting in {self.pause-i}..")
                await asyncio.sleep(1)
                i += 1
            await next_round_msg.delete()
            self.round_fut = asyncio.ensure_future(asyncio.wait_for(self.round(self.length), timeout=self.length))
            try:
                await self.round_fut
            except asyncio.TimeoutError:
                if type(self.answers) == list:
                    await self.channel.send(f"The answer was **{self.answers[0]}**")
                elif type(self.answers) == str:
                    await self.channel.send(f"The answer was **{self.answers}**")
                await self.save_round_stats()
                self.round_reset()
            sorted_scoreboard = dict(sorted(self.scoreboard.items(), key=lambda x: x[1], reverse=True))
            for index, (key, value) in enumerate(sorted_scoreboard.items()):
                if index < 3 and self.current_round >= self.rounds:
                    scoreboard_msg += f"{podium[index]}{key}: **{value}**\n"
                else:
                    scoreboard_msg += f"{key}: **{value}**\n"
            if not scoreboard_msg:
                scoreboard_msg = "\u2063"
            embed = discord.Embed(title="Scoreboard")
            if not self.current_round > self.rounds:
                pass
            embed.add_field(name="\u2063", value=scoreboard_msg)

            await self.channel.send(embed=embed)

    async def round(self, length):

        self.current_round += 1
        await self.get_question()
        await self.channel.send(f"Round {self.current_round}/{self.rounds}: {self.question}")
        while True:

            def check(m):
                return (
                    not m.author.bot
                    and not m.content[0] in self.bot_prefixes
                    and not m.content.startswith("//")
                    and not m.content.startswith(self.bot.user.mention)
                    and m.channel == self.channel
                )

            try:
                msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                if not self.has_answered.count(msg.author) >= self.attempts:
                    if await self.do_guess(msg.content.lower()):
                        if type(self.answers) == list:
                            await self.channel.send(
                                f"{msg.author.mention} correct! The answer was **{self.answers[0]}**"
                            )
                        elif type(self.answers) == str:
                            await self.channel.send(f"{msg.author.mention} correct! The answer was **{self.answers}**")
                        self.has_answered.append(msg.author)
                        # await msg.add_reaction("✅") Not really necessary imho
                        if not msg.author.mention in self.scoreboard.keys():
                            self.scoreboard[msg.author.mention] = 1
                            self.player_stats[msg.author] = {"points": 1, "wrong": 0}
                        else:
                            self.player_stats[msg.author]["points"] += 1
                            self.scoreboard[msg.author.mention] += 1
                        if self.has_answered.count(msg.author) == 1:
                            if "rounds_played" in self.player_stats[msg.author].keys():
                                self.player_stats[msg.author]["rounds_played"] += 1
                                print("Adding one from correct")
                            else:
                                self.player_stats[msg.author]["rounds_played"] = 1
                                print("setting one from correct")
                        await self.save_round_stats(msg.author)
                        self.round_reset()
                        break
                    else:
                        self.has_answered.append(msg.author)
                        if msg.author in self.player_stats.keys():
                            self.player_stats[msg.author]["wrong"] += 1
                        else:
                            self.player_stats[msg.author] = {"points": 0, "wrong": 1}
                        if self.has_answered.count(msg.author) == 1:
                            if "rounds_played" in self.player_stats[msg.author].keys():
                                self.player_stats[msg.author]["rounds_played"] += 1
                                print("adding one from false")
                            else:
                                self.player_stats[msg.author]["rounds_played"] = 1
                                print("setting one from false")
            except asyncio.TimeoutError:
                await self.save_round_stats()
                self.round_reset()
                break

    async def fetch_player_stats(self, member: discord.Member):
        return await self.db["PLAYERSTATS"].find_one({"_id": member.id})

    async def fetch_leaderboard(self, attr="points", length=5):
        return await (self.db["PLAYERSTATS"].find({"active": True}).sort(attr, pymongo.DESCENDING)).to_list(length)

    async def record_stats(self):
        await self.prepare_stats()

        player_stats_collection = self.db["PLAYERSTATS"]
        game_stats_collection = self.db["GAMESTATS"]
        for key in self.player_stats.keys():
            player = self.player_stats[key]
            if not "points" in player.keys():
                player["points"] = 0
            if not "wrong" in player.keys():
                player["wrong"] = 0
            if not "rounds_played" in player.keys():
                player["rounds_played"] = 0
            if await player_stats_collection.find_one({"_id": key.id}):
                await player_stats_collection.update_one({"_id": key.id}, {"$set": {"active": True}})
                await player_stats_collection.update_one(
                    {"_id": key.id},
                    {
                        "$inc": {
                            "points": player["points"],
                            "wrong": player["wrong"],
                            "total_rounds": player["rounds_played"],
                            "total_games": 1,
                        }
                    },
                )
            else:
                await player_stats_collection.insert_one(
                    {
                        "_id": key.id,
                        "active": True,
                        "points": player["points"],
                        "wrong": player["wrong"],
                        "total_rounds": player["rounds_played"],
                        "total_games": 1,
                    }
                )
        await game_stats_collection.insert_one(self.game_stats)
        await self.update_leaderboard()

    async def save_round_stats(self, winner=None):
        # for key in self.player_stats.keys():
        # print(f"key: {key}")
        # print("rounds Played: ", self.player_stats[key]["rounds_played"])
        if winner:
            self.game_stats["rounds"].append(
                {
                    "question": self.question,
                    "answers": self.answers,
                    "winner": {
                        "name": f"{winner.name}#{winner.discriminator}",
                        "display_name": winner.display_name,
                        "id": winner.id,
                    },
                    "wrong": [
                        {"name": f"{x.name}#{x.discriminator}", "display_name": x.display_name, "id": x.id}
                        for x in self.has_answered
                    ],
                }
            )
        else:
            self.game_stats["rounds"].append(
                {
                    "question": self.question,
                    "answers": self.answers,
                    "wrong": [
                        {"name": f"{x.name}#{x.discriminator}", "display_name": x.display_name, "id": x.id}
                        for x in self.has_answered
                    ],
                }
            )

    async def prepare_stats(self):
        self.game_stats["settings"] = {
            "rounds": self.rounds,
            "round_length": self.length,
            "pause_time": self.pause,
            "attempts": self.attempts,
            "channel": {
                "name": self.channel.name if self.channel else None,
                "id": self.channel.id if self.channel else None,
            },
        }
        self.game_stats["_id"] = (
            max([x["_id"] for x in (await (self.db["GAMESTATS"].find({})).to_list(length=None))]) + 1
        )
        self.game_stats["date"] = datetime.datetime.now()

    async def update_leaderboard(self):
        if "leaderboard_msg_id" not in TriviaConfig.document:
            ldb_channel = discord.utils.get(self.channel.guild.channels, name="hall-of-fame")
            lbd_msg_exists = False
        else:
            ldb_channel = self.bot.get_channel(TriviaConfig.document["leaderboard_channel_id"])
            try:
                ldb_msg = await ldb_channel.fetch_message(TriviaConfig.document["leaderboard_msg_id"])
                lbd_msg_exists = True
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                lbd_msg_exists = False

        embed = discord.Embed(title="LEADERBOARD", type="rich", color=0xFF6600, timestamp=datetime.datetime.now())
        leaderboard_points = await self.fetch_leaderboard()
        leaderboard_games = await self.fetch_leaderboard(attr="total_games")
        leaderboard_rounds = await self.fetch_leaderboard(attr="total_rounds")
        points = " ,".join([f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_points)]).replace(
            ",", ""
        )
        points_num = " ,".join([f"**{x['points']}**\n" for i, x in enumerate(leaderboard_points)]).replace(",", "")
        games = " ,".join([f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_games)]).replace(
            ",", ""
        )
        games_num = " ,".join([f"**{x['total_games']}**\n" for i, x in enumerate(leaderboard_games)]).replace(",", "")
        rounds = " ,".join([f"{ordinal(i+1)} <@!{x['_id']}>\n" for i, x in enumerate(leaderboard_rounds)]).replace(
            ",", ""
        )
        rounds_num = " ,".join([f"**{x['total_rounds']}**\n" for i, x in enumerate(leaderboard_rounds)]).replace(
            ",", ""
        )
        embed.add_field(name="Points", value=points)
        embed.add_field(name="\u2063", value=points_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.add_field(name="Games", value=games)
        embed.add_field(name="\u2063", value=games_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.add_field(name="Rounds", value=rounds)
        embed.add_field(name="\u2063", value=rounds_num)
        embed.add_field(name="\u2063", value="\u2063")
        embed.set_author(name="Heroes of Newerth Trivia", icon_url="https://i.imgur.com/q8KmQtw.png")
        embed.set_footer(text="Last updated ")
        embed.set_thumbnail(url=ICONS["ladder"])
        if lbd_msg_exists:
            await ldb_msg.edit(embed=embed)
        else:
            lbd_msg = await ldb_channel.send(embed=embed)
            await TriviaConfig.set("leaderboard_channel_id", ldb_channel.id)
            await TriviaConfig.set("leaderboard_msg_id", lbd_msg.id)

    async def confirm_options(self, ctx):
        confirm = False
        embed = discord.Embed(
            title="Confirm game options", description="Respond with 'yes' to confirm or 'no' to cancel"
        )
        embed.add_field(
            name="OPTIONS",
            value=(
                "\n"
                f"**Number of rounds**          : **{self.rounds}**\n"
                f"**Channel**                   : **{self.channel.mention}**\n"
                f"**Time per round**            : **{self.length}**\n"
                f"**Time between rounds**       : **{self.pause}**\n"
                f"**Attempts per question**     : **{self.attempts}**\n"
            ),
        )

        def confirm_check(msg):
            return msg.author.id == ctx.author.id and msg.channel == ctx.channel

        await ctx.send(embed=embed)
        try:
            conf_msg = (await self.bot.wait_for("message", timeout=120.0, check=confirm_check)).content.lower()
            if conf_msg == "yes":
                confirm = True
                await self.send_game_info(ctx)
            elif conf_msg == "no":
                confirm = False
        except asyncio.TimeoutError:
            return False
        return confirm

    async def send_game_info(self, ctx):
        embed = discord.Embed(
            title=self.name[0].upper() + self.name[1:],
            description=f"The game is starting in {self.delay} seconds!",
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="Game Options",
            value=(
                "\n"
                f"**Number of rounds**          : **{self.rounds}**\n"
                f"**Channel**                   : **{self.channel.mention}**\n"
                f"**Time per round**            : **{self.length}**\n"
                f"**Time between rounds**       : **{self.pause}**\n"
                f"**Attempts per question**     : **{self.attempts}**\n"
            ),
        )
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        await self.channel.send(embed=embed)
        await asyncio.sleep(self.delay)

    async def do_guess(self, guess):
        return guess.casefold() in self.answers

    async def get_prefixes(self, ctx):
        self.bot_prefixes = [(x).replace(self.bot.user.mention, "") for x in (await self.bot.get_prefix(ctx.message))]

    async def get_question(self):
        q_doc = random.choice(TriviaGame.QUESTIONS)
        TriviaGame.QUESTIONS.remove(q_doc)
        self.question = q_doc["question"]
        self.answers = [s.casefold() for s in q_doc["answers"]]

    def round_reset(self):
        self.question = ""
        self.answers = []
        self.has_answered = []
        if self.round_fut:
            try:
                self.round_fut.cancel()
            except:
                pass
            self.round_fut = None

    def game_reset(self):
        self.game_stats = {"rounds": []}
        self.player_stats = {}
        self.round_reset()
        self.current_round = 0
        self.rounds = 0
        self.scoreboard = {}
        if self.game_fut:
            try:
                self.game_fut.cancel()
            except:
                pass
            self.game_fut = None

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.db["PLAYERSTATS"].find_one_and_update({"_id": member.id}, {"$set": {"active": False}})

    @trivia.command()
    async def git(self, ctx):
        """Sends the link to ziep's github repository, mainly used for dev purposes"""
        await ctx.send("https://github.com/ziepziep/DiscordTrivia")

    def cog_unload(self):
        self.game_reset()


def setup(bot):
    bot.add_cog(TriviaGame(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(TriviaGame(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
