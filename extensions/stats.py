import asyncio
import timeit
import collections

import aiohttp
import discord
from discord.ext import commands

import core.perseverance
import core.config as config
from core.checks import database_ready, is_senior

from hon.avatar import get_avatar

# TO DO: timeout wait_for reaction


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TO DO: clean up branching, member to user, CAI
    @commands.command(aliases=["info", "sheet", "rank"])
    @database_ready()
    async def stats(self, ctx, member: str = ""):
        """Gets user's RCT game info from the sheet."""
        start = timeit.default_timer()
        list_of_lists = config.LIST_OF_LISTS
        check_failed = False

        # Remove Discord ID dep at some point. This whole branching requires a better solution but keeping it for now.
        if member == "":
            member = ctx.author
            member_discord_id = str(ctx.author.id)
        elif len(ctx.message.raw_mentions) > 0:
            member = discord.utils.find(
                lambda m: m.id == ctx.message.raw_mentions[0], ctx.guild.members
            )
            member_discord_id = str(ctx.message.raw_mentions[0])
        else:
            found_em = False
            for row in list_of_lists:
                if row[1].lower() == member.lower():
                    if row[32].isdigit():
                        lu_member_id = int(row[32])
                        found_em = True
                        break
            if not found_em:
                return await ctx.send("That player has never joined Discord.")
            member = discord.utils.find(
                lambda m: m.id == lu_member_id, ctx.guild.members
            )
            member_discord_id = str(lu_member_id)
        requester_discord_id = str(ctx.author.id)
        requester_name = None
        # member = ctx.guild.get_member(int(member_discord_id))

        # This needs to be split. Keeping for now.
        for row in list_of_lists:
            if row[32] == member_discord_id:
                row_values = row
            if row[32] == requester_discord_id:
                requester_name = row[1]

        nick = row_values[1]
        nick_lower = nick.lower()

        # Check trivia spreadsheet for points.
        try:
            for row in config.LIST_OF_LISTS_TRIVIA:
                if row[0].lower() == nick_lower:
                    row_values_trivia = row
                    break
            trivia_points = row_values_trivia[2]
        except:
            trivia_points = 0

        if row_values[21] == "":
            absence = "No"
        else:
            absence = "Yes"
        games = int(row_values[2])
        bonus = []
        if games >= 10:
            bonus.append("10")
        if games >= 20:
            bonus.append("20")
        if int(row_values[16]) > 0:
            bonus.append("50")
        if len(bonus) == 0:
            bonus.append("None")
            bonus = ", ".join(bonus)
        else:
            bonus = ", ".join(bonus) + " games"

        # This cycle.
        seconds = int(row_values[3])
        dhms = ""
        for scale in 86400, 3600, 60:
            result, seconds = divmod(seconds, scale)
            if dhms != "" or result > 0:
                dhms += "{0:02d}:".format(result)
        dhms += "{0:02d}".format(seconds)

        gametime = f"{dhms}"

        # Total.
        seconds_total = int(row_values[6])
        dhms_total = ""
        for scale_total in 86400, 3600, 60:
            result_total, seconds_total = divmod(seconds_total, scale_total)
            if dhms_total != "" or result_total > 0:
                dhms_total += "{0:02d}:".format(result_total)
        dhms_total += "{0:02d}".format(seconds_total)

        gametime_total = f"{dhms_total}"

        heroes = []
        players = []
        try:
            for x in config.PLAYER_SLASH_HERO:
                if x != "" and "/" in x:
                    y = x.split(",")
                    for z in y:
                        h = z.split("/")[0]
                        h = h.strip(" ")
                        k = z.split("/")[1]
                        heroes.append(k)
                        players.append(h)
        except:
            games_played = "0"
            check_failed = True
        try:
            [x.lower() for x in players].index(nick_lower)
        except:
            games_played = "0"
            check_failed = True

        heroes_played = []
        if not check_failed:
            for i in range(0, len(players)):
                if players[i].lower() == nick_lower:
                    heroes_played.append(heroes[i])
            games_played = str(len(heroes_played))

        def is_current_member():
            return row_values[0].lower() in (
                "true",
                "1",
                "tester",
                "senior",
                "staff",
            )  # true, 1 legacy

        current_member = is_current_member()

        # Rank icons from url.
        rank_name = row_values[10]
        rank_icons = {
            "Immortal": "https://i.imgur.com/dpugisO.png",
            "Legendary": "https://i.imgur.com/59Jighv.png",
            "Diamond": "https://i.imgur.com/AZYAK39.png",
            "Gold": "https://i.imgur.com/ZDLUlqs.png",
            "Silver": "https://i.imgur.com/xxxlPAq.png",
            "Bronze": "https://i.imgur.com/svAUm00.png",
            "Warning": "https://i.imgur.com/svAUm00.png",
            "No rank": "https://i.imgur.com/ys2UBNW.png",
        }

        role_translations = {
            "None": "a former tester",
            "Tester": "tester",
            "Senior": "senior tester",
            "Staff": "Frostburn staff member",
        }

        nick_src = nick
        nick = discord.utils.escape_markdown(nick)
        if current_member:
            # Reusing leaderboard to calculate current placement.
            offset = 2  # The first 2 rows are reserved.

            # This testing cycle.
            tc_players = [
                list_of_lists[x][1]
                for x in range(offset, len(list_of_lists))
                if list_of_lists[x][0] != "None"
            ]
            tc_games = [
                int(list_of_lists[x][2])
                for x in range(offset, len(list_of_lists))
                if list_of_lists[x][0] != "None"
            ]
            tc_bugs = [
                int(list_of_lists[x][4])
                for x in range(offset, len(list_of_lists))
                if list_of_lists[x][0] != "None"
            ]
            tc_tokens = [
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

            leaderboard_len = len(tc_players)

            # Create a list of tuples and sort it later.
            unsorted_leaderboard = []

            for i in range(leaderboard_len):
                unsorted_leaderboard.append(
                    (
                        tc_players[i].lower(),
                        tc_games[i],
                        tc_bugs[i],
                        tc_tokens[i],
                        at_games[i],
                        at_bugs[i],
                    )
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

            # Convert cardinal to ordinal.
            def ordinal(n):
                _suffix = (
                    "th"
                    if 4 <= n % 100 <= 20
                    else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
                )
                return f"{n}{_suffix}"

            player_tuple = (
                nick_src.lower(),
                int(games),
                int(row_values[4]),
                int(row_values[8]),
                int(row_values[5]),
                int(row_values[7]),
            )

            # Find player's placement on the ladder.
            rank_tc_games = f"{ordinal(sorted_by_games.index(player_tuple)+1)}"
            rank_tc_bugs = f"{ordinal(sorted_by_bugs.index(player_tuple)+1)}"
            rank_tc_tokens = f"{ordinal(sorted_by_tokens.index(player_tuple)+1)}"
            rank_at_games = f"{ordinal(sorted_by_at_games.index(player_tuple)+1)}"
            rank_at_bugs = f"{ordinal(sorted_by_at_bugs.index(player_tuple)+1)}"

        # Check if the player owns a Custom Account Icon on the retail client and display it.
        _account_id = row_values[33]
        account_icon_url = await get_avatar(_account_id)

        embed = discord.Embed(
            title="Retail Candidate Testers",
            type="rich",
            description=f"Information for {role_translations[row_values[0]]} {nick}.",
            url="https://forums.heroesofnewerth.com/forumdisplay.php?209-Retail-Candidate-Testers",
            color=0xFF6600,
            timestamp=config.LAST_RETRIEVED,
        )
        embed.set_author(
            name=nick_src,
            url=f"https://forums.heroesofnewerth.com/member.php?{_account_id}",
            icon_url=account_icon_url,
        )
        if current_member:
            embed.add_field(name="Unconfirmed games", value=games_played, inline=True)
            # embed.add_field(name=u"\u2063", value=u"\u2063", inline=True)
            embed.add_field(
                name="Games", value=f"{games} ({rank_tc_games})", inline=True
            )
        if current_member:
            embed.add_field(
                name="Total games",
                value=f"{row_values[5]} ({rank_at_games})",
                inline=True,
            )
        else:
            embed.add_field(name="Total games", value=row_values[5], inline=True)
        if current_member:
            embed.add_field(name="Game time", value=gametime, inline=True)
        embed.add_field(name="Total game time", value=gametime_total, inline=True)
        if current_member:
            embed.add_field(
                name="Bug reports",
                value=f"{row_values[4]} ({rank_tc_bugs})",
                inline=True,
            )
        if current_member:
            embed.add_field(
                name="Total bug reports",
                value=f"{row_values[7]} ({rank_at_bugs})",
                inline=True,
            )
        else:
            embed.add_field(
                name="Total bug reports", value=row_values[7], inline=True,
            )
        if current_member:
            embed.add_field(
                name="Tokens earned",
                value=f"{row_values[8]} ({rank_tc_tokens})",
                inline=True,
            )
            embed.add_field(name="Bonuses", value=bonus, inline=True)
            embed.add_field(name="Activity rank", value=rank_name, inline=True)
            embed.add_field(name="Multiplier", value=f"{row_values[12]}x", inline=True)
            embed.add_field(name="Perks", value=row_values[19], inline=True)
            embed.add_field(name="Absence", value=absence, inline=True)
        embed.add_field(name="Join date", value=row_values[20], inline=True)
        embed.add_field(name="Trivia points", value=trivia_points, inline=True)
        if not current_member and row_values[22] != "":
            embed.add_field(
                name="Reason for removal", value=row_values[22], inline=False
            )
        if row_values[31] != "":
            embed.add_field(name="Awards", value="\u2063" + row_values[31], inline=True)
        if requester_discord_id is not None:
            embed.set_footer(
                text=f"Requested by {requester_name} (✓). Timestamp provided shows the time of last retrieval. React with 🗑️ to delete or with 💾 to preserve this message. No action results in deletion after 5 minutes.",
                icon_url="https://i.imgur.com/q8KmQtw.png",
            )
        else:
            embed.set_footer(
                text="Requested by {.display_name} ({.name}#{.discriminator}). Timestamp provided shows the time of last retrieval. React with 🗑️ to delete or with 💾 to preserve this message. No action results in deletion after 5 minutes.".format(
                    ctx.author
                ),
                icon_url="https://i.imgur.com/q8KmQtw.png",
            )
        # embed.set_footer(text="React with 🆗 to delete this message.", icon_url="https://i.imgur.com/Ou1k4lD.png")
        # embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        embed.set_thumbnail(url=rank_icons[rank_name])
        message = await ctx.send(embed=embed)
        stop = timeit.default_timer()
        print(stop - start)
        await message.add_reaction("🗑️")
        await message.add_reaction("💾")

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.message.author
                and reaction.emoji in ["🗑️", "💾"]
                and reaction.message.id == message.id,
                timeout=300.0,
            )

            if reaction.emoji == "🗑️":
                await message.delete()

        except asyncio.TimeoutError:
            await message.delete()

    # TO DO: this needs to be prettier
    @commands.command(aliases=["hero", "herousage"])
    @is_senior()
    @database_ready()
    async def usage(self, ctx):
        """Hero usage list for the current patch cycle."""
        hul_embed = discord.Embed(title="Hero Usage List", type="rich", color=0xFF6600)
        hul_embed.set_author(
            name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url
        )
        hul_embed.add_field(name="By Hero", value="📈")
        hul_embed.add_field(name="By Player", value="📉")
        hul_embed.add_field(name="Show All Picks", value="📊")
        hul_embed.set_footer(text="Please add one of the reactions above to continue.")
        hul_message = await ctx.send(embed=hul_embed)
        # await asyncio.sleep(0.1)
        await hul_message.add_reaction("📈")
        await hul_message.add_reaction("📉")
        await hul_message.add_reaction("📊")
        reaction, _ = await self.bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: user == ctx.message.author
            and reaction.emoji in ["📈", "📉", "📊"]
            and reaction.message.id == hul_message.id,
        )
        # reaction_action=await self.bot.wait_for_reaction(['📈','📉','📊'], user=ctx.message.author, timeout=60.0, message=hul_message)
        await hul_message.delete()
        start = timeit.default_timer()
        try:
            if reaction.emoji == "📊":
                heroes = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                k = z.split("/")[1]
                                heroes.append(k)
                except:
                    await ctx.send("Unavailable. Please wait for the next conversion.")
                    return

                hero_counter = collections.Counter(heroes)
                hero_keys = hero_counter.keys()
                hero_values = hero_counter.values()

                hero_percent = []
                hero_no_percent = []
                last_hero = []
                discord_message = []

                for val in hero_values:
                    hero_percent.append(round((int(val) * 100) / len(heroes), 2))
                    hero_no_percent.append(int(val))
                for hero in hero_keys:
                    last_hero.append(hero)
                for percent in range(0, len(hero_percent), 1):
                    discord_message.append(
                        "\n{0}: **{1}** ({2}%)".format(
                            last_hero[percent],
                            hero_no_percent[percent],
                            hero_percent[percent],
                        )
                    )

                discord_message.sort()

                length = len(hero_percent)
                if length <= 50:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:length]))
                elif length <= 100:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:length]))
                elif length <= 150:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:length]))
                else:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:150]))
                    await ctx.send("".join(discord_message[150:length]))

            elif reaction.emoji == "📈":
                heroes = []
                players = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                h = z.split("/")[0]
                                h = h.strip(" ")
                                k = z.split("/")[1]
                                heroes.append(k)
                                players.append(h)
                except:
                    await ctx.send("Please convert to proper format first.")
                    return
                await ctx.send("Please enter the name of the hero:")
                wf_message = await self.bot.wait_for(
                    "message", check=lambda m: m.author == ctx.message.author
                )
                hero_name = wf_message.content
                hero_name_lower = hero_name.lower()
                try:
                    [x.lower() for x in heroes].index(hero_name_lower)
                except:
                    await ctx.send(
                        "**{0}** was not picked this cycle.".format(hero_name.title())
                    )
                    return
                hero_counter = 0
                for i in heroes:
                    if i == hero_name:
                        hero_counter += 1
                # heroPercentage=((hero_counter*100)/len(heroes))
                played_by = []
                for i in range(0, len(heroes), 1):
                    if heroes[i].lower() == hero_name_lower:
                        played_by.append(players[i])
                        hero_name = heroes[i]
                played_by = collections.Counter(played_by)
                nb_plays = played_by.values()
                nb_plays_c = []
                for i in nb_plays:
                    nb_plays_c.append(str(i))
                played_by = played_by.keys()
                played_by_o = []
                for i in played_by:
                    played_by_o.append(i)
                discord_message = []
                for i in range(0, len(played_by_o)):
                    if i == (len(played_by_o) - 1):
                        temp = "\n" + played_by_o[i] + ": **" + nb_plays_c[i] + "**"
                        discord_message.append(temp)
                    else:
                        temp = "\n" + played_by_o[i] + ": **" + nb_plays_c[i] + "**"
                        discord_message.append(temp)
                discord_message.sort()
                length = len(discord_message)
                if length <= 50:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:length]))
                elif length <= 100:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:length]))
                else:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:length]))
            elif reaction.emoji == "📉":
                heroes = []
                players = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                h = z.split("/")[0]
                                h = h.strip(" ")
                                k = z.split("/")[1]
                                heroes.append(k)
                                players.append(h)
                except Exception:
                    await ctx.send("Please convert to proper format first.")
                    return
                await ctx.send("Please enter the name of the player:")
                wf_message = await self.bot.wait_for(
                    "message", check=lambda m: m.author == ctx.message.author
                )
                playerName = wf_message.content
                playerNameLower = playerName.lower()
                try:
                    [x.lower() for x in players].index(playerNameLower)
                except:
                    await ctx.send(
                        "**{0}** did not play this cycle.".format(playerName)
                    )
                    return
                playedHeroes = []
                for i in range(0, len(players)):
                    if players[i].lower() == playerNameLower:
                        playedHeroes.append(heroes[i])
                        playerName = players[i]
                playedHeroes = collections.Counter(playedHeroes)
                heroesNames = playedHeroes.keys()
                heroesCount = playedHeroes.values()
                hero_name = []
                heroCount = []
                for i in heroesNames:
                    hero_name.append(i)
                for i in heroesCount:
                    heroCount.append(str(i))
                lastHero = []
                for i in range(0, len(hero_name)):
                    if i == (len(hero_name) - 1):
                        temp = "\n" + hero_name[i] + ": **" + heroCount[i] + "**"
                        lastHero.append(temp)
                    else:
                        temp = "\n" + hero_name[i] + ": **" + heroCount[i] + "**"
                        lastHero.append(temp)
                lastHero.sort()
                length = len(lastHero)
                if length <= 50:
                    await ctx.send("Hero picks for **{0}**:".format(playerName))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:length]))
                elif length <= 100:
                    await ctx.send("Hero picks for **{0}**:".format(playerName))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:50]))
                    await ctx.send("".join(lastHero[50:length]))
                else:
                    await ctx.send("Hero picks for **{0}**:".format(playerName))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:50]))
                    await ctx.send("".join(lastHero[50:100]))
                    await ctx.send("".join(lastHero[100:length]))
        except Exception:
            return
        stop = timeit.default_timer()
        print(stop - start)


def setup(bot):
    bot.add_cog(Stats(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Stats(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
