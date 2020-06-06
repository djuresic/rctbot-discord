import asyncio
import timeit
import collections
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands
from PIL import Image

import core.perseverance
import core.config as config
import core.spreadsheet as spreadsheet
import hon.acp as acp
from core.checks import database_ready, is_senior, is_tester

from hon.avatar import get_avatar
from hon.masterserver import Client
from hon.portal import VPClient

# TO DO: timeout wait_for reaction


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet_name = "RCT Spreadsheet"
        self.rewards_worksheet_name = "RCT Players and Rewards"

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
        try:
            async with aiohttp.ClientSession() as session:
                simple_stats = await Client("ac", session=session).show_simple_stats(
                    nick
                )
                if simple_stats and b"nickname" in simple_stats:
                    nick_with_clan_tag = simple_stats[b"nickname"].decode()
                    if "]" in nick_with_clan_tag:
                        clan_tag = f"{nick_with_clan_tag.split(']')[0]}]"
                    else:
                        clan_tag = ""
                else:
                    nick_with_clan_tag = nick
                    clan_tag = None
        except:
            nick_with_clan_tag = nick
            clan_tag = None

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
        rank_icons_emoji = {
            "Immortal": "<:Immortal:711744275339018323>",
            "Legendary": "<:Legendary:711744131772186714>",
            "Diamond": "<:Diamond:711744217654886480>",
            "Gold": "<:Gold:711744184478072853>",
            "Silver": "<:Silver:711744335846047744>",
            "Bronze": "<:Bronze:711744364367577158>",
            "Warning": "<:Bronze:711744364367577158>",
            "No rank": "<:Norank:711744503228399616>",
        }
        rank_chests_emoji = {
            "Immortal": "<:ImmortalChest:711926778540589126>",
            "Legendary": "<:LegendaryChest:711926778477936682>",
            "Diamond": "<:DiamondChest:711926778368884739>",
            "Gold": "<:GoldChest:711926778654097458>",
            "Silver": "<:SilverChest:711926778238861365>",
            "Bronze": "<:BronzeChest:711926778339262507>",
            "Warning": "<:BronzeChest:711926778339262507>",
            "No rank": "<:UnrankedChest:711926778524074054>",
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
            name=nick_with_clan_tag,
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

            if requester_name.lower() == nick_lower:
                owned_tokens_message = (
                    "React with <:gold:711938379587125340> to reveal."
                )
            else:
                owned_tokens_message = f"Available when used by {nick} only!"
            embed.add_field(
                name="Tokens owned", value=owned_tokens_message, inline=True,
            )

            embed.add_field(
                name="Activity rank",
                value=f"{rank_icons_emoji[rank_name]} {'Unranked' if rank_name == 'No rank' else rank_name}",
                inline=True,
            )
            embed.add_field(
                name="Multiplier",
                value=f"{rank_chests_emoji[rank_name]} {row_values[12]}x",
                inline=True,
            )
            embed.add_field(name="Bonuses", value=bonus, inline=True)

            embed.add_field(name="Perks", value=row_values[19], inline=True)
            embed.add_field(name="Absence", value=absence, inline=True)
        embed.add_field(name="Join date", value=row_values[20], inline=True)
        # embed.add_field(name="Trivia points", value=trivia_points, inline=True)
        if not current_member and row_values[22] != "":
            embed.add_field(
                name="Reason for removal", value=row_values[22], inline=False
            )
        if row_values[31] != "":
            embed.add_field(name="Awards", value="\u2063" + row_values[31], inline=True)

        if row_values[19] == "Pending" and requester_name.lower() == nick_lower:
            if clan_tag is not None:
                if clan_tag == "[RCT]":
                    perks_message = "React with <:RCT:717710063657156688> to claim your rewards now! Note that it may take several minutes for them to show up in your vault. Please refrain from clicking on this reaction again (in new embedded messages) for the next two minutes."
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

        if row_values[19] == "Requested" and requester_name.lower() == nick_lower:
            embed.add_field(
                name="Did you receive your RCT Chat Symbol and Name Color?",
                value="React with <:yay:717806806889660416> if they are in your vault or with <:nay:717806831916810251> if they are not.",
                inline=False,
            )
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
        # embed.set_image(url="https://i.imgur.com/PlO2rtf.png") # Hmmm
        if row_values[35] == "Yes":
            if row_values[36] != "":
                embed.set_image(url=row_values[36])
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
        if requester_name.lower() == nick_lower:
            await message.add_reaction("<:gold:711938379587125340>")
        if perks_ready_to_claim and requester_name.lower() == nick_lower:
            await message.add_reaction("<:RCT:717710063657156688>")
        if row_values[19] == "Requested" and requester_name.lower() == nick_lower:
            await message.add_reaction("<:yay:717806806889660416>")
            await message.add_reaction("<:nay:717806831916810251>")

        async def set_perks_status(status):
            gs_client = await spreadsheet.set_client()
            ss = await gs_client.open(self.spreadsheet_name)
            ws = await ss.worksheet(self.rewards_worksheet_name)
            players_col = await ws.col_values(2)
            players_col = [player_ent.lower() for player_ent in players_col]
            player_row = players_col.index(nick_lower) + 1
            return await ws.update_cell(player_row, 20, status)

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.message.author
                and str(reaction.emoji)
                in [
                    "🗑️",
                    "💾",
                    "<:gold:711938379587125340>",
                    "<:RCT:717710063657156688>",
                    "<:yay:717806806889660416>",
                    "<:nay:717806831916810251>",
                ]
                and reaction.message.id == message.id,
                timeout=300.0,
            )

            if reaction.emoji == "🗑️":
                await message.delete()

            if (
                str(reaction.emoji) == "<:RCT:717710063657156688>"
                and perks_ready_to_claim
                and requester_name.lower() == nick_lower
            ):
                async with aiohttp.ClientSession(
                    connector=(await acp.proxy_connector())
                ) as session:
                    status = await acp.authenticate(session)
                    if status != 200:
                        return await ctx.send(
                            f"{ctx.author.mention} Uh oh, something went wrong. {status}"
                        )
                    await acp.add_perks(session, nick_lower, ctx.author)
                await set_perks_status("Requested")
                await ctx.send(
                    f"{ctx.author.mention} Done! Please use this command again in a few minutes to confirm whether you received the RCT Chat Symbol and Name Color."
                )

            if (
                str(reaction.emoji) == "<:yay:717806806889660416>"
                and row_values[19] == "Requested"
                and requester_name.lower() == nick_lower
            ):
                await set_perks_status("Yes")
                await ctx.send(
                    f"{ctx.author.mention} Awesome! Thanks for using RCTBot."
                )

            if (
                str(reaction.emoji) == "<:nay:717806831916810251>"
                and row_values[19] == "Requested"
                and requester_name.lower() == nick_lower
            ):
                await set_perks_status("Pending")
                await ctx.send(
                    f"{ctx.author.mention} Perks status set to Pending. You should be able to use the same command and request rewards again in a few minutes."
                )

            if (
                str(reaction.emoji) == "<:gold:711938379587125340>"
                and requester_name.lower() == nick_lower
            ):
                await message.clear_reactions()
                async with VPClient() as portal:
                    tokens = await portal.get_tokens(_account_id)
                embed.set_field_at(
                    index=8, name="Tokens owned", value=tokens, inline=True
                )
                await message.edit(embed=embed)
                await message.add_reaction("🗑️")
                await message.add_reaction("💾")

                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: user == ctx.message.author
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

    # change to .stats, rename current .stats command to .rct
    @commands.command(aliases=["rstats"])
    @is_senior()
    @database_ready()
    async def retail(self, ctx, nickname: str):
        "retail simple stats"
        async with aiohttp.ClientSession() as session:
            client = Client("ac", session=session)
            response = await client.show_simple_stats(nickname)
            print(response)
        embed = discord.Embed(
            title=client.client_name,
            type="rich",
            description="Simple Stats",
            url="https://forums.heroesofnewerth.com/forumdisplay.php?209-Retail-Candidate-Testers",
            color=client.color,
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=response[b"nickname"].decode(),
            url=f"https://forums.heroesofnewerth.com/member.php?{response[b'account_id'].decode()}",
            icon_url=(await get_avatar(response[b"account_id"].decode())),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @is_tester()
    @database_ready()
    async def signature(self, ctx):
        "Signature options"
        price = 300
        member_discord_id = str(ctx.author.id)
        for row in config.LIST_OF_LISTS:
            if row[32] == member_discord_id:
                row_values = row

        async def set_signature(url=None, purchase=False):
            gs_client = await spreadsheet.set_client()
            ss = await gs_client.open(self.spreadsheet_name)
            ws = await ss.worksheet(self.rewards_worksheet_name)
            players_col = await ws.col_values(2)
            players_col = [player_ent.lower() for player_ent in players_col]
            player_row = players_col.index(row_values[1].lower()) + 1
            if purchase:
                return await ws.update_cell(player_row, 36, "Yes")
            if url is not None:
                return await ws.update_cell(player_row, 37, url)

        if row_values[35] == "Yes":
            purchased = True
        else:
            purchased = False

        if not purchased:
            desc = "You do not own a Discord Embedded Signature.\n\nDue to it beings somewhat intrusive and breaking the layout of stats display in some cases, it costs 300 Volunteer Tokens. This is a one time purchase and it is purely cosmetic. It does not give any other benefits other than adding a personal touch to your RCT stats display."
        else:
            desc = "Options"

        embed = discord.Embed(
            title="Discord Embedded Signature",
            type="rich",
            description=desc,
            color=0xFF6600,
            timestamp=config.LAST_RETRIEVED,
        )
        embed.set_author(
            name=row_values[1], icon_url=ctx.author.avatar_url,
        )

        if purchased:
            embed.add_field(name="Upload", value="⬆️", inline=True)
            if row_values[36] != "":
                embed.add_field(name="Clear", value="🗑️", inline=True)
                embed.set_image(url=row_values[36])
        else:
            embed.add_field(name="Purchase", value="🛒", inline=True)

        embed.add_field(name="Cancel", value="❌", inline=True)
        embed.set_footer(
            text="Unlike Custom Account Icons, you may reupload your Discord Embedded Signature at no additional cost. Supports images up to 900 x 150 pixels, which means you can use the same signature for (or from) the Heroes of Newerth forums.",
            icon_url="https://i.imgur.com/q8KmQtw.png",
        )

        message = await ctx.send(embed=embed)
        if purchased:
            await message.add_reaction("⬆️")
            if row_values[36] != "":
                await message.add_reaction("🗑️")
        else:
            await message.add_reaction("🛒")
        await message.add_reaction("❌")

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: user == ctx.message.author
                and str(reaction.emoji) in ["❌", "🗑️", "⬆️", "🛒"]
                and reaction.message.id == message.id,
                timeout=300.0,
            )
            await message.delete()

            if reaction.emoji == "🗑️" and row_values[36] != "":
                await set_signature("")
                await ctx.send(
                    f"{ctx.message.author.mention} Signature cleared! It may take up to a minute for changes to apply.",
                    delete_after=15.0,
                )

            if reaction.emoji == "🛒" and not purchased:
                confirmation = (
                    "I AM ABSOLUTELY SURE I WANT TO PURCHASE DISCORD EMBEDDED SIGNATURE"
                )
                purchase_prompt = await ctx.send(
                    f"{ctx.message.author.mention} Are you **absolutely sure** you want to purchase **Discord Embedded Signature** for **{price} Volunteer Tokens**? This is irreversible and could leave you with negative tokens.\n\n Type `{confirmation}` to confirm this order, or anything else to cancel."
                )
                purchase_confirmation = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.message.author.id
                    and m.channel.id == ctx.channel.id,
                )
                await purchase_prompt.delete()
                if purchase_confirmation.content != confirmation:
                    await purchase_confirmation.delete()
                    return await ctx.send(
                        f"{ctx.message.author.mention} Order cancelled.",
                        delete_after=15.0,
                    )
                await purchase_confirmation.delete()
                try:
                    async with VPClient() as portal:
                        await portal.mod_tokens(f"{row_values[1]} -{price}")
                    await set_signature(purchase=True)
                    return await ctx.send(
                        f"{ctx.message.author.mention} Successfully purchased Discord Embedded Signature! Note that it may take up to a minute for the command to reflect changes. Please refrain from attempting to purchase this again if your tokens have been deducted.",
                        delete_after=30.0,
                    )
                except:
                    return await ctx.send(
                        f"{ctx.message.author.mention} Something went wrong, please try again.",
                        delete_after=15.0,
                    )

            if reaction.emoji == "⬆️" and purchased:
                do_it_now = await ctx.send(
                    f"{ctx.message.author.mention} Upload your signature as a message attachment in your next Discord message here."
                )
                # Needs timeout
                signature_message = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.message.author.id
                    and m.channel.id == ctx.channel.id,
                )
                await do_it_now.delete()
                if len(signature_message.attachments) == 0:
                    return await ctx.send(
                        f"{ctx.message.author.mention} You did not attach an image! Use `.signature` to retry.",
                        delete_after=15.0,
                    )
                attachment = signature_message.attachments[0]
                # print(attachment)
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        image_b = await resp.read()
                image_bio = BytesIO(image_b)
                try:
                    with Image.open(image_bio) as image_pil:
                        width, height = image_pil.size
                        # print(width, height)
                        if width > 900 or height > 150:
                            await signature_message.delete()
                            return await ctx.send(
                                f"{ctx.message.author.mention} Image exceeds maximum allowed dimensions of 900 x 150 pixels! Use `.signature` to retry.\n\nRecommended dimensions: `285 x 95 pixels`\nYour image dimensions: `{width} x {height} pixels`",
                                delete_after=25.0,
                            )
                except:
                    await signature_message.delete()
                    return await ctx.send(
                        f"{ctx.message.author.mention} Unsupported file type! Use `.signature` to retry.",
                        delete_after=15.0,
                    )
                image_bio.seek(0)
                sigantures_channel = self.bot.get_channel(718465776172138497)
                uploaded_signature_message = await sigantures_channel.send(
                    f"{discord.utils.escape_markdown(row_values[1])}",
                    file=discord.File(image_bio, filename=attachment.filename),
                )
                image_bio.close()
                await signature_message.delete()
                uploaded_signature_url = uploaded_signature_message.attachments[0].url
                await set_signature(uploaded_signature_url)
                await ctx.send(
                    f"{ctx.message.author.mention} Signature set! It may take up to a minute for changes to apply.",
                    delete_after=15.0,
                )

        except:
            await message.delete()


def setup(bot):
    bot.add_cog(Stats(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Stats(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
