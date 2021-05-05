# (c) 2020 ziep

import os
import random
import asyncio
import datetime


import discord
from discord.ext import commands
import pymongo

from rctbot.core.driver import AsyncDatabaseHandler, DatabaseHandler
from rctbot.core.utils import chunks, ordinal
from rctbot.core.paginator import EmbedPaginatorSession

from rctbot.extensions.trivia.config import TriviaConfig

os.environ["PYTHONASYNCIODEBUG"] = "1"
# pylint: disable=no-member
podium = ["🏆", "🥈", "🥉"]
ICONS = {
    "matches": "https://i.imgur.com/NYNZqKl.png",
    "most_kills": "https://i.imgur.com/J4lHd7N.png",
    "most_assists": "https://i.imgur.com/zjPs1Fd.png",
    "ladder": "https://i.imgur.com/e3Kenf0.png",
}
n2w = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}


class TriviaGame(commands.Cog):
    """Trivia game class."""

    DATABASE = DatabaseHandler.client["Trivia"]
    QUESTIONS = list(DATABASE["QUESTIONS"].find({"enabled": True}))

    def __init__(self, bot):
        self.bot = bot
        self.db_client = AsyncDatabaseHandler.client
        self.db = self.db_client["Trivia"]
        self.question = ""
        self.answers = []
        self.has_answered = []
        self.bot_prefixes = []
        self.current_round = 0
        self.loop = None
        self.scoreboard = {}
        self.game_fut = None
        self.round_fut = None
        self.stats = {}
        self.player_stats = {}
        self.game_stats = {"rounds": []}
        self.winners = []
        self.do_not_count_roles = []
        self.options = {
            "rounds": 1,
            "length": 60,
            "pause": 5,
            "attempts": 2,
            "channel": None,
            "admin_channel": None,
            "name": "Trivia",
            "delay": 60.0,
            "point_distribution": [3, 1, 1, 1, 1, 1, 1, 1],
            "repost": False,
            "mute_duration": 0.5,
        }

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

    @trivia.command(aliases=["q"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def quick(self, ctx, rounds: int = 5):
        self.game_reset()
        await self.get_prefixes(ctx)
        self.options["admin_channel"] = ctx.channel
        self.options["channel"] = ctx.channel
        self.options["delay"] = 5.0
        self.options["length"] = 20
        self.options["rounds"] = rounds
        if await self.confirm_options(ctx):

            self.loop = asyncio.get_event_loop()
            self.game_fut = asyncio.ensure_future(self.game())

            try:
                await self.game_fut
                await self.record_stats()
            except asyncio.CancelledError:
                pass  # pylint: disable=unnecessary-pass

        else:
            await ctx.send("Aborting..")

    @trivia.command(aliases=["s"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    @commands.max_concurrency(1)
    async def start(self, ctx, *args):
        """Starts a game of trivia"""
        self.game_reset()
        self.do_not_count_roles = [
            discord.utils.get(ctx.guild.roles, name=name) for name in TriviaConfig.document["do_not_count_roles"]
        ]
        await self.bot.change_presence(
            activity=discord.Activity(name="HoN Trivia", type=discord.ActivityType.playing),
            status=discord.Status.online,
            afk=False,
        )
        try:
            self.options["rounds"] = (
                int(args[args.index("--rounds") + 1]) if "--rounds" in args else self.options["rounds"]
            )
            self.options["length"] = (
                int(args[args.index("--length") + 1]) if "--length" in args else self.options["length"]
            )
            self.options["pause"] = (
                int(args[args.index("--pause") + 1]) if "--pause" in args else self.options["pause"]
            )
            self.options["attempts"] = (
                int(args[args.index("--attempts") + 1]) if "--attempts" in args else self.options["attempts"]
            )
            self.options["channel"] = (
                await commands.TextChannelConverter().convert(ctx, (args[args.index("--channel") + 1]))
                if "--channel" in args
                else ctx.channel
            )
            self.options["admin_channel"] = (
                await commands.TextChannelConverter().convert(ctx, args[args.index("--admin_channel") + 1])
                if "--admin_channel" in args
                else ctx.channel
            )
            self.options["name"] = args[args.index("--name") + 1] if "--name" in args else self.options["name"]

            self.options["repost"] = "--repost" in args
            self.options["delay"] = (
                int(args[args.index("--delay") + 1]) if "--delay" in args else self.options["delay"]
            )
            self.options["mute_duration"] = (
                float(args[args.index("--mute") + 1]) if "--mute" in args else self.options["mute_duration"]
            )
        except Exception as e:
            print(e)
            await ctx.send("Invalid arguments!")
            return
        await self.get_prefixes(ctx)
        if await self.confirm_options(ctx):

            self.loop = asyncio.get_event_loop()
            self.game_fut = asyncio.ensure_future(self.game())
            try:
                await self.game_fut
                await self.record_stats()
            except asyncio.CancelledError:
                pass
        else:
            await ctx.send("Aborting..")

    @trivia.command(aliases=["oldstart"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    @commands.max_concurrency(1)
    async def old_start(self, ctx, channel: discord.TextChannel = None, delay: float = 60.0, *, args=""):
        """Starts a game of trivia"""
        self.options["repost"] = "--repost" in args
        self.options["delay"] = delay
        self.game_reset()
        self.options["admin_channel"] = ctx.channel
        await self.bot.change_presence(
            activity=discord.Activity(name="HoN Trivia", type=discord.ActivityType.playing),
            status=discord.Status.online,
            afk=False,
        )
        if isinstance(channel, discord.channel.TextChannel):
            self.options["channel"] = channel
        else:
            self.options["channel"] = ctx.channel
            await ctx.send(f"Channel selected is {self.options['channel'].mention}")
        await self.options["channel"].edit(topic="Trivia is live!")
        await ctx.send("Name of the Trivia (No answer within 1 min sets the name to `Trivia`)")

        def check(m):
            return m.author == ctx.author

        try:
            self.options["name"] = (await self.bot.wait_for("message", timeout=60.0, check=check)).content
        except asyncio.TimeoutError:
            self.options["name"] = "Trivia"

        await ctx.send("Number of questions")
        try:
            self.options["rounds"] = int((await self.bot.wait_for("message", timeout=30.0, check=self.check)).content)
        except asyncio.TimeoutError:
            self.options["rounds"] = 3
        self.current_round = 0
        # check if there are enough questions left
        if len(TriviaGame.QUESTIONS) < self.options["rounds"]:
            TriviaGame.QUESTIONS = await (self.db["QUESTIONS"].find({"enabled": True})).to_list(length=None)
        await ctx.send("Time per round in seconds")

        try:
            self.options["length"] = int((await self.bot.wait_for("message", timeout=30.0, check=self.check)).content)
        except asyncio.TimeoutError:
            self.options["length"] = 60
        await ctx.send("Time **between** rounds in seconds")

        try:
            self.options["pause"] = int((await self.bot.wait_for("message", timeout=30.0, check=self.check)).content)
        except asyncio.TimeoutError:
            self.options["pause"] = 3
        await ctx.send("Number of attemps per round")

        try:
            self.options["attempts"] = int(
                (await self.bot.wait_for("message", timeout=30.0, check=self.check)).content
            )
        except asyncio.TimeoutError:
            self.options["attempts"] = 1
        await self.get_prefixes(ctx)
        if await self.confirm_options(ctx):

            self.loop = asyncio.get_event_loop()
            self.game_fut = asyncio.ensure_future(self.game())
            try:
                await self.game_fut
                await self.record_stats()
            except asyncio.CancelledError:
                pass
                # try:
                #    await self.record_stats()
                # except:
                #    print("Failed to record stats for cancelled game")
        else:
            await ctx.send("Aborting..")

    @trivia.command()
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def setattempts(self, ctx, attempts: int):
        """Change the number of attempts per question and player"""
        self.options["attempts"] = int(attempts)
        await ctx.message.add_reaction("👌")

    @trivia.command(aliases=["pausetime"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def setpause(self, ctx, pause_time: int):
        """Adjust the pause time"""
        self.options["pause"] = int(pause_time)
        await ctx.message.add_reaction("👌")

    @trivia.command()
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def stop(self, ctx):
        """Exits the current game"""
        try:

            self.round_fut.cancel()
        except:
            pass
        try:
            self.game_fut.cancel()
        except:
            pass
        self.game_reset()
        await ctx.message.add_reaction("🆗")

    @trivia.command(name="answer", aliases=["a"])
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def show_answer(self, ctx):
        """Take a peak at the answer"""
        a = self.answers if self.answers else "None"
        await ctx.send(a)

    @trivia.command()
    async def stats(self, ctx, member: discord.Member = None):
        """Stats for a player"""
        if not member:
            member = ctx.author
        if (player_stats := await self.fetch_player_stats(member)) :  # pyint: disable=superfluous-parens
            embed = discord.Embed(title="Trivia: Player Stats", timestamp=ctx.message.created_at)
            embed.add_field(name="Games", value=player_stats["total_games"])
            embed.add_field(name="Rounds", value=player_stats["total_rounds"])
            embed.add_field(name="Points", value=player_stats["points"])
            embed.add_field(name="Available Tokens", value=player_stats["tokens"])
            embed.add_field(name="Correct Answers", value=player_stats["correct"])
            embed.add_field(name="Incorrect Answers", value=player_stats["wrong"])
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
            embed = discord.Embed(
                title=title,
                type="rich",
                color=0xFF6600,
                timestamp=ctx.message.created_at,
            )
            embed.add_field(name="Rank", value=placements)
            embed.add_field(name="Player", value=names)
            embed.add_field(name=title.split(" ")[0], value=amounts)

            embed.set_author(name="Heroes of Newerth Trivia", icon_url="https://i.imgur.com/q8KmQtw.png")
            embed.set_thumbnail(url=icon)
            embed.set_footer(icon_url=ICONS["ladder"])
            embeds.append(embed)

        session = EmbedPaginatorSession(self.bot, ctx, *embeds)
        await session.run()

    async def game(self):
        while self.current_round < self.options["rounds"]:
            scoreboard_msg = ""
            time_str = str(self.options["pause"])
            text = ""
            for num in time_str:
                text += f":{n2w[num]}:"
            await asyncio.sleep(1)
            i = 1
            while i < self.options["pause"]:
                if self.options["pause"] - i == 10:
                    await self.options["channel"].send(
                        ":octagonal_sign: Prepare for the next question in :one::zero: seconds, mute in :five: seconds :octagonal_sign:"
                    )
                elif not (self.options["pause"] - i) % 10:
                    time_str = str(self.options["pause"] - i)
                    text = ""
                    for num in time_str:
                        text += f":{n2w[num]}:"
                    await self.options["channel"].send(content=f"Next round starting in {text} seconds")
                if self.options["pause"] - i == 6:
                    await self.options["channel"].set_permissions(
                        self.options["channel"].guild.default_role, send_messages=False
                    )
                elif (self.options["pause"] - i) <= 5:
                    await self.options["channel"].send(f":{n2w[str(self.options['pause']-i)]}:")
                await asyncio.sleep(1)
                i += 1
            self.round_fut = asyncio.ensure_future(
                asyncio.wait_for(self.round(self.options["length"]), timeout=self.options["length"])
            )
            try:
                await self.round_fut
            except asyncio.TimeoutError:
                pass
            await self.save_round_stats()
            if self.winners:
                winners_str = ""
                for winner in self.winners:
                    winners_str += winner.mention + " "
                if isinstance(self.answers, list):
                    correct_answer = ", ".join(self.answers)
                    if len(self.answers) > 1:
                        before_answer_str = "Answers were"
                    else:
                        before_answer_str = "The answer was"
                elif isinstance(self.answers, str):
                    correct_answer = self.answers
                    before_answer_str = "The answer was"

                await self.options["channel"].send(
                    f"**Time's up!** {before_answer_str}: **{correct_answer}**\nGood job! {winners_str}"
                )
            self.round_reset()
            self.scoreboard = [(key, value["points"]) for (key, value) in self.player_stats.items()]
            sorted_scoreboard = dict(sorted(self.scoreboard, key=lambda x: x[1], reverse=True))
            for index, (key, value) in enumerate(sorted_scoreboard.items()):
                if index < 3 and self.current_round >= self.options["rounds"]:
                    scoreboard_msg += f"{podium[index]}{key.mention}: **{value}**\n"
                elif index < 25:
                    if key in self.winners:
                        scoreboard_msg += f"{key.mention}: **{value}** +{self.options['point_distribution'][self.winners.index(key)]}\n"
                    else:
                        scoreboard_msg += f"{key.mention}: **{value}**\n"
                else:
                    break
            if not scoreboard_msg:
                scoreboard_msg = "\u2063"
            embed = discord.Embed(title="Scoreboard", description=scoreboard_msg)
            if not self.current_round > self.options["rounds"]:
                pass

            await self.options["channel"].send(embed=embed)
        await self.bot.change_presence(
            activity=discord.Activity(name="Heroes of Newerth", type=discord.ActivityType.watching),
            status=discord.Status.dnd,
            afk=False,
        )

    async def round(self, length):
        self.current_round += 1
        self.winners = []
        msg_count = 0
        await self.get_question()
        await self.options["channel"].send(
            f"Round {self.current_round}/{self.options['rounds']}: **{discord.utils.escape_markdown(self.question)}**"
        )
        await asyncio.sleep(self.options["mute_duration"])
        await self.options["channel"].set_permissions(self.options["channel"].guild.default_role, send_messages=True)
        # await self.options["channel"].edit(topic=discord.utils.escape_markdown(self.question))

        def check(m):
            return (
                not m.author.bot
                and not len(m.content) == 0
                and not m.content[0] in self.bot_prefixes
                and not m.content.startswith("//")
                and not m.content.startswith(self.bot.user.mention)
                and m.channel == self.options["channel"]
                and not any(role in m.author.roles for role in self.do_not_count_roles)
            )

        while True:
            try:
                msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                msg_count += 1
                if msg_count % 12 == 0 and self.options["repost"]:
                    await self.options["channel"].send(
                        f"Round {self.current_round}/{self.options['rounds']}: **{discord.utils.escape_markdown(self.question)}**"
                    )
                # print(msg.content)
                # await msg.delete()
                if (
                    not self.has_answered.count(msg.author) >= self.options["attempts"]
                    and msg.author not in self.winners
                ):
                    self.has_answered.append(msg.author)

                    if await self.do_guess(msg.content.lower()):
                        self.winners.append(msg.author)
                        if len(self.winners) >= len(self.options["point_distribution"]):
                            await self.save_round_stats()
                            self.round_reset()
                            break
                    else:
                        pass

            except asyncio.TimeoutError:
                await self.save_round_stats()
                self.round_reset()
                break

    def check(self, m):
        """General check method for awaiting messages"""
        return (
            not m.author.bot
            and not len(m.content) == 0
            and not m.content[0] in self.bot_prefixes
            and not m.content.startswith("//")
            and not m.content.startswith(self.bot.user.mention)
            and m.channel == self.options["admin_channel"]
        )

    async def fetch_player_stats(self, member: discord.Member):
        return await self.db["PLAYERSTATS"].find_one({"_id": member.id})

    async def fetch_leaderboard(self, attr="points", length=5):
        return await (self.db["PLAYERSTATS"].find({"active": True}).sort(attr, pymongo.DESCENDING)).to_list(length)

    async def record_stats(self):
        await self.prepare_stats()

        player_stats_collection = self.db["PLAYERSTATS"]
        game_stats_collection = self.db["GAMESTATS"]
        for key in self.player_stats:
            player = self.player_stats[key]
            if await player_stats_collection.find_one({"_id": key.id}):
                await player_stats_collection.update_one({"_id": key.id}, {"$set": {"active": True}})
                await player_stats_collection.update_one(
                    {"_id": key.id},
                    {
                        "$inc": {
                            "points": player["points"],
                            "correct": player["correct"],
                            "wrong": player["wrong"],
                            "total_rounds": player["correct"] + player["wrong"],
                            "total_games": 1,
                            "tokens": player["points"],
                        },
                        "$set": {"active": True},
                    },
                )
            else:
                await player_stats_collection.insert_one(
                    {
                        "_id": key.id,
                        "active": True,
                        "points": player["points"],
                        "correct": player["correct"],
                        "wrong": player["wrong"],
                        "total_rounds": player["correct"] + player["wrong"],
                        "total_games": 1,
                        "tokens": player["points"],
                    }
                )
        await game_stats_collection.insert_one(self.game_stats)
        await self.update_leaderboard()

    async def save_round_stats(self):

        winners = []
        losers = list(set(self.has_answered))
        for i, winner in enumerate(self.winners):
            winners.append(
                {"name": f"{winner.name}#{winner.discriminator}", "display_name": winner.display_name, "id": winner.id}
            )
            if player := self.player_stats.get(winner):
                if "points" in player:
                    self.player_stats[winner]["points"] += self.options["point_distribution"][i]
                    self.player_stats[winner]["correct"] += 1
                else:
                    self.player_stats[winner]["points"] = self.options["point_distribution"][i]
                    self.player_stats[winner]["correct"] = 1
            else:
                self.player_stats[winner] = {"points": self.options["point_distribution"][i], "correct": 1, "wrong": 0}
        for i, loser in enumerate(losers):
            if player := self.player_stats.get(loser):
                if "wrong" in player:
                    self.player_stats[loser]["wrong"] += self.has_answered.count(loser) - self.winners.count(loser)
                else:
                    self.player_stats[loser]["wrong"] = self.has_answered.count(loser) - self.winners.count(loser)
            else:
                self.player_stats[loser] = {
                    "points": 0,
                    "correct": 0,
                    "wrong": self.has_answered.count(loser) - self.winners.count(loser),
                }
        self.game_stats["rounds"].append(
            {
                "question": self.question,
                "answers": self.answers,
                "winners": winners,
                "wrong": [
                    {"name": f"{x.name}#{x.discriminator}", "display_name": x.display_name, "id": x.id}
                    for x in self.has_answered
                ],
            }
        )

    async def prepare_stats(self):
        self.game_stats["settings"] = {
            "name": self.options["name"],
            "rounds": self.options["rounds"],
            "round_length": self.options["length"],
            "pause_time": self.options["pause"],
            "attempts": self.options["attempts"],
            "repost": self.options["repost"],
            "point_distribution": self.options["point_distribution"],
            "mute_duration": self.options["mute_duration"],
            "channel": {
                "name": self.options["channel"].name if self.options["channel"] else None,
                "id": self.options["channel"].id if self.options["channel"] else None,
            },
        }
        self.game_stats["_id"] = (
            max([x["_id"] for x in (await (self.db["GAMESTATS"].find({})).to_list(length=None))]) + 1
        )
        self.game_stats["date"] = datetime.datetime.now()

    async def update_leaderboard(self):
        if "leaderboard_msg_id" not in TriviaConfig.document:
            ldb_channel = discord.utils.get(self.options["channel"].guild.channels, name="hall-of-fame")
            lbd_msg_exists = False
        else:
            ldb_channel = self.bot.get_channel(TriviaConfig.document["leaderboard_channel_id"])
            try:
                ldb_msg = await ldb_channel.fetch_message(TriviaConfig.document["leaderboard_msg_id"])
                lbd_msg_exists = True
            except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError):
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
                f"**Number of rounds**          : **{self.options['rounds']}**\n"
                f"**Channel**                   : **{self.options['channel'].mention}**\n"
                f"**Time per round**            : **{self.options['length']}**\n"
                f"**Time between rounds**       : **{self.options['pause']}**\n"
                f"**Attempts per question**     : **{self.options['attempts']}**\n"
                f"**Repost questions**            : **{self.options['repost']}**"
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
            title=self.options["name"][0].upper() + self.options["name"][1:],
            description=f"The game is starting in {self.options['delay']} seconds!",
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="Game Options",
            value=(
                "\n"
                f"**Number of rounds**          : **{self.options['rounds']}**\n"
                f"**Channel**                   : **{self.options['channel'].mention}**\n"
                f"**Time per round**            : **{self.options['length']}**\n"
                f"**Time between rounds**       : **{self.options['pause']}**\n"
                f"**Attempts per question**     : **{self.options['attempts']}**\n"
            ),
        )
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        await self.options["channel"].send(embed=embed)
        await asyncio.sleep(self.options["delay"])

    async def do_guess(self, guess):
        return (
            guess.lower() in [a.lower() for a in self.answers]
            if isinstance(self.answers, list)
            else guess.lower() in self.answers.lower()
        )

    async def get_prefixes(self, ctx):
        self.bot_prefixes = [(x).replace(self.bot.user.mention, "") for x in (await self.bot.get_prefix(ctx.message))]

    async def get_question(self):
        q_doc = random.choice(TriviaGame.QUESTIONS)
        TriviaGame.QUESTIONS.remove(q_doc)
        self.question = q_doc["question"]
        self.answers = q_doc["answers"]

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
        self.options = {
            "rounds": 1,
            "length": 60,
            "pause": 5,
            "attempts": 2,
            "channel": None,
            "admin_channel": None,
            "name": "Trivia",
            "delay": 60.0,
            "point_distribution": [3, 1, 1, 1, 1, 1, 1, 1],
            "repost": False,
        }
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

    def cog_unload(self):
        self.game_reset()
