import discord
from discord.ext import commands

import rctbot.config
from rctbot.core import checks
from rctbot.core.mongodb import CLIENT


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        # TODO: Since cycle snapshots are saved it's possible to load past tester data.
        # self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        # self.testing_cycles = self.db[rctbot.config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

    @commands.command()
    @checks.is_senior()
    async def leaderboard(self, ctx):
        """Player performance leaderboard."""
        games = await (
            self.testers.find(
                {"enabled": True}, {"_id": 0, "nickname": 1, "games": 1}, sort=list({"games": -1}.items())
            )
        ).to_list(length=10)
        bugs = await (
            self.testers.find({"enabled": True}, {"_id": 0, "nickname": 1, "bugs": 1}, sort=list({"bugs": -1}.items()))
        ).to_list(length=10)
        tokens = await (
            self.testers.find(
                {"enabled": True}, {"_id": 0, "nickname": 1, "tokens": 1}, sort=list({"tokens": -1}.items())
            )
        ).to_list(length=10)
        total_games = await (
            self.testers.find({}, {"_id": 0, "nickname": 1, "total_games": 1}, sort=list({"total_games": -1}.items()))
        ).to_list(length=10)
        total_bugs = await (
            self.testers.find({}, {"_id": 0, "nickname": 1, "total_bugs": 1}, sort=list({"total_bugs": -1}.items()))
        ).to_list(length=10)

        def format_leaderboard_for_discord(sorted_list: list, dict_key: str, leaderboard_stat: str) -> list:
            return [
                "{place}.{ws_1} {nickname}{ws_2} {value}{ws_3} {stat}".format(
                    place=i + 1,
                    ws_1=(3 - len(str(i + 1))) * " ",
                    nickname=sorted_list[i]["nickname"],
                    ws_2=(14 - len(sorted_list[i]["nickname"])) * " ",
                    value=sorted_list[i][dict_key],
                    ws_3=(5 - len(str(sorted_list[i][dict_key]))) * " ",
                    stat=leaderboard_stat,
                )
                for i in range(len(sorted_list))
            ]

        fmt_games = format_leaderboard_for_discord(games, "games", "games")
        fmt_bugs = format_leaderboard_for_discord(bugs, "bugs", "bug reports")
        fmt_tokens = format_leaderboard_for_discord(tokens, "tokens", "tokens")
        fmt_total_games = format_leaderboard_for_discord(total_games, "total_games", "games")
        fmt_total_bugs = format_leaderboard_for_discord(total_bugs, "total_bugs", "bug reports")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/games.png", filename="games.png"))
        await ctx.send("```\n" + "\n".join(fmt_games) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/bugs.png", filename="bugs.png"))
        await ctx.send("```\n" + "\n".join(fmt_bugs) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/tokens.png", filename="tokens.png"))
        await ctx.send("```\n" + "\n".join(fmt_tokens) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/atgames.png", filename="atgames.png"))
        await ctx.send("```\n" + "\n".join(fmt_total_games) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/atbugs.png", filename="atbugs.png"))
        await ctx.send("```\n" + "\n".join(fmt_total_bugs) + "```")

        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def legacyleaderboard(self, ctx):
        """Legacy player performance leaderboard.
        
        This uses Google Sheets.
        """
        list_of_lists = rctbot.config.LIST_OF_LISTS
        offset = 2  # The first 2 rows are reserved.

        # This testing cycle.
        players = [list_of_lists[x][1] for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"]
        games = [int(list_of_lists[x][2]) for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"]
        bugs = [int(list_of_lists[x][4]) for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"]
        tokens = [int(list_of_lists[x][8]) for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"]

        # Total games (all-time).
        at_games = [
            int(list_of_lists[x][5]) for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"
        ]
        at_bugs = [
            int(list_of_lists[x][7]) for x in range(offset, len(list_of_lists)) if list_of_lists[x][0] != "None"
        ]

        leaderboard_len = len(players)

        # Create a list of tuples and sort it later.
        unsorted_leaderboard = []

        for i in range(leaderboard_len):
            unsorted_leaderboard.append((players[i], games[i], bugs[i], tokens[i], at_games[i], at_bugs[i]))

        sorted_by_games = sorted(unsorted_leaderboard, key=lambda unsorted_tuples: unsorted_tuples[1], reverse=True,)
        sorted_by_bugs = sorted(unsorted_leaderboard, key=lambda unsorted_tuples: unsorted_tuples[2], reverse=True,)
        sorted_by_tokens = sorted(unsorted_leaderboard, key=lambda unsorted_tuples: unsorted_tuples[3], reverse=True,)

        sorted_by_at_games = sorted(
            unsorted_leaderboard, key=lambda unsorted_tuples: unsorted_tuples[4], reverse=True,
        )
        sorted_by_at_bugs = sorted(unsorted_leaderboard, key=lambda unsorted_tuples: unsorted_tuples[5], reverse=True,)

        leaderboard_games = [
            # f"{i+1}. {discord.utils.escape_markdown(sorted_by_games[i][0])}: {sorted_by_games[i][1]} games"
            "{}.{} {}{} {}{} games".format(
                i + 1,
                (3 - len(str(i + 1))) * " ",
                sorted_by_games[i][0],
                (14 - len(sorted_by_games[i][0])) * " ",
                sorted_by_games[i][1],
                (3 - len(str(sorted_by_games[i][1]))) * " ",
            )
            for i in range(leaderboard_len)
        ]
        leaderboard_bugs = [
            # f"{i+1}. {discord.utils.escape_markdown(sorted_by_bugs[i][0])}: {sorted_by_bugs[i][2]} bug reports"
            "{}.{} {}{} {}{} bug reports".format(
                i + 1,
                (3 - len(str(i + 1))) * " ",
                sorted_by_bugs[i][0],
                (14 - len(sorted_by_bugs[i][0])) * " ",
                sorted_by_bugs[i][2],
                (3 - len(str(sorted_by_bugs[i][2]))) * " ",
            )
            for i in range(leaderboard_len)
        ]
        leaderboard_tokens = [
            # f"{i+1}. {discord.utils.escape_markdown(sorted_by_tokens[i][0])}: {sorted_by_tokens[i][3]} tokens"
            "{}.{} {}{} {}{} tokens".format(
                i + 1,
                (3 - len(str(i + 1))) * " ",
                sorted_by_tokens[i][0],
                (14 - len(sorted_by_tokens[i][0])) * " ",
                sorted_by_tokens[i][3],
                (5 - len(str(sorted_by_tokens[i][3]))) * " ",
            )
            for i in range(leaderboard_len)
        ]

        leaderboard_at_games = [
            # f"{i+1}. {discord.utils.escape_markdown(sorted_by_at_games[i][0])}: {sorted_by_at_games[i][4]} games"
            "{}.{} {}{} {}{} games".format(
                i + 1,
                (3 - len(str(i + 1))) * " ",
                sorted_by_at_games[i][0],
                (14 - len(sorted_by_at_games[i][0])) * " ",
                sorted_by_at_games[i][4],
                (5 - len(str(sorted_by_at_games[i][4]))) * " ",
            )
            for i in range(leaderboard_len)
        ]
        leaderboard_at_bugs = [
            # f"{i+1}. {discord.utils.escape_markdown(sorted_by_at_bugs[i][0])}: {sorted_by_at_bugs[i][5]} bug reports"
            "{}.{} {}{} {}{} bug reports".format(
                i + 1,
                (3 - len(str(i + 1))) * " ",
                sorted_by_at_bugs[i][0],
                (14 - len(sorted_by_at_bugs[i][0])) * " ",
                sorted_by_at_bugs[i][5],
                (4 - len(str(sorted_by_at_bugs[i][5]))) * " ",
            )
            for i in range(leaderboard_len)
        ]

        await ctx.send(file=discord.File("rctbot/res/leaderboard/games.png", filename="games.png"))
        await ctx.send("```\n" + "\n".join(leaderboard_games[:10]) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/bugs.png", filename="bugs.png"))
        await ctx.send("```\n" + "\n".join(leaderboard_bugs[:10]) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/tokens.png", filename="tokens.png"))
        await ctx.send("```\n" + "\n".join(leaderboard_tokens[:10]) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/atgames.png", filename="atgames.png"))
        await ctx.send("```\n" + "\n".join(leaderboard_at_games[:10]) + "```")

        await ctx.send(file=discord.File("rctbot/res/leaderboard/atbugs.png", filename="atbugs.png"))
        await ctx.send("```\n" + "\n".join(leaderboard_at_bugs[:10]) + "```")

        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Leaderboard(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Leaderboard(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
