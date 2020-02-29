import asyncio
import timeit

import discord
from discord.ext import commands

import config

from extensions.checks import database_ready

# TO DO: timeout wait_for reaction

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TO DO: clean up branching, async functions
    @commands.command(aliases=['info', 'sheet', 'rank'])
    @database_ready()
    async def stats(self, ctx, member:discord.Member=None):
        """Gets user's RCT game info from the sheet"""
        start = timeit.default_timer()
        check_failed = False

        if member is None:
            member = ctx.message.author
        member_discord_id = str(member.id)
        requester_discord_id = str(ctx.message.author.id)
        requester_name = None

        for row in config.LIST_OF_LISTS:
            if row[32] == member_discord_id:
                row_values = row
            if row[32] == requester_discord_id:
                requester_name = row[1]

        nick = row_values[1]
        nick_lower = nick.lower()

        #check trivia spreadsheet for points
        try:
            for row in config.LIST_OF_LISTS_TRIVIA:
                if row[0].lower() == nick_lower:
                    row_values_trivia = row
                    break
            trivia_points = row_values_trivia[2]
        except:
            trivia_points = 0

        if row_values[21] == '':
            absence = 'No'
        else:
            absence = 'Yes'
        games = int(row_values[2])
        bonus = []
        if games >= 10:
            bonus.append('10')
        if games >= 20:
            bonus.append('20')
        if int(row_values[16]) > 0:
            bonus.append('50')
        if len(bonus) == 0:
            bonus.append('None')
            bonus = ', '.join(bonus)
        else:
            bonus = ', '.join(bonus)+' games'

        #this cycle
        seconds = int(row_values[3])
        dhms = ''
        for scale in 86400, 3600, 60:
            result, seconds = divmod(seconds, scale)
            if dhms != '' or result > 0:
                dhms += '{0:02d}:'.format(result)
        dhms += '{0:02d}'.format(seconds)

        # if seconds>=60:
        #     dhms = dhms.split(':')
        #     gametime = "{0} minutes {1} seconds".format(dhms[0],dhms[1])
        # elif seconds>=3600:
        #     dhms = dhms.split(':')
        #     gametime = "{0} hours {1} minutes {2} seconds".format(dhms[0],dhms[1],dhms[2])
        # else:
        #     gametime = "{0} seconds".format(dhms)

        gametime = '{0}'.format(dhms)

        #total
        seconds_total = int(row_values[6])
        dhms_total = ''
        for scale_total in 86400, 3600, 60:
            result_total, seconds_total = divmod(seconds_total, scale_total)
            if dhms_total != '' or result_total > 0:
                dhms_total += '{0:02d}:'.format(result_total)
        dhms_total += '{0:02d}'.format(seconds_total)

        # if seconds_total>=60:
        #     dhms_total = dhms_total.split(':')
        #     gametime_total = "{0} minutes {1} seconds".format(dhms_total[0],dhms_total[1])
        # elif seconds_total>=3600:
        #     dhms_total = dhms_total.split(':')
        #     gametime_total = "{0} hours {1} minutes {2} seconds".format(dhms_total[0],dhms_total[1],dhms_total[2])
        # elif seconds_total>=86400:
        #     dhms_total = dhms_total.split(':')
        #     gametime_total = "{0} days {1} hours {2} minutes {3} seconds".format(dhms_total[0],dhms_total[1],dhms_total[2],dhms_total[2])
        # else:
        #     gametime_total = "{0} seconds".format(dhms_total)

        gametime_total = '{0}'.format(dhms_total)

        heroes = []
        players = []
        try:
            for x in config.PLAYER_SLASH_HERO:
                if x != '' and '/' in x:
                    y = x.split(',')
                    for z in y:
                        h = z.split('/')[0]
                        h = h.strip(' ')
                        k = z.split('/')[1]
                        heroes.append(k)
                        players.append(h)
        except:
            games_played = '0'
            check_failed = True
        try:
            [x.lower() for x in players].index(nick_lower)
        except:
            games_played = '0'
            check_failed = True
        heroes_played = []
        if not check_failed:
            for i in range(0, len(players)):
                if players[i].lower() == nick_lower:
                    heroes_played.append(heroes[i])
                    #playerName=players[i]
            #games_played = collections.Counter(heroes_played)
            games_played = str(len(heroes_played))
        
        def is_current_member():
            return row_values[0].lower() in ('true', '1')
        #TO DO: this to function

        current_member = row_values[0]
        if current_member == 'TRUE':
            former = ''
        else:
            former = 'a former '

        rank_name = row_values[10]
        if rank_name == 'Immortal' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/dpugisO.png'
        elif rank_name == 'Legendary' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/59Jighv.png'
        elif rank_name == 'Diamond' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/AZYAK39.png'
        elif rank_name == 'Gold' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/ZDLUlqs.png'
        elif rank_name == 'Silver' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/xxxlPAq.png'
        elif rank_name == 'Bronze' and current_member == 'TRUE':
            rank_url = 'https://i.imgur.com/svAUm00.png'
        else:
            rank_url = 'https://i.imgur.com/ys2UBNW.png'

        guild = member.guild
        senior_tester_candidate_role = discord.utils.get(guild.roles, name="Senior Tester Candidate")
        senior_tester_role = discord.utils.get(guild.roles, name="Senior Tester")
        staff_role = discord.utils.get(guild.roles, name="Frostburn Staff")
        role_list = member.roles
        if staff_role in role_list:
            effective_role = 'Frostburn staff member'
            pass
        elif senior_tester_role in role_list:
            effective_role = 'senior tester'
        elif senior_tester_candidate_role in role_list:
            effective_role = 'senior tester candidate'
        else:
            effective_role="tester"

        nick_src = nick
        if nick.startswith('`') or nick.startswith('_'):
            nick=('\\'+nick)

        embed = discord.Embed(title="Retail Candidate Testers", type="rich", description="Information for {0}{1} {2}.".format(former, effective_role, nick), url="https://forums.heroesofnewerth.com/forumdisplay.php?209-Retail-Candidate-Testers", color=0xff6600, timestamp=ctx.message.created_at)
        embed.set_author(name=nick_src, url="https://docs.google.com/spreadsheets/d/1HpDhrKbyK01rRUUFw3v-30QrNJpLHaOmWYrUxkKDbq0/edit#gid=0", icon_url=member.avatar_url)
        if current_member == 'TRUE':
            embed.add_field(name="Unconfirmed games", value=games_played, inline=True)
            #embed.add_field(name=u"\u2063", value=u"\u2063", inline=True)
            embed.add_field(name="Games", value=games, inline=True)
        embed.add_field(name="Total games", value=row_values[5], inline=True)
        if current_member == 'TRUE':
            embed.add_field(name="Game time", value=gametime, inline=True)
        embed.add_field(name="Total game time", value=gametime_total, inline=True)
        if current_member == 'TRUE':
            embed.add_field(name="Bug reports", value=row_values[4], inline=True)
        embed.add_field(name="Total bug reports", value=row_values[7], inline=True)
        #embed.add_field(name="Total games", value=row_values[3], inline=True)
        #embed.add_field(name="Total game time", value="N/A", inline=True)
        #embed.add_field(name="Total bug reports", value=row_values[10], inline=True)
        if current_member == 'TRUE':
            embed.add_field(name="Tokens earned", value=row_values[8], inline=True)
            embed.add_field(name="Bonuses", value=bonus, inline=True)
            embed.add_field(name="Activity rank", value=row_values[10], inline=True)
            embed.add_field(name="Multiplier", value="{0}x".format(row_values[12]), inline=True)
            embed.add_field(name="Perks", value=row_values[19], inline=True)
            embed.add_field(name="Absence", value=absence, inline=True)
        embed.add_field(name="Join date", value=row_values[20], inline=True)
        embed.add_field(name="Trivia points", value=trivia_points, inline=True)
        if current_member == 'FALSE' and row_values[22] != '':
            embed.add_field(name="Reason for removal", value=row_values[22], inline=False)
        #embed.add_field(name=u"\u2063", value=u"\u2063", inline=True)
        #embed.add_field(name=u"\u2063", value=u"\u2063", inline=True)
        if row_values[31] != '':
            embed.add_field(name="Awards", value=u"\u2063"+row_values[31], inline=True)
        if requester_discord_id is not None:
            embed.set_footer(text="Requested by {0} (✓). React with 🆗 to delete this message.".format(requester_name), icon_url="https://i.imgur.com/q8KmQtw.png")
        else:
            embed.set_footer(text="Requested by {0} ({1}#{2}). React with 🆗 to delete this message.".format(ctx.message.author.display_name, ctx.message.author.name, ctx.message.author.discriminator), icon_url="https://i.imgur.com/q8KmQtw.png")
        #embed.set_footer(text="React with 🆗 to delete this message.", icon_url="https://i.imgur.com/Ou1k4lD.png")
        #embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        embed.set_thumbnail(url=rank_url)
        message = await ctx.send(embed=embed)
        stop = timeit.default_timer()
        print(stop-start)
        await message.add_reaction('🆗')
        await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id)
        await message.delete()

def setup(bot):
    bot.add_cog(Stats(bot))
    print('Stats loaded.')