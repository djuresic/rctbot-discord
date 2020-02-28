import os
import asyncio
import platform #sys
import random
import json
import timeit
import collections
from time import time, gmtime, strftime
from datetime import datetime
from hashlib import md5, sha256

import discord
from discord.ext import commands

import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

import aiohttp
# import youtube_dl TO DO: music port

import phpserialize

# note to myself: ctx.author: shorthand for Message.author, also applies to: guild, channel

# TO DO:
# oh yeah it's f strings time!
# remove unnecessary "global"s, port: on_member_join, announce_testing, keep_alive, games, distribute, trivia, mvp, joined, mute, table, ttt, hangman, whois, pr
# detailed platform data
# remove utf-8 from encode/decode, it's the default in py 3
# option for remote config and empty config file creation


#Heroku
if 'DYNO' in os.environ:
    HEROKU_DEPLOYED = True
else:
    HEROKU_DEPLOYED = False

#load local config, platform for dev purposes
if 'Windows' in platform.system():
    CONFIG_FILE = 'dev_config.json'
else:
    CONFIG_FILE = 'config.json'

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as CONFIG:
        CONFIG = json.load(CONFIG)
        try:
            CONFIG_DISCORD = CONFIG['DISCORD']
            CONFIG_HON = CONFIG['HON']
            CONFIG_GOOGLE = CONFIG['GOOGLE']
            
            if HEROKU_DEPLOYED:
                CONFIG_HEROKU = CONFIG['HEROKU']
                HEROKU_APP_NAME = CONFIG_HEROKU['APP_NAME']
        except:
            raise Exception('Invalid configuration file or missing keys.')
else:
    raise Exception(f'Missing configuration file {CONFIG_FILE} in directory.')

#Discord
DISCORD_TOKEN = CONFIG_DISCORD['TOKEN']
DISCORD_NOTES_CHANNEL_ID = CONFIG_DISCORD['NOTES_CHANNEL_ID']
DISCORD_ANNOUNCEMENTS_CHANNEL_ID = CONFIG_DISCORD['ANNOUNCEMENTS_CHANNEL_ID']
DISCORD_FORUMS_ROLE_ID = CONFIG_DISCORD['FORUMS_ROLE_ID']
DISCORD_BUGS_CHANNEL_ID = CONFIG_DISCORD['BUGS_CHANNEL_ID']
DISCORD_BOT_LOG_CHANNEL_ID = CONFIG_DISCORD['BOT_LOG_CHANNEL_ID']
DISCORD_WHITELIST_IDS = CONFIG_DISCORD['WHITELIST_IDS']

DISCORD_DM_COMMANDS = ['report', 'notes'] #TO DO: replace with a decorator (guild_only and dm_allowed)

#Heroes of Newerth
HON_USER_AGENT = CONFIG_HON['USER_AGENT']
HON_NAEU_MASTERSERVER = CONFIG_HON['NAEU_MASTERSERVER']
HON_NAEU_RC_MASTERSERVER = CONFIG_HON['NAEU_RC_MASTERSERVER']
HON_NAEU_TC_MASTERSERVER = CONFIG_HON['NAEU_TC_MASTERSERVER']
HON_NAEU_RC_OS_PART = CONFIG_HON['NAEU_RC_OS_PART']
HON_NAEU_TC_OS_PART = CONFIG_HON['NAEU_TC_OS_PART']
HON_REGION = CONFIG_HON['REGION']
HON_s2_n = CONFIG_HON['s2_n']
HON_s2_g = CONFIG_HON['s2_g']
HON_ALT_DOMAIN = CONFIG_HON['ALT_DOMAIN']
HON_CAT_PASSWORD = CONFIG_HON['CAT_PASSWORD']
HON_FORUM_USER = CONFIG_HON['FORUM_USER']
HON_FORUM_USER_MD5_PASSWORD = CONFIG_HON['FORUM_USER_MD5_PASSWORD']
HON_FORUM_USER_ACCOUNT_ID = CONFIG_HON['FORUM_USER_ACCOUNT_ID']
HON_FORUM_ANNOUNCEMENTS_THREAD_ID = CONFIG_HON['FORUM_ANNOUNCEMENTS_THREAD_ID']
HON_FORUM_RCT_BUGS_SUBFORUM_ID = CONFIG_HON['FORUM_RCT_BUGS_SUBFORUM_ID']
HON_FORUM_CREATE_ALL_THREADS = CONFIG_HON['FORUM_CREATE_ALL_THREADS']
HON_FORUM_SCREENSHOT_LIMIT = CONFIG_HON['FORUM_SCREENSHOT_LIMIT']

#Google
GOOGLE_CLIENT_SECRET_FILE = CONFIG_GOOGLE['CLIENT_SECRET_FILE']
GOOGLE_SCOPES = CONFIG_GOOGLE['SCOPES']

#dynamic
DATABASE_READY = False
LIST_OF_LISTS = None
LIST_OF_LISTS_TRIVIA = None
PLAYER_SLASH_HERO = None #TO DO: this horror to dict
SETTINGS = None #TO DO: dict please
FETCH_SHEET_PASS = 0
OPEN_REPORTS = []
hangmanRunning = False
xpCooldownList = []

winter_solstice = '''Some say the world will end in fire,
Some say in ice.
From what I’ve tasted of desire
I hold with those who favor fire.
But if it had to perish twice,
I think I know enough of hate
To say that for destruction ice
Is also great
And would suffice.

- Robert Frost'''

bot = commands.Bot(command_prefix=['!', '.'], description=winter_solstice)


#-------------------- Decorators --------------------
class DatabaseNotReady(commands.CheckFailure):
    pass

class NotInWhiteList(commands.CheckFailure):
    pass

class NotATester(commands.CheckFailure): #TO DO: special case in handler
    pass

class GuildOnlyCommand(commands.CheckFailure):
    pass

def database_ready():
    #ctx mandatory positional argument
    async def database_ready_check(ctx):
        if not DATABASE_READY:
            raise DatabaseNotReady("Database is not ready!")   
        return True
        #return DATABASE_READY
    return commands.check(database_ready_check)

def in_whitelist(whitelist):
    async def in_whitelist_check(ctx):
        if ctx.author.id not in whitelist:
            raise NotInWhiteList("You're not on the whitelist!")
        return True
    return commands.check(in_whitelist_check)

def is_tester():
    async def is_tester_check(ctx):
        if not DATABASE_READY:
            raise DatabaseNotReady("Database is not ready!")

        found_id = False
        is_enabled = False

        def checkbox_to_bool(checkbox):
            return checkbox.lower() in ('true', '1')

        for x in LIST_OF_LISTS:
            if x[32] == str(ctx.author.id):
                found_id = True
                is_enabled = checkbox_to_bool(x[0])
                break

        return found_id and is_enabled
    return commands.check(is_tester_check)

