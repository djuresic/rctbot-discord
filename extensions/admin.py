import asyncio
from datetime import date

import discord
from discord.ext import commands

import config
from extensions.checks import is_senior
import extensions.spreadsheet as spreadsheet


class Administration(commands.Cog):
    def __init__(self, bot):
        # fmt: off
        self.bot = bot
        self.spreadsheet_name = "RCT Spreadsheet"
        self.rewards_worksheet_name = "RCT Players and Rewards"
        self.token_formula = '=IFERROR(C{row}*10+D{row}*0.003725+IF(C{row}>=10,75,0)+IF(C{row}>=20,225,0))*M{row}+Q{row}*750+S{row}+100*E{row}'
        self.token_formula_old = '=IFERROR(C{row}*25+IF(C{row}>=10,100,0)+IF(C{row}>=20,300,0))+Q{row}*750+S{row}+100*E{row}'
        self.rank_formula = '=IF(AND(C{row}+E{row}=0,NOT(A{row}="None"),V{row}="",K{row}="Bronze",NOT(AF{row}="")),"Bronze",IF(AND(C{row}+E{row}=0,NOT(A{row}="None"),V{row}="",K{row}="Bronze"),"Warning",IF(AND(C{row}+E{row}=0,NOT(A{row}="None"),K{row}="Bronze"),"Bronze",IF(AND(C{row}+E{row}>=5,NOT(A{row}="None"),K{row}="Bronze"),"Silver",IF(AND(C{row}+E{row}<3,NOT(A{row}="None"),K{row}="Silver"),"Bronze",IF(AND(C{row}+E{row}>=8,NOT(A{row}="None"),K{row}="Silver"),"Gold",IF(AND(C{row}+E{row}<5,NOT(A{row}="None"),K{row}="Gold"),"Silver",IF(AND(C{row}+E{row}>=10,NOT(A{row}="None"),K{row}="Gold"),"Diamond",IF(AND(C{row}+E{row}<7,NOT(A{row}="None"),K{row}="Diamond"),"Gold",IF(AND(C{row}+E{row}>=12,NOT(A{row}="None"),K{row}="Diamond"),"Legendary",IF(AND(C{row}+E{row}<10,NOT(A{row}="None"),K{row}="Legendary"),"Diamond",IF(AND(C{row}+E{row}>0,C{row}+E{row}<5,NOT(A{row}="None"),K{row}="Bronze"),"Bronze",IF(AND(C{row}+E{row}>=3,C{row}+E{row}<8,NOT(A{row}="None"),K{row}="Silver"),"Silver",IF(AND(C{row}+E{row}>=5,C{row}+E{row}<10,NOT(A{row}="None"),K{row}="Gold"),"Gold",IF(AND(C{row}+E{row}>=7,C{row}+E{row}<12,NOT(A{row}="None"),K{row}="Diamond"),"Diamond",IF(AND(C{row}+E{row}>=10,NOT(A{row}="None"),K{row}="Legendary"),"Legendary",IF(AND(C{row}+E{row}<3,NOT(A{row}="None"),K{row}="Warning"),"No rank",IF(AND(C{row}+E{row}>=3,NOT(A{row}="None"),K{row}="Warning"),"Bronze",IF(AND(NOT(A{row}="None"),K{row}="No rank"),"No rank",IF(A{row}="None","No rank","Immortal"))))))))))))))))))))'
        self.multiplier_formula = '=IF(AND(K{row}="Warning"),1+N{row},IF(AND(K{row}="Legendary"),2+N{row},IF(AND(K{row}="Diamond"),1.75+N{row},IF(AND(K{row}="Gold"),1.5+N{row},IF(AND(K{row}="Silver"),1.25+N{row},IF(AND(K{row}="Bronze"),1+N{row},IF(AND(K{row}="Immortal"),2.5+N{row},0)))))))*IF(A{row}="None",0,1)'
        self.bonus_this_cycle_formula = '=IFERROR(C{row}/50,0)'
        self.eligible_for_bonus_formula = '=IF(AND(B{row} = "Test Player"),FLOOR(10+(F{row}/50)-P{row},1),FLOOR((F{row}/50)-P{row},1))'
        self.bonus_formula = '=IF(AND(B{row}="Test Player"),10+(F{row}/50)-P{row},(F{row}/50)-P{row})'
        self.tokens_left_to_give = '=IFERROR(C{row}*10+D{row}*0.003725+IF(C{row}>=10,75,0)+IF(C{row}>=20,225,0))*M{row}+Q{row}*750+S{row}+100*E{row}-Y{row}'
        self.games_left_to_count = '=C{row}-AA{row}'
        self.conc_player_tokens = '=IFERROR(CONCATENATE(B{row}," ",ROUND(X{row},0)))'
        # fmt: on

    @commands.group()
    @is_senior()
    async def admin(self, ctx):
        pass

    @admin.command(name="add")
    async def _add(self, ctx, names: str):
        "admin add <csv nicknames>"
        if "," in names:
            names = names.split(",")
        else:
            names = names.split(";")

        names = list(dict.fromkeys(names))  # Remove duplicates
        dr_names = "\n".join(names)
        message = await ctx.send(f"```\n{dr_names}```\nDoes this look correct?")
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        reaction, _ = await self.bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: user == ctx.author
            and reaction.emoji in ["✅", "❌"]
            and reaction.message.id == message.id,
        )

        if reaction.emoji == "❌":
            return await ctx.send("admin add cancelled.")

        client = await spreadsheet.set_client()
        ss = await client.open(self.spreadsheet_name)
        ws = await ss.worksheet(self.rewards_worksheet_name)
        players = await ws.col_values(2)
        names = [
            name
            for name in names
            if name.lower() not in [player.lower() for player in players]
        ]
        dr_names_new = "\n".join(names)
        await ctx.send(f"First time members:\n```\n{dr_names_new}```")
        # init_rows = ws.row_count This is inconsistent.
        init_rows = len(players)
        added_rows = len(names)
        now_rows = init_rows + added_rows
        await ctx.send(f"Current rows: {init_rows}\nAdding {added_rows} more.")
        # await ws.add_rows(added_rows) Don't...

        index = 0
        for row in range(init_rows + 1, now_rows + 1):
            await ctx.send(
                f"Updating row {row}/{now_rows}\nPlayer: {discord.utils.escape_markdown(names[index])}"
            )

            token_formula = self.token_formula.format(row=row)
            token_formula_old = self.token_formula_old.format(row=row)

            tokens_left_to_give = self.tokens_left_to_give.format(row=row)
            games_left_to_count = self.games_left_to_count.format(row=row)

            rank_formula = self.rank_formula.format(row=row)
            multiplier_formula = self.multiplier_formula.format(row=row)

            bonus_formula = self.bonus_formula.format(row=row)
            bonus_this_cycle_formula = self.bonus_this_cycle_formula.format(row=row)
            eligible_for_bonus_formula = self.eligible_for_bonus_formula.format(row=row)

            conc_player_tokens = self.conc_player_tokens.format(row=row)

            join_date = date.today().strftime("%m/%d/%Y")

            await ws.append_row(
                (
                    "None",  # Rank
                    names[index],  # Nickname
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    token_formula,
                    token_formula_old,
                    "Gold",
                    rank_formula,
                    multiplier_formula,
                    5,
                    bonus_this_cycle_formula,
                    0,
                    eligible_for_bonus_formula,
                    bonus_formula,
                    0,
                    "No",  # Perks
                    join_date,
                    "",
                    "",
                    tokens_left_to_give,
                    0,  # Tokens given this cycle
                    games_left_to_count,  # (To add to total games)
                    0,  # Games counted this cycle
                    conc_player_tokens,  # Player name and tokens left to give, CONCATENATE
                    "",  # Reserved
                    "",  # Reserved
                    "",  # Reserved
                    "",
                    "",  # Discord ID
                )
            )

            await ws.update_cell(row, 9, token_formula)
            await ws.update_cell(row, 10, token_formula_old)
            await ws.update_cell(row, 12, rank_formula)
            await ws.update_cell(row, 13, multiplier_formula)
            await ws.update_cell(row, 15, bonus_this_cycle_formula)
            await ws.update_cell(row, 17, eligible_for_bonus_formula)
            await ws.update_cell(row, 18, bonus_formula)
            await ws.update_cell(row, 24, tokens_left_to_give)
            await ws.update_cell(row, 26, games_left_to_count)
            await ws.update_cell(row, 28, conc_player_tokens)

            await ctx.send("Done.")

            index += 1

        final_rows = len(await ws.col_values(1))
        await ctx.send(f"Rows total now: {final_rows}\nOver and out.")


def setup(bot):
    bot.add_cog(Administration(bot))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Administration(bot))
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
