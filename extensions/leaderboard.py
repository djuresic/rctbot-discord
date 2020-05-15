import asyncio

import discord
from discord.ext import commands

import core.perseverance
import core.config as config
from core.checks import is_tester, is_senior
import core.spreadsheet as spreadsheet


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_senior()
    async def leaderboard(self, ctx, player: discord.Member = None):
        """Player performance leaderboard."""
        list_of_lists = config.LIST_OF_LISTS
        offset = 2  # The first 2 rows are reserved.

        # This testing cycle.
        players = [
            list_of_lists[x][1]
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]
        games = [
            int(list_of_lists[x][2])
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]
        bugs = [
            int(list_of_lists[x][4])
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]
        tokens = [
            int(list_of_lists[x][8])
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]

        # Total games (all-time).
        at_games = [
            int(list_of_lists[x][5])
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]
        at_bugs = [
            int(list_of_lists[x][7])
            for x in range(offset, len(list_of_lists))
            if list_of_lists[x][0] != "None"
        ]

        leaderboard_len = len(players)

        # Create a list of tuples and sort it later.
        unsorted_leaderboard = []

        for i in range(leaderboard_len):
            unsorted_leaderboard.append(
                (players[i], games[i], bugs[i], tokens[i], at_games[i], at_bugs[i])
            )

        sorted_by_games = sorted(
            unsorted_leaderboard,
            key=lambda unsorted_tuples: unsorted_tuples[1],
            reverse=True,
        )
        sorted_by_bugs = sorted(
            unsorted_leaderboard,
            key=lambda unsorted_tuples: unsorted_tuples[2],
            reverse=True,
        )
        sorted_by_tokens = sorted(
            unsorted_leaderboard,
            key=lambda unsorted_tuples: unsorted_tuples[3],
            reverse=True,
        )

        sorted_by_at_games = sorted(
            unsorted_leaderboard,
            key=lambda unsorted_tuples: unsorted_tuples[4],
            reverse=True,
        )
        sorted_by_at_bugs = sorted(
            unsorted_leaderboard,
            key=lambda unsorted_tuples: unsorted_tuples[5],
            reverse=True,
        )

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

        await ctx.send(
            file=discord.File("res/leaderboard/games.png", filename="games.png")
        )
        await ctx.send("```\n" + "\n".join(leaderboard_games[:10]) + "```")

        await ctx.send(
            file=discord.File("res/leaderboard/bugs.png", filename="bugs.png")
        )
        await ctx.send("```\n" + "\n".join(leaderboard_bugs[:10]) + "```")

        await ctx.send(
            file=discord.File("res/leaderboard/tokens.png", filename="tokens.png")
        )
        await ctx.send("```\n" + "\n".join(leaderboard_tokens[:10]) + "```")

        await ctx.send(
            file=discord.File("res/leaderboard/atgames.png", filename="atgames.png")
        )
        await ctx.send("```\n" + "\n".join(leaderboard_at_games[:10]) + "```")

        await ctx.send(
            file=discord.File("res/leaderboard/atbugs.png", filename="atbugs.png")
        )
        await ctx.send("```\n" + "\n".join(leaderboard_at_bugs[:10]) + "```")

        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Leaderboard(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Leaderboard(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