def guild_only(): #TO DO: this annoyance
    async def guild_only_check(ctx):
        if ctx.message.guild is None:
            raise GuildOnlyCommand("Not allowed in Direct Message!")
        return True
    return commands.check(guild_only_check)


#-------------------- Masterserver Queries --------------------
@bot.command()
@is_tester()
async def version(ctx):
    """Check all RC client versions."""
    global HON_NAEU_RC_MASTERSERVER

    async with ctx.message.channel.typing():

        rc_patcher = f'http://{HON_NAEU_RC_MASTERSERVER}/patcher/patcher.php'

        wrc_query = {'version' : '0.0.0.0', 'os' : f'wrc-{HON_NAEU_RC_OS_PART}', 'arch' : 'i686'}
        lrc_query = {'version' : '0.0.0.0', 'os' : f'lrc-{HON_NAEU_RC_OS_PART}', 'arch' : 'x86-biarch'}
        mrc_query = {'version' : '0.0.0.0', 'os' : f'mrc-{HON_NAEU_RC_OS_PART}', 'arch' : 'universal'}
        
        async with aiohttp.ClientSession() as session:

            async def get_latest_version(url, query):
                async with session.get(url, params=query) as resp:
                    serialized = await resp.text()
                    unserialized = phpserialize.loads(serialized.encode())[0] #deserialize
                    decoded = {k.decode() : v.decode()  for k, v in unserialized.items()}
                    version = decoded['version']
                return version

            wrc = await get_latest_version(rc_patcher, wrc_query)
            lrc = await get_latest_version(rc_patcher, lrc_query)
            mrc = await get_latest_version(rc_patcher, mrc_query)

        await ctx.send(f"**Windows:** {wrc}\n**Mac:** {mrc}\n**Linux:** {lrc}")


@bot.command(name="honstats")
@in_whitelist(DISCORD_WHITELIST_IDS)
async def show_simple_stats(ctx, nickname=None):
    """show_simple_stats ac"""
    global HON_NAEU_MASTERSERVER

    ac_client_requester = 'http://' + HON_NAEU_MASTERSERVER + '/client_requester.php'

    if nickname is None:
        nickname = ctx.author.display_name
    
    query = {'f' : 'show_simple_stats', 'nickname' : nickname}

    async with aiohttp.ClientSession() as session:

        async with session.get(ac_client_requester, params=query) as resp:
            result = await resp.text()
            result = phpserialize.loads(result.encode('utf-8'))
            print(result)
            result = {k.decode('utf-8', 'ignore') : v  for k, v in result.items() if not isinstance(k, int)}
            print(result)
            await ctx.send(result)

@bot.command(name="rchonstats")
@in_whitelist(DISCORD_WHITELIST_IDS)
async def show_simple_stats_rc(ctx, nickname=None):
    """show_simple_stats rc"""
    global HON_NAEU_RC_MASTERSERVER

    rc_client_requester = 'http://' + HON_NAEU_RC_MASTERSERVER + '/client_requester.php'

    if nickname is None:
        nickname = ctx.author.display_name
    
    query = {'f' : 'show_simple_stats', 'nickname' : nickname}

    async with aiohttp.ClientSession() as session:

        async with session.get(rc_client_requester, params=query) as resp:
            result = await resp.text()
            result = phpserialize.loads(result.encode('utf-8'))
            print(result)
            result = {k.decode('utf-8', 'ignore') : v  for k, v in result.items() if not isinstance(k, int)}
            print(result)
            await ctx.send(result)

@bot.command()
@in_whitelist(DISCORD_WHITELIST_IDS)
async def srp(ctx):
    """secure remote password authentication""" #TO DO: remove py 2.7 syntax, fix srp, secrets to conf, f in async, aiohttp, global for cookie
    try:
        import srp
    except:
        pass
    from urllib.request import Request
    from urllib.request import urlopen
    from urllib.parse import urlencode, quote
    #...


#-------------------- RCT Stats --------------------
#TO DO: clean up branching, async functions
@bot.command(aliases=['info', 'sheet', 'rank'])
@database_ready()
async def stats(ctx, member:discord.Member=None):
    """Gets user's RCT game info from the sheet"""
    start = timeit.default_timer()
    global LIST_OF_LISTS
    global LIST_OF_LISTS_TRIVIA
    check_failed = False

    if member is None:
        member = ctx.message.author
    member_discord_id = str(member.id)
    requester_discord_id = str(ctx.message.author.id)
    requester_name = None

    for row in LIST_OF_LISTS:
        if row[32] == member_discord_id:
            row_values = row
        if row[32] == requester_discord_id:
            requester_name = row[1]

    nick = row_values[1]
    nick_lower = nick.lower()

    #check trivia spreadsheet for points
    try:
        for row in LIST_OF_LISTS_TRIVIA:
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

    global PLAYER_SLASH_HERO #TO DO: adapt this horror to dict
    heroes = []
    players = []
    try:
        for x in PLAYER_SLASH_HERO:
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
    await bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id)
    await message.delete()


#-------------------- Forums & Bug Reports --------------------
#TO DO: universal login function
@bot.command()
@commands.has_any_role('Manage Roles', 'Overlord', 'Frostburn Staff', 'Senior Tester', 'Senior Tester Candidate')
async def create(ctx, patch:str=None, link:str=None):
    if patch is None or link is None:
        await ctx.send('The correct format is `.create <version> <patch notes link or Discord>`')
        return
    await ctx.send('Please wait.')
    global HON_FORUM_USER
    global HON_FORUM_USER_MD5_PASSWORD
    global HON_FORUM_USER_ACCOUNT_ID
    global HON_FORUM_ANNOUNCEMENTS_THREAD_ID
    global HON_FORUM_RCT_BUGS_SUBFORUM_ID
    global HON_FORUM_CREATE_ALL_THREADS

    index = 'https://forums.heroesofnewerth.com/index.php'
    login_url = 'https://forums.heroesofnewerth.com/login.php'
    login_params = {'do' : 'login'}
    login_data = {'cookieuser':'1',
                'do':'login',
                's':'',
                'securitytoken':'guest',
                'vb_login_md5password':HON_FORUM_USER_MD5_PASSWORD,
                'vb_login_md5password_utf':HON_FORUM_USER_MD5_PASSWORD,
                'vb_login_password':'',
                'vb_login_password_hint':'Password',
                'vb_login_username':HON_FORUM_USER}

    async with aiohttp.ClientSession() as session:

        async with session.post(login_url, params=login_params, data=login_data) as resp:
            await resp.text()
        
        async with session.get(index) as resp:
            index_get = await resp.text()
            securitytoken = index_get.split('SECURITYTOKEN = "')[1][:51]

        poststarttime = str(int(time()))

        patch_search = "-" + patch.replace(".", "-")

        message_mechanics_general = "[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{0} Bugs - Mechanics[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Mechanics bugs only (and general bugs that don't belong in the other bug threads but aren't art or sound).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{1}\"]{1}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind.".format(patch, link)
        message_tooltips = "[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{0} Bugs - Tooltips[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Tooltip bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{1}\"]{1}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind.".format(patch, link)
        
        #to correct
        posthash_mechanics_general = md5(message_mechanics_general.encode('utf-8')).hexdigest()
        posthash_tooltips = md5(message_tooltips.encode('utf-8')).hexdigest()

        thread_mechanics_general = "{0} Bugs - Mechanics".format(patch)
        thread_tooltips = "{0} Bugs - Tooltips".format(patch)

        thread_mechanics_general_search = "{0}-Bugs-Mechanics\" id=\"thread_title_".format(patch_search)
        thread_tooltips_search = "{0}-Bugs-Tooltips\" id=\"thread_title_".format(patch_search)

        newthread_mechanics_general = {'do':'postthread',
                'f':HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                'iconid':'0',
                'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                'message':message_mechanics_general,
                'message_backup':message_mechanics_general,
                'parseurl':'1',
                'posthash':posthash_mechanics_general,
                'poststarttime':poststarttime,
                'prefixid':'',
                's':'',
                'sbutton':'Submit+New+Thread',
                'securitytoken':securitytoken,
                'signature':'1',
                'subject':thread_mechanics_general,
                'until':'0',
                'wysiwyg':'0'}

        newthread_tooltips = {'do':'postthread',
                'f':HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                'iconid':'0',
                'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                'message':message_tooltips,
                'message_backup':message_tooltips,
                'parseurl':'1',
                'posthash':posthash_tooltips,
                'poststarttime':poststarttime,
                'prefixid':'',
                's':'',
                'sbutton':'Submit+New+Thread',
                'securitytoken':securitytoken,
                'signature':'1',
                'subject':thread_tooltips,
                'until':'0',
                'wysiwyg':'0'}

        if HON_FORUM_CREATE_ALL_THREADS:
            message_ui = "[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{0} - Bugs (UI)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Interface bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{1}\"]{1}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind.".format(patch, link)
            message_sound = "[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{0} - Bugs (Sound)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Sound bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{1}\"]https://forums.heroesofnewerth.com/forumdisplay.php?209-Retail-Candidate-Testers[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind.".format(patch, link)
            message_art = "[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{0} - Bugs (Art)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Art bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{1}\"]{1}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind.".format(patch, link)

            #to correct
            posthash_ui = md5(message_ui.encode('utf-8')).hexdigest()
            posthash_sound = md5(message_sound.encode('utf-8')).hexdigest()
            posthash_art = md5(message_art.encode('utf-8')).hexdigest()

            thread_ui = "{0} Bugs - UI".format(patch)
            thread_sound = "{0} Bugs - Sound".format(patch)
            thread_art = "{0} Bugs - Art".format(patch)

            thread_ui_search = "{0}-Bugs-UI\" id=\"thread_title_".format(patch_search)
            thread_sound_search = "{0}-Bugs-Sound\" id=\"thread_title_".format(patch_search)
            thread_art_search = "{0}-Bugs-Art\" id=\"thread_title_".format(patch_search)


            newthread_ui = {'do':'postthread',
                    'f':HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                    'iconid':'0',
                    'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                    'message':message_ui,
                    'message_backup':message_ui,
                    'parseurl':'1',
                    'posthash':posthash_ui,
                    'poststarttime':poststarttime,
                    'prefixid':'',
                    's':'',
                    'sbutton':'Submit+New+Thread',
                    'securitytoken':securitytoken,
                    'signature':'1',
                    'subject':thread_ui,
                    'until':'0',
                    'wysiwyg':'0'}

            newthread_sound = {'do':'postthread',
                    'f':HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                    'iconid':'0',
                    'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                    'message':message_sound,
                    'message_backup':message_sound,
                    'parseurl':'1',
                    'posthash':posthash_sound,
                    'poststarttime':poststarttime,
                    'prefixid':'',
                    's':'',
                    'sbutton':'Submit+New+Thread',
                    'securitytoken':securitytoken,
                    'signature':'1',
                    'subject':thread_sound,
                    'until':'0',
                    'wysiwyg':'0'}

            newthread_art = {'do':'postthread',
                    'f':HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                    'iconid':'0',
                    'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                    'message':message_art,
                    'message_backup':message_art,
                    'parseurl':'1',
                    'posthash':posthash_art,
                    'poststarttime':poststarttime,
                    'prefixid':'',
                    's':'',
                    'sbutton':'Submit+New+Thread',
                    'securitytoken':securitytoken,
                    'signature':'1',
                    'subject':thread_art,
                    'until':'0',
                    'wysiwyg':'0'}

        async def post_thread(newthread_data):
            newthread_url = 'https://forums.heroesofnewerth.com/newthread.php'
            newthread_params = {'do' : 'postthread', 'f' : HON_FORUM_RCT_BUGS_SUBFORUM_ID}
            async with session.post(newthread_url, params=newthread_params, data=newthread_data) as resp:
                await resp.text()
            return

        await post_thread(newthread_mechanics_general)
        await post_thread(newthread_tooltips)
 
        if HON_FORUM_CREATE_ALL_THREADS:
            await post_thread(newthread_ui)
            await post_thread(newthread_art)
            await post_thread(newthread_sound)

        subforum_url = 'https://forums.heroesofnewerth.com/forumdisplay.php?{0}'.format(HON_FORUM_RCT_BUGS_SUBFORUM_ID)
        
        await ctx.send('Threads have been created and can be viewed here: {0}'.format(subforum_url))
        await asyncio.sleep(1)

        await ctx.send('Updating settings...')

        async with session.get(subforum_url) as resp:
            content = await resp.text()
            thread_mechanics_general_id = content.split(thread_mechanics_general_search)[1][:6]
            thread_tooltips_id = content.split(thread_tooltips_search)[1][:6]

            if HON_FORUM_CREATE_ALL_THREADS:
                thread_ui_id = content.split(thread_ui_search)[1][:6]
                thread_sound_id = content.split(thread_sound_search)[1][:6]
                thread_art_id = content.split(thread_art_search)[1][:6]

        try:
            global GOOGLE_CLIENT_SECRET_FILE
            global GOOGLE_SCOPES

            def get_creds():
                return ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CLIENT_SECRET_FILE, GOOGLE_SCOPES)

            gspread_client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
            gspread_client = await gspread_client_manager.authorize()

            rct_spreadsheet = await gspread_client.open('RCT Spreadsheet')
            settings_worksheet = await rct_spreadsheet.worksheet('Settings')

            #async def save_thread_id(row, thread):
                #return await settings_worksheet.update_acell(row, 2, thread)
            
            #await save_thread_id(8, thread_mechanics_general_id)
            #await save_thread_id(12, thread_tooltips_id)

            await settings_worksheet.update_acell('B8', thread_mechanics_general_id)
            await asyncio.sleep(0.5)
            await settings_worksheet.update_acell('B12', thread_tooltips_id)

            if HON_FORUM_CREATE_ALL_THREADS:
                #await save_thread_id(11, thread_ui_id)
                #await save_thread_id(9, thread_art_id)
                #await save_thread_id(10, thread_sound_id)
                await asyncio.sleep(0.5)
                await settings_worksheet.update_acell('B11', thread_ui_id)
                await asyncio.sleep(0.5)
                await settings_worksheet.update_acell('B9', thread_art_id)
                await asyncio.sleep(0.5)
                await settings_worksheet.update_acell('B10', thread_sound_id)
            
            await ctx.send('Saved succesfully.')
        except:
            await ctx.send('Uh oh, something went wrong. 😦')


#TO DO: could be shorter, too many sleeps, 
@bot.command()
@is_tester()
async def report(ctx):
    global SETTINGS
    global OPEN_REPORTS
    global LIST_OF_LISTS
    global DISCORD_BUGS_CHANNEL_ID
    global DISCORD_BOT_LOG_CHANNEL_ID
    global HON_FORUM_CREATE_ALL_THREADS
    global HON_FORUM_SCREENSHOT_LIMIT
    global DISCORD_WHITELIST_IDS

    report_author = ctx.message.author
    source_channel = ctx.message.channel
    bug_reports_channel = bot.get_channel(DISCORD_BUGS_CHANNEL_ID)

    if report_author not in bug_reports_channel.members or report_author.id not in DISCORD_WHITELIST_IDS: #TO DO: this has to go
        return

    if report_author in OPEN_REPORTS:
        already_pending_content = "You already have a bug report pending, please complete that one first."
        already_pending_message = await report_author.send("{.mention} ".format(report_author) + already_pending_content)
        await asyncio.sleep(8)
        await already_pending_message.edit(content=already_pending_content)
        return

    OPEN_REPORTS.append(report_author)

    report_author_discord_id = str(report_author.id)
    for x in LIST_OF_LISTS:
        if x[32] == report_author_discord_id:
            report_author_verified_name = x[1]
            break

    bc_embed = discord.Embed(title="Bug Report Categories", type="rich", color=0xff6600)
    bc_embed.set_author(name=report_author_verified_name, icon_url=report_author.avatar_url)
    bc_embed.set_footer(text="Please add one of the reactions described above to continue.")
    bc_content = "{.mention} ".format(report_author)
    bc_message = await report_author.send(content=bc_content, embed=bc_embed)

    await bc_message.add_reaction('⚙')
    await bc_message.add_reaction('📋')
    if HON_FORUM_CREATE_ALL_THREADS:
        await bc_message.add_reaction(bc_message, '🎨')
        await asyncio.sleep(0.1)
        await bc_message.add_reaction(bc_message, '🔊')
        await asyncio.sleep(0.1)
        await bc_message.add_reaction(bc_message, '💻')
        await asyncio.sleep(0.1)
    await bc_message.add_reaction('❌')

    bc_embed.add_field(name="Mechanic/General", value='⚙')
    bc_embed.add_field(name="Tooltips", value='📋')
    if HON_FORUM_CREATE_ALL_THREADS:
        bc_embed.add_field(name="Art", value='🎨')
        bc_embed.add_field(name="Sound", value='🔊')
        bc_embed.add_field(name="User Interface", value='💻')
    bc_embed.add_field(name="Cancel", value='❌')
    await bc_message.edit(content=bc_content, embed=bc_embed)

    emojis_dict = {
                '⚙': {'category': 'Mechanics/General', 'threadid': SETTINGS[7]},
                '📋': {'category': 'Tooltips', 'threadid': SETTINGS[11]},
                '🎨': {'category': 'Art', 'threadid': SETTINGS[8]},
                '🔊': {'category': 'Sound', 'threadid': SETTINGS[9]},
                '💻': {'category': 'User Interface', 'threadid': SETTINGS[10]}
                }

    #reaction_symbols = [reaction.emoji for reaction in bc_message.reactions if reaction.emoji in emojis_dict.keys()] #no clue why bc_message.reactions returns an empty list every time
    if HON_FORUM_CREATE_ALL_THREADS:
        reaction_symbols = ['📋','⚙','🎨','🔊','💻','❌']
    else:
        reaction_symbols = ['📋','⚙','❌']

    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in reaction_symbols and reaction.message.id == bc_message.id)
    await bc_message.edit(content=None, embed=bc_embed)
    ##await bot.delete_message(ctx.message)

    if reaction.emoji == '❌':
        cancel_report_content = "Process cancelled. Use `.report` to start over."
        cancel_report_message = await report_author.send("{.mention} ".format(report_author) + cancel_report_content)
        OPEN_REPORTS.remove(report_author)
        await asyncio.sleep(8)
        await cancel_report_message.edit(content=cancel_report_content)
        return
    else:
        bug_category = emojis_dict[reaction.emoji]['category']
        threadid = emojis_dict[reaction.emoji]['threadid']
        proceed_prompt_content = "You chose to report a **{}** bug. Do you wish to proceed?".format(bug_category)
        proceed_prompt_message = await report_author.send("{.mention} ".format(report_author) + proceed_prompt_content)

    await proceed_prompt_message.add_reaction('✅')
    await proceed_prompt_message.add_reaction('❌')
    
    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in ['✅','❌'] and reaction.message.id == proceed_prompt_message.id)
    await proceed_prompt_message.edit(content=proceed_prompt_content)
    
    if reaction.emoji == '❌':
        proceed_prompt_no_content = "Process cancelled. Use `.report` to start over."
        proceed_prompt_no_message = await report_author.send("{.mention} ".format(report_author) + proceed_prompt_no_content)
        OPEN_REPORTS.remove(report_author)
        await asyncio.sleep(8)
        await proceed_prompt_no_message.edit(content=proceed_prompt_no_content)
        return

    ask_for_version_content = "Please enter the **version** of the RCT client. Format: `<0.xx.xxx>` e.g. `0.27.231.1`"
    ask_for_version_message = await report_author.send("{.mention} ".format(report_author) + ask_for_version_content)
    rc_version_message = await bot.wait_for('message', check=lambda m: m.author == report_author)
    await ask_for_version_message.edit(content=ask_for_version_content)

    ask_for_build_date_content = "Please enter the **build date** of the RCT client. Format: `<Day Month Year>` e.g. `2 April 2018`"
    ask_for_build_date_message = await report_author.send("{.mention} ".format(report_author) + ask_for_build_date_content)
    build_date_message = await bot.wait_for('message', check=lambda m: m.author == report_author)
    await ask_for_build_date_message.edit(content=ask_for_build_date_content)

    ask_for_screenshots_content = "Please enter the **number of screenshots** your have. Format : `<integer>` e.g.  `2`\nIn case you don't have any screenshots or want to include them in the description instead, enter `0` to proceed."
    ask_for_screenshots_message = await report_author.send("{.mention} ".format(report_author) + ask_for_screenshots_content)
    number_of_screenshots_message = await bot.wait_for('message', check=lambda m: m.author == report_author)
    await ask_for_screenshots_message.edit(content=ask_for_screenshots_content)

    screenshots_list = []
    try:
        number_of_screenshots = int(number_of_screenshots_message.content)
        if number_of_screenshots > HON_FORUM_SCREENSHOT_LIMIT:
            number_of_screenshots = HON_FORUM_SCREENSHOT_LIMIT
            too_many_screenshots_content = "That might be too many screenshots. Your entry has been changed to `{}`. If the screenshots excluded were necessary, please add them to the description.".format(number_of_screenshots)
            too_many_screenshots_message = await report_author.send("{.mention} ".format(report_author) + too_many_screenshots_content)
            await asyncio.sleep(8)
            await too_many_screenshots_message.edit(content=too_many_screenshots_content)

        for i in range(1, number_of_screenshots+1, 1):
            ask_for_screenshot_link_content = "Please enter the **screenshot link** number {} of the bug. e.g. `https://i.imgur.com/D0Yn9JC.png`".format(i)
            ask_for_screenshot_link_message = await report_author.send("{.mention} ".format(report_author))
            screenshot_link_message = await bot.wait_for('message', check=lambda m: m.author == report_author)
            screenshots_list.append(screenshot_link_message.content)
            await ask_for_screenshot_link_message.edit(content=ask_for_screenshot_link_content)

    except:
        screenshots_not_integer_content = "Your input was not an integer. If this is a mistake, please add your screenshots to the bug description."
        screenshots_not_integer_message = await report_author.send("{.mention} ".format(report_author) + screenshots_not_integer_content)
        await asyncio.sleep(8)
        await screenshots_not_integer_message.edit(content=screenshots_not_integer_content)

    ask_for_description_content = "Please enter the **description** of the bug, up to 2000 characters. Use `Shift + Enter` for new lines, `Enter` to submit. e.g. `This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.`"
    ask_for_description_message = await report_author.send("{.mention} ".format(report_author) + ask_for_description_content)
    bug_description_message = await bot.wait_for('message', check=lambda m: m.author == report_author)
    await ask_for_description_message.edit(content=ask_for_description_content)

    if len(screenshots_list) < 1:
        screenshots_list_message = ''
        screenshots_list_message_discord = ''
    else:
        screenshots_list_message = '[QUOTE]' + '\n '.join(screenshots_list) + '[/QUOTE]\n\n'
        screenshots_list_message_discord = '\n'.join(screenshots_list) + '\n\n'
        if len(screenshots_list_message_discord) > 200:
            screenshots_list_message_discord = screenshots_list_message_discord[:200] + '...\n\n'

    bug_description_discord = bug_description_message.content
    if len(bug_description_discord) > 1200:
        bug_description_discord = bug_description_discord[:1200] + '...'

    final_report_prompt_content = "Is this your final report?\n```Version: {0}\nBuild date: {1}\n\n{2}{3}```".format(rc_version_message.content, build_date_message.content, screenshots_list_message_discord, bug_description_discord)
    final_report_prompt_message = await report_author.send("{.mention} ".format(report_author) + final_report_prompt_content)

    await final_report_prompt_message.add_reaction('✅')
    await final_report_prompt_message.add_reaction('❌')

    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in ['✅','❌'] and reaction.message.id == final_report_prompt_message.id)
    await final_report_prompt_message.edit(content=final_report_prompt_content)

    if reaction.emoji == '❌':
        final_report_discarded_content = "Your report has been discarded."
        final_report_discarded_message = await report_author.send("{.mention} ".format(report_author))
        OPEN_REPORTS.remove(report_author)
        await asyncio.sleep(8)
        await final_report_discarded_message.edit(content=final_report_discarded_content)
        return

    global HON_FORUM_USER
    global HON_FORUM_USER_MD5_PASSWORD
    global HON_FORUM_USER_ACCOUNT_ID

    index = 'https://forums.heroesofnewerth.com/index.php'
    login_url = 'https://forums.heroesofnewerth.com/login.php'
    login_params = {'do' : 'login'}
    login_data = {'cookieuser':'1',
                'do':'login',
                's':'',
                'securitytoken':'guest',
                'vb_login_md5password':HON_FORUM_USER_MD5_PASSWORD,
                'vb_login_md5password_utf':HON_FORUM_USER_MD5_PASSWORD,
                'vb_login_password':'',
                'vb_login_password_hint':'Password',
                'vb_login_username':HON_FORUM_USER}
    
    async with aiohttp.ClientSession() as session:

            async with session.post(login_url, params=login_params, data=login_data) as resp:
                await resp.text()
            
            async with session.get(index) as resp:
                index_get = await resp.text()
                securitytoken = index_get.split('SECURITYTOKEN = "')[1][:51]
            
            poststarttime = str(int(time()))
            message = "[COLOR=#0099FF]Version:[/COLOR] {0}\n[COLOR=#0099FF]Build date:[/COLOR] {1}\n\n{2}{3}\n\n\nReported by: [COLOR=#00cc99]{4}[/COLOR] ({5.name}#{5.discriminator})".format(rc_version_message.content, build_date_message.content, screenshots_list_message, bug_description_message.content, report_author_verified_name, report_author)
            posthash = md5(message.encode()).hexdigest()
            new_reply_url = 'https://forums.heroesofnewerth.com/newreply.php'
            post_params = {'do' : 'postreply', 't' : threadid}
            #thread = 'https://forums.heroesofnewerth.com/newreply.php?do=postreply&t={0}'.format(threadid)
            post = {'ajax':'1',
                    'ajax_lastpost':'',
                    'do':'postreply',
                    'fromquickreply':'1',
                    'loggedinuser':'9040128',
                    'securitytoken':securitytoken,
                    'message':message,
                    'message_backup':message,
                    'p':'who cares',
                    'parseurl':'1',
                    'post_as':'9040128',
                    'posthash':posthash,
                    'poststarttime':poststarttime,
                    's':'',
                    'securitytoken':securitytoken,
                    'signature':'1',
                    'specifiedpost':'0',
                    't':threadid,
                    'wysiwyg':'0'}
            
            async with session.post(new_reply_url, params=post_params, data=post) as resp:
                await resp.text()

    #await report_author.send("{0}, your report has been posted in the **{1}** thread and can be viewed here: https://forums.heroesofnewerth.com/showthread.php?{2}&goto=newpost".format(report_author.mention,bug_category,threadid))
    is_this_valid  = await bug_reports_channel.send("{0}, your report has been posted in the **{1}** thread and can be viewed here: https://forums.heroesofnewerth.com/showthread.php?{2}&goto=newpost\n```Version: {3}\nBuild date: {4}\n\n{5}{6}\n\n\nReported by: {7} ({8.name}#{8.discriminator})```<@&248187345776410625> Awaiting decision.".format(report_author.mention, bug_category, threadid, rc_version_message.content, build_date_message.content, screenshots_list_message_discord, bug_description_discord, report_author_verified_name, report_author))

    def get_creds():
        return ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CLIENT_SECRET_FILE, GOOGLE_SCOPES)

    gspread_client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    gspread_client = await gspread_client_manager.authorize()

    rct_spreadsheet = await gspread_client.open('RCT Spreadsheet')
    bug_reports_worksheet = await rct_spreadsheet.worksheet('Bug Reports')
    bug_reporters = await bug_reports_worksheet.col_values(1)

    reporters = []
    for i in bug_reporters:
        if i == "":
            break
        reporters.append(i)
    
    k = -1
    for i in range(0, len(reporters), 1):
        if reporters[i] == report_author_verified_name:
            k = i
            break
    #add +1 report
    if k == -1:
        val = 1
        await bug_reports_worksheet.update_cell(len(reporters)+1, 1, report_author_verified_name)
        await bug_reports_worksheet.update_cell(len(reporters)+1, 2, str(val))
    else:
        old_value = await bug_reports_worksheet.cell(k+1, 2)
        old_value = old_value.value
        new_value = int(old_value)+1
        await bug_reports_worksheet.update_cell(k+1, 2, str(new_value))

    #is_this_valid=await report_author.send("@Senior Tester , is this a valid bug report?")
    OPEN_REPORTS.remove(report_author)
    await is_this_valid.add_reaction('✅')
    await is_this_valid.add_reaction('❌')
    await is_this_valid.add_reaction('⚠')

    await asyncio.sleep(0.5)

    senior_tester_name = ''

    def check(reaction, user):
        global senior_tester_name
        if reaction.message.id != is_this_valid.id or reaction.emoji not in ['✅','❌','⚠']: 
            return False
        guild = bug_reports_channel.guild
        check_user_roles = user.roles
        frostburn = discord.utils.get(guild.roles, name="Senior Tester")
        senior = discord.utils.get(guild.roles, name="Frostburn Staff")
        if senior in check_user_roles or frostburn in check_user_roles:
            senior_tester_id = str(user.id)
            for x in LIST_OF_LISTS:
                if x[32] == senior_tester_id:
                    senior_tester_verified_name = x[1]
                    break
            senior_tester_name = '{0} ({1.name}#{1.discriminator})'.format(senior_tester_verified_name, user)
        return senior in check_user_roles or frostburn in check_user_roles

    #validate=await bot.wait_for_reaction(['✅','❌','⚠'],message=is_this_valid,check=check)
    reaction, user = await bot.wait_for('reaction_add', check=check)

    if reaction.emoji == '❌':
        if k == -1:
            val=0
            await bug_reports_worksheet.update_cell(len(reporters)+1, 1, report_author_verified_name)
            await bug_reports_worksheet.update_cell(len(reporters)+1, 2, str(val))
        else:
            old_value = await bug_reports_worksheet.cell(k+1, 2)
            old_value = old_value.value
            new_value = int(old_value)-1
            await bug_reports_worksheet.update_cell(k+1, 2, str(new_value))
        old_content = is_this_valid.content
        new_content = old_content[:-41] + "❌ This report has been rejected by {0}.".format(senior_tester_name)
        await is_this_valid.edit(content=new_content)

    elif reaction.emoji == '⚠':
        if k == -1:
            val = 0
            await bug_reports_worksheet.update_cell(len(reporters)+1, 1, report_author_verified_name)
            await bug_reports_worksheet.update_cell(len(reporters)+1, 2, str(val))
        else:
            old_value = await bug_reports_worksheet.cell(k+1, 2)
            old_value = old_value.value
            new_value = int(old_value)-1
            await bug_reports_worksheet.update_cell(k+1, 2, str(new_value))
        old_content = is_this_valid.content
        new_content = old_content[:-41] + "⚠ This report has been deemed valid by {0}, but a smilar or related one was already submitted.".format(senior_tester_name)
        await is_this_valid.edit(content=new_content)

    else:
        old_content = is_this_valid.content
        new_content = old_content[:-41] + "✅ This report has been approved by {0}.".format(senior_tester_name)
        await is_this_valid.edit(content=new_content)

    return #aaaaaaalllllriiiight


#TO DO: this needs to be prettier
@bot.command()
@commands.has_any_role('Manage Roles', 'Overlord', 'Frostburn Staff', 'Senior Tester', 'Senior Tester Candidate')
async def hero(ctx):
    global PLAYER_SLASH_HERO

    hul_embed = discord.Embed(title="Hero Usage List", type="rich", color=0xff6600)
    hul_embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
    hul_embed.add_field(name="By Hero", value='📈')
    hul_embed.add_field(name="By Player", value='📉')
    hul_embed.add_field(name="Show All Picks", value='📊')
    hul_embed.set_footer(text="Please add one of the reactions above to continue.")
    hul_message = await ctx.send(embed=hul_embed)
    #await asyncio.sleep(0.1)
    await hul_message.add_reaction('📈')
    await hul_message.add_reaction('📉')
    await hul_message.add_reaction('📊')
    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji in ['📈','📉','📊'] and reaction.message.id == hul_message.id)
    #reaction_action=await bot.wait_for_reaction(['📈','📉','📊'], user=ctx.message.author, timeout=60.0, message=hul_message)
    await hul_message.delete()
    start = timeit.default_timer()
    try:
        if reaction.emoji == '📊':
            heroes = []
            try:
                for x in PLAYER_SLASH_HERO:
                    if x != '' and '/' in x:
                        y = x.split(',')
                        for z in y:
                            k = z.split('/')[1]
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
                hero_percent.append(round((int(val)*100)/len(heroes), 2))
                hero_no_percent.append(int(val))
            for hero in hero_keys:
                last_hero.append(hero)
            for percent in range(0, len(hero_percent), 1):
                discord_message.append("\n{0}: **{1}** ({2}%)".format(last_hero[percent], hero_no_percent[percent], hero_percent[percent]))

            discord_message.sort()

            length = len(hero_percent)
            if length <= 50:
                await ctx.send('Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**'.format(len(heroes),length))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:length]))
            elif length <= 100:
                await ctx.send('Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**'.format(len(heroes),length))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:50]))
                await ctx.send(''.join(discord_message[50:length]))
            elif length<=150:
                await ctx.send('Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**'.format(len(heroes),length))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:50]))
                await ctx.send(''.join(discord_message[50:100]))
                await ctx.send(''.join(discord_message[100:length]))
            else:
                await ctx.send('Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**'.format(len(heroes),length))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:50]))
                await ctx.send(''.join(discord_message[50:100]))
                await ctx.send(''.join(discord_message[100:150]))
                await ctx.send(''.join(discord_message[150:length]))
        
        elif reaction.emoji == '📈':
            heroes = []
            players = []
            try:
                for x in PLAYER_SLASH_HERO:
                    if x!='' and '/' in x:
                        y=x.split(',')
                        for z in y:
                            h=z.split('/')[0]
                            h=h.strip(' ')
                            k=z.split('/')[1]
                            heroes.append(k)
                            players.append(h)
            except:
                await ctx.send("Please convert to proper format first.")
                return
            await ctx.send("Please enter the name of the hero:")
            wf_message = await bot.wait_for('message', check=lambda m: m.author == ctx.message.author)
            hero_name = wf_message.content
            hero_name_lower = hero_name.lower()
            try:
                [x.lower() for x in heroes].index(hero_name_lower)
            except:
                await ctx.send("**{0}** was not picked this cycle.".format(hero_name.title()))
                return
            hero_counter = 0
            for i in heroes:
                if i == hero_name:
                    hero_counter += 1
            #heroPercentage=((hero_counter*100)/len(heroes))
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
                if i == (len(played_by_o)-1):
                    temp = "\n" + played_by_o[i] + ": **" + nb_plays_c[i] + "**"
                    discord_message.append(temp)
                else:
                    temp = "\n" + played_by_o[i] + ": **" + nb_plays_c[i] + "**"
                    discord_message.append(temp)
            discord_message.sort()
            length = len(discord_message)
            if length <= 50:
                await ctx.send('**{0}** was picked by:'.format(hero_name))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:length]))
            elif length <= 100:
                await ctx.send('**{0}** was picked by:'.format(hero_name))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:50]))
                await ctx.send(''.join(discord_message[50:length]))
            else:
                await ctx.send('**{0}** was picked by:'.format(hero_name))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(discord_message[0:50]))
                await ctx.send(''.join(discord_message[50:100]))
                await ctx.send(''.join(discord_message[100:length]))
        elif reaction.emoji == '📉':
            heroes = []
            players = []
            try:
                for x in PLAYER_SLASH_HERO:
                    if x != '' and '/' in x:
                        y = x.split(',')
                        for z in y:
                            h = z.split('/')[0]
                            h = h.strip(' ')
                            k = z.split('/')[1]
                            heroes.append(k)
                            players.append(h)
            except Exception:
                await ctx.send("Please convert to proper format first.")
                return
            await ctx.send("Please enter the name of the player:")
            wf_message = await bot.wait_for('message', check=lambda m: m.author == ctx.message.author)
            playerName = wf_message.content
            playerNameLower=playerName.lower()
            try:
                [x.lower() for x in players].index(playerNameLower)
            except:
                await ctx.send("**{0}** did not play this cycle.".format(playerName))
                return
            playedHeroes=[]
            for i in range(0,len(players)):
                if players[i].lower()==playerNameLower:
                    playedHeroes.append(heroes[i])
                    playerName=players[i]
            playedHeroes=collections.Counter(playedHeroes)
            heroesNames=playedHeroes.keys()
            heroesCount=playedHeroes.values()
            hero_name=[]
            heroCount=[]
            for i in heroesNames:
                hero_name.append(i)
            for i in heroesCount:
                heroCount.append(str(i))
            lastHero=[]
            for i in range(0,len(hero_name)):
                if i==(len(hero_name)-1):
                    temp="\n"+hero_name[i]+": **"+heroCount[i]+"**"
                    lastHero.append(temp)
                else:
                    temp="\n"+hero_name[i]+": **"+heroCount[i]+"**"
                    lastHero.append(temp)
            lastHero.sort()
            length=len(lastHero)
            if length <= 50:
                await ctx.send("Hero picks for **{0}**:".format(playerName))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(lastHero[0:length]))
            elif length <= 100:
                await ctx.send("Hero picks for **{0}**:".format(playerName))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(lastHero[0:50]))
                await ctx.send(''.join(lastHero[50:length]))
            else:
                await ctx.send("Hero picks for **{0}**:".format(playerName))
                #await asyncio.sleep(0.25)
                await ctx.send(''.join(lastHero[0:50]))
                await ctx.send(''.join(lastHero[50:100]))
                await ctx.send(''.join(lastHero[100:length]))
    except Exception:
        return
    stop = timeit.default_timer()
    print(stop-start)


#-------------------- Patch Notes --------------------
@bot.command()
@is_tester()
async def notes(ctx):
    """Returns current testing notes"""
    global HON_ALT_DOMAIN
    global HON_CAT_PASSWORD
    global DISCORD_NOTES_CHANNEL_ID

    author = ctx.message.author
    log_channel = bot.get_channel(DISCORD_NOTES_CHANNEL_ID)

    token_generator = f'https://{HON_ALT_DOMAIN}/site/create-access-token'
    cat_query = {'discordId' : author.id, 'password' : HON_CAT_PASSWORD}
    
    async with aiohttp.ClientSession() as session:

        async with session.get(token_generator, params=cat_query) as resp:
            token = await resp.text()

    notes_url = f'https://{HON_ALT_DOMAIN}/{token}'
    await author.send(f'Current Testing Notes: {notes_url}')
    await log_channel.send(f'({strftime("%a, %d %b %Y, %H:%M:%S %Z", gmtime())}) {author.mention} received Testing Notes with the URL: `{notes_url}`')


#-------------------- Moderation --------------------
@bot.command(aliases=['clear', 'delete'])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, number:int, offender:discord.Member=None):
    channel = ctx.message.channel
    if number < 2 or number > 99:
        message = await ctx.send('Invalid number of messages.')
        await message.add_reaction('🆗')
        await bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
        await message.delete()
        return

    if offender is not None:
        if offender == ctx.message.author:
            number += 1 #accounting for command invoking message
        messages = []
        counter = 0
        async for message_sent in channel.history(limit=250):
            if counter == number: break
            if message_sent.author == offender:
                messages.append(message_sent)
                counter += 1
        await channel.delete_messages(messages)
        message = await ctx.send('Deleted the last {0} messages from {1.mention}.'.format(len(messages), offender))
        await message.add_reaction('🆗')
        await bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
        await message.delete()

    else:
        #messages = await channel.history(limit=number).flatten()
        deleted = await channel.purge(limit=number+1) #accounting for command invoking message
        message = await ctx.send('Deleted the last {} messages.'.format(len(deleted)))
        await message.add_reaction('🆗')
        await bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
        await message.delete()


#-------------------- Games --------------------
@bot.command()
async def roll(ctx, low : int, high : int):
    """Let's roll the dice!"""
    result = random.randint(low, high)
    await ctx.send('{0} rolled {1} {2} and got **{3}**.'.format(ctx.message.author.mention, low, high, result))


#-------------------- Misc --------------------
@bot.command()
async def cat(ctx):
    """Get a random cat image from The Cat API."""
    search_url = 'https://api.thecatapi.com/v1/images/search'
    try:
        search_headers = {'x-api-key' : CONFIG['CAT']['x-api-key']}
    except:
        search_headers = None

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=search_headers) as resp:
            json_resp = await resp.json()
    
    cat_dict = json_resp[0]
    cat_img_url = cat_dict['url']

    await ctx.send(f'{cat_img_url}')


@bot.command()
async def dog(ctx):
    """Get a random dog image from The Dog API."""
    search_url = 'https://api.thedogapi.com/v1/images/search'
    try:
        search_headers = {'x-api-key' : CONFIG['DOG']['x-api-key']}
    except:
        search_headers = None

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=search_headers) as resp:
            json_resp = await resp.json()
    
    dog_dict = json_resp[0]
    dog_img_url = dog_dict['url']

    await ctx.send(f'{dog_img_url}')


#-------------------- Events, Error Handling & Debugging --------------------
@bot.command()
@in_whitelist(DISCORD_WHITELIST_IDS)
async def dev_permission_test(ctx):
    await ctx.send("{.mention} You do have permission.".format(ctx.message.author))


@bot.event
async def on_ready():
    print('{0} ({0.id}) reporting for duty from {1}! All shall respect the law that is my {2}!'.format(bot.user, platform.platform(), CONFIG_FILE))
    watching = discord.Activity(name="Heroes of Newerth", type=discord.ActivityType.watching)
    #streaming = discord.Streaming(platform="Twitch", name="Heroes of Newerth", game="Heroes of Newerth", url="https://www.twitch.tv/", twitch_name="")
    await bot.change_presence(activity=watching, status=discord.Status.dnd, afk=False)
    print('------')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, NotInWhiteList):
        await ctx.author.send(error)

    if isinstance(error, DatabaseNotReady):
        await ctx.send("{.mention} Slow down speedy, I just woke up. Try *me* again in a few seconds.".format(ctx.author))

    print(error)
    return

@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)

    if message.guild is None and ctx.valid: #TO DO: with guild_only and dm_allowed
        #print([f.__name__ for f in ctx.command.checks])
        if ctx.command.name not in DISCORD_DM_COMMANDS:
            print("{0.name}#{0.discriminator} ({0.id}) tried to invoke {1} in Direct Message: {2}".format(message.author, ctx.command, message.content))
            return

    # if ctx.valid:
    #     if ctx.command in DISCORD_DM_COMMANDS and message.author.id not in DISCORD_WHITELIST_IDS:
    #         await message.author.send("You do not have permission.")
    #     else:
    #         await bot.process_commands(message)
    # else:
    #     pass

    if message.channel.id == DISCORD_ANNOUNCEMENTS_CHANNEL_ID:
        global DISCORD_FORUMS_ROLE_ID
        if DISCORD_FORUMS_ROLE_ID in message.raw_role_mentions:
            global HON_FORUM_USER
            global HON_FORUM_USER_MD5_PASSWORD
            global HON_FORUM_USER_ACCOUNT_ID
            global HON_FORUM_ANNOUNCEMENTS_THREAD_ID

            index = 'https://forums.heroesofnewerth.com/index.php'
            login_url = 'https://forums.heroesofnewerth.com/login.php'
            login_params = {'do' : 'login'}
            login_data = {'cookieuser':'1',
                        'do':'login',
                        's':'',
                        'securitytoken':'guest',
                        'vb_login_md5password':HON_FORUM_USER_MD5_PASSWORD,
                        'vb_login_md5password_utf':HON_FORUM_USER_MD5_PASSWORD,
                        'vb_login_password':'',
                        'vb_login_password_hint':'Password',
                        'vb_login_username':HON_FORUM_USER}

            async with aiohttp.ClientSession() as session:

                async with session.post(login_url, params=login_params, data=login_data) as resp:
                    await resp.text()
                
                async with session.get(index) as resp:
                    index_get = await resp.text()
                    securitytoken = index_get.split('SECURITYTOKEN = "')[1][:51]
                
                content = message.content.split(DISCORD_FORUMS_ROLE_ID)[1].strip(' ')
                announcement = "{0}\n\n\nMade by: [COLOR=#00cc99]{1.display_name}[/COLOR] ({1.name}#{1.discriminator})".format(content, message.author)
                poststarttime = str(int(time()))
                posthash = md5(announcement.encode('utf-8')).hexdigest() #"This is fine."

                new_reply_url = 'https://forums.heroesofnewerth.com/newreply.php'
                post_params = {'do' : 'postreply', 't' : HON_FORUM_ANNOUNCEMENTS_THREAD_ID}
                post_data = {'ajax':'1',
                            'ajax_lastpost':'',
                            'do':'postreply',
                            'fromquickreply':'1',
                            'loggedinuser':HON_FORUM_USER_ACCOUNT_ID,
                            'securitytoken':securitytoken,
                            'message':announcement,
                            'message_backup':announcement,
                            'p':'who cares',
                            'parseurl':'1',
                            'post_as':HON_FORUM_USER_ACCOUNT_ID,
                            'posthash':posthash,
                            'poststarttime':poststarttime,
                            's':'',
                            'securitytoken':securitytoken,
                            'signature':'1',
                            'specifiedpost':'0',
                            't':HON_FORUM_ANNOUNCEMENTS_THREAD_ID,
                            'wysiwyg':'0'}
                
                async with session.post(new_reply_url, params=post_params, data=post_data) as resp:
                    await resp.text()

    await bot.process_commands(message)


#-------------------- Background Tasks --------------------
async def fetch_sheet():
    await bot.wait_until_ready()
    global GOOGLE_CLIENT_SECRET_FILE
    global GOOGLE_SCOPES

    global LIST_OF_LISTS
    global LIST_OF_LISTS_TRIVIA
    global SETTINGS
    global PLAYER_SLASH_HERO
    global FETCH_SHEET_PASS

    global DATABASE_READY

    def get_creds():
        return ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CLIENT_SECRET_FILE, GOOGLE_SCOPES)
    
    gspread_client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

    count_pass = 0
    #while not bot.is_closed:
    while True:
        gspread_client = await gspread_client_manager.authorize() #"This is fine." (It's actually fine, for real. gspread_asyncio has a cache.)

        #spreadsheet and worksheets
        rct_spreadsheet = await gspread_client.open('RCT Spreadsheet')
        rewards_worksheet = await rct_spreadsheet.worksheet('RCT Players and Rewards')
        trivia_worksheet = await rct_spreadsheet.worksheet('trivia_sheet')
        settings_worksheet = await rct_spreadsheet.worksheet('Settings')
        games_worksheet = await rct_spreadsheet.worksheet('Games')

        #update globals
        LIST_OF_LISTS = await rewards_worksheet.get_all_values()
        LIST_OF_LISTS_TRIVIA = await trivia_worksheet.get_all_values()
        SETTINGS = await settings_worksheet.col_values(2)
        PLAYER_SLASH_HERO = await games_worksheet.col_values(13)

        DATABASE_READY = True
        
        count_pass += 1
        FETCH_SHEET_PASS = count_pass
        if count_pass <= 2:
            print ('fetch_sheet pass {0}'.format(FETCH_SHEET_PASS))

        await asyncio.sleep(60)


bot.remove_command('help')

bot.loop.create_task(fetch_sheet())

bot.run(DISCORD_TOKEN)