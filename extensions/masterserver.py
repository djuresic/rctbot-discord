import binascii
from hashlib import md5, sha256

import asyncio
import aiohttp
import discord
from discord.ext import commands

import utils.phpserialize as phpserialize
import srp

import config
from extensions.checks import is_tester, is_senior, in_whitelist, is_authenticated
# import extensions.administration as administration


async def translate_masterserver(masterserver, short=True):
    info = config.HON_MASTERSERVER_INFO[masterserver]
    if short:
        return info['short']
    else:
        return info['client']


async def authenticate_and_update_info(masterserver):
    info = config.HON_MASTERSERVER_INFO[masterserver]
    data = await authenticate(masterserver, info['user'], info['password'])

    try:
        config.HON_MASTERSERVER_INFO[masterserver]['cookie'] = data[b'cookie'].decode()
        config.HON_MASTERSERVER_INFO[masterserver]['ip'] = data[b'ip'].decode()
        config.HON_MASTERSERVER_INFO[masterserver]['auth_hash'] = data[b'auth_hash'].decode()
        config.HON_MASTERSERVER_INFO[masterserver]['chat_url'] = data[b'chat_url'].decode()
        config.HON_MASTERSERVER_INFO[masterserver]['chat_port']= int(data[b'chat_port'].decode())
        config.HON_MASTERSERVER_INFO[masterserver]['account_id'] = int(data[b'account_id'].decode())
        config.HON_MASTERSERVER_INFO[masterserver]['nickname'] = data[b'nickname'].decode()

        config.HON_MASTERSERVER_INFO[masterserver]['authenticated'] = True
        print(f"{info['short']} authenticated!")
        return True

    except:
        config.HON_MASTERSERVER_INFO[masterserver]['authenticated'] = False
        print(f"{info['short']} failed to authenticate!")
        return False


async def request(session, query, masterserver='ac', path=None, cookie=False, deserialize=True): # default to RC masterserver instead
    # print(query)
    info = config.HON_MASTERSERVER_INFO[masterserver]

    if path is None:
        path = 'client_requester.php'

    if cookie:
        query['cookie'] = info['cookie']

    hostname = info['hostname']
    version = info['version']
    headers = {'User-Agent': f'{config.HON_GAME_CLIENT}/{version}/l{masterserver}/x86-biarch', 'X-Forwarded-For': 'unknown'}
    # print(headers)

    async with session.get('http://{0}/{1}'.format(hostname, path), params=query, headers=headers) as resp:
        try:
            data = await resp.text()
        except:
            print("Something went wrong while querying masterserver")
            return None
        if deserialize:
            return phpserialize.loads(data.encode())
        else:
            return data


async def authenticate(masterserver, login, password): # <3
    session = aiohttp.ClientSession()
    login = login.lower()
    query = {'f': 'pre_auth', 'login': login}
    srp.rfc5054_enable()
    user = srp.User(login.encode(), None, hash_alg=srp.SHA256, ng_type=srp.NG_CUSTOM, n_hex=config.HON_S2_N.encode(), g_hex=config.HON_S2_G.encode())
    _, A = user.start_authentication()
    query['A'] = binascii.hexlify(A).decode()
    result = await request(session, query, masterserver=masterserver)
    if b'B' not in result: return result
    s = binascii.unhexlify(result[b'salt'])
    B = binascii.unhexlify(result[b'B'])
    salt2 = result[b'salt2']
    user.password = (sha256((md5((md5(password.encode()).hexdigest()).encode() + salt2 + config.HON_SRP_SS.encode()).hexdigest()).encode() + config.HON_SRP_SL.encode()).hexdigest()).encode()
    user.p = user.password
    M = user.process_challenge(s, B)
    del(query['A'])
    query['f'] = 'srpAuth'
    query['proof'] = binascii.hexlify(M).decode()
    result = await request(session, query, masterserver=masterserver)
    await session.close()
    # print(result)
    return result

async def nick2id(nickname, masterserver='ac'):
    async with aiohttp.ClientSession() as session:
        result = await request(session, {'f': 'nick2id', 'nickname[]': nickname.lower()}, masterserver=masterserver)
        account_id = [value.lower() for value in result.values() if isinstance(value, bytes)][0] # Not great
        cs_nickname = [key for key, value in result.items() if value == account_id][0]
    return {'nickname': cs_nickname.decode(), 'account_id': account_id.decode()}

async def id2nick(account_id, masterserver='ac'):
    async with aiohttp.ClientSession() as session:
        result = await request(session, {'f': 'id2nick', 'account_id[]': account_id}, masterserver=masterserver)
        try:
            nickname = result[int(account_id)]
        except:
            nickname = result
    return nickname


class Masterserver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_tester()
    async def version(self, ctx, masterserver: str='rc'):
        """Check all client versions for <masterserver>. Defaults to RCT masterserver."""

        client_os = {
            'ac': 'ac',
            'rc': f'rc-{config.HON_NAEU_RC_OS_PART}',
            'tc': f'tc-{config.HON_NAEU_TC_OS_PART}'
        }
        client = await translate_masterserver(masterserver, short=False)

        async with ctx.message.channel.typing():
            w_query = {'version' : '0.0.0.0', 'os' : f'w{client_os[masterserver]}', 'arch' : 'i686'}
            l_query = {'version' : '0.0.0.0', 'os' : f'l{client_os[masterserver]}', 'arch' : 'x86-biarch'}
            m_query = {'version' : '0.0.0.0', 'os' : f'm{client_os[masterserver]}', 'arch' : 'universal'}
            
            async with aiohttp.ClientSession() as session:
                w_version = (await request(session, w_query, masterserver, 'patcher/patcher.php'))[0][b'version'].decode()
                l_version = (await request(session, l_query, masterserver, 'patcher/patcher.php'))[0][b'version'].decode()
                m_version = (await request(session, m_query, masterserver, 'patcher/patcher.php'))[0][b'version'].decode()

            await ctx.send(f"{client}\n\n**Windows:** {w_version}\n**Mac:** {l_version}\n**Linux:** {m_version}")


    @commands.command(name="sstats")
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def show_simple_stats(self, ctx, nickname=None, masterserver='ac'): # Dev purpose only
        """show_simple_stats"""

        if nickname is None:
            nickname = ctx.author.display_name
        
        query = {'f' : 'show_simple_stats', 'nickname' : nickname.lower()}

        async with aiohttp.ClientSession() as session:
            print(await request(session, query, masterserver=masterserver))

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def readc(self, ctx):
        await ctx.send(f"ac: {config.HON_MASTERSERVER_INFO['ac']['cookie']},\nrc: {config.HON_MASTERSERVER_INFO['rc']['cookie']},\ntc: {config.HON_MASTERSERVER_INFO['tc']['cookie']}")

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def forcesrp(self, ctx):
        await authenticate_and_update_info('ac')
        await authenticate_and_update_info('rc')
        await authenticate_and_update_info('tc')
        await ctx.send(f"ac: {config.HON_MASTERSERVER_INFO['ac']['cookie']},\nrc: {config.HON_MASTERSERVER_INFO['rc']['cookie']},\ntc: {config.HON_MASTERSERVER_INFO['tc']['cookie']}")
    
    @commands.command(name="mstq")
    @is_authenticated()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def get_match_stats(self, ctx, matchid: str, masterserver: str='ac'):
        async with aiohttp.ClientSession() as session:
            match = await request(session, {'f': 'get_match_stats', 'match_id[]': matchid}, masterserver=masterserver, cookie=True)
            print(match)
            # await ctx.send(match)

    @commands.command(aliases=['lu', 'lup', 'lkp', 'lkup'])
    @is_senior()
    @is_authenticated()
    async def lookup(self, ctx, player: str, masterserver: str='ac', upgrades: str='False'):
        """lookup <nickname or account ID> <masterserver> [-u|--upgrades]"""

        if player.isdigit():
            result = await id2nick(player, masterserver=masterserver)
            if result is not None and not isinstance(result, dict): # Till id2nick returns nick
                player = result.decode().lower()
            else:
                return await ctx.send('Account does not exist.')
        else:
            player = player.lower()

        def to_bool(upgrades):
            return upgrades.lower() in ('true', '1', 'yes', '-u', '--upgrades')

        upgrades = to_bool(upgrades)

        async with aiohttp.ClientSession() as session:
            query = {'f' : 'show_stats', 'nickname' : player, 'table' : 'ranked'}
            data = await request(session, query, masterserver=masterserver, cookie=True)

            try:
                account_id = data[b'account_id'].decode()
            except:
                return await ctx.send('Account does not exist.')

            if upgrades:
                query_ss = {'f' : 'show_simple_stats', 'nickname' : player}
                data_ss = await request(session, query_ss, masterserver=masterserver)

                query['table'] = 'mastery'
                data_mu = await request(session, query, masterserver=masterserver, cookie=True)

                selected_upgrades = ', '.join([v.decode() for v in data_mu[b'selected_upgrades'].values() if isinstance(v, bytes)])
                other_upgrades = ', '.join([v.decode() for v in data[b'my_upgrades'].values() if isinstance(v, bytes)])

            if masterserver == 'ac':
                # async with session.get(f'https://hon-avatar.now.sh/{account_id}') as resp:
                #     account_icon_url = await resp.text()
                #     print(account_icon_url)
                account_icon_url = 'https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png'
            else:
                account_icon_url = 'https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png'

        # print(data)
        # print(data_ss)

        client = await translate_masterserver(masterserver, short=False)

        try:
            nickname = data[b'nickname'].decode().split(']')[1]
        except:
            nickname = data[b'nickname'].decode()
        
        try:
            clan_name = data[b'name'].decode()
        except:
            clan_name = 'None'

        if clan_name != 'None':
            clan_tag = data[b'nickname'].decode().split(']')[0]+']'
        else:
            clan_tag = 'None'
        
        try:
            clan_rank = data[b'rank'].decode()
        except:
            clan_rank = 'None'
        
        if clan_rank != 'None' and clan_name == 'None': # Ah yes, the ghost clan.
            clan_name = u'\u2063'
            clan_tag = '[]'
            embed_nickname = f'{clan_tag}{nickname}'
        elif clan_name != 'None':
            embed_nickname = f'{clan_tag}{nickname}'
        else:
            embed_nickname = nickname

        try:
            last_activity = data[b'last_activity'].decode()
        except:
            last_activity = 'None'

        try:
            account_type = config.HON_TYPE_MAP[data[b'account_type'].decode()]
        except:
            account_type = 'Unknown'

        try:
            standing = config.HON_STANDING_MAP[data[b'standing'].decode()]
        except:
            standing = 'Unknown'

        embed = discord.Embed(title=client, type="rich", description="Account Information", color=0xff6600, timestamp=ctx.message.created_at)
        embed.set_author(name=embed_nickname, url=f"https://www.heroesofnewerth.com/playerstats/ranked/{nickname}", icon_url=account_icon_url)

        embed.add_field(name="Nickname", value=nickname, inline=True)
        embed.add_field(name="Account ID", value=account_id, inline=True)
        embed.add_field(name="Super ID", value=data[b'super_id'].decode(), inline=True)

        embed.add_field(name="Created", value=data[b'create_date'].decode(), inline=True)
        embed.add_field(name="Last Activity", value=last_activity, inline=True)

        embed.add_field(name="Account Type", value=account_type, inline=True)
        embed.add_field(name="Standing", value=standing, inline=True)

        embed.add_field(name="Clan Tag", value=clan_tag, inline=True)
        embed.add_field(name="Clan Name", value=clan_name, inline=True)
        embed.add_field(name="Clan Rank", value=clan_rank, inline=True)

        embed.add_field(name="Level", value=data[b'level'].decode(), inline=True)
        embed.add_field(name="Level Experience", value=data[b'level_exp'], inline=True)

        if upgrades:
            embed.add_field(name="Avatars", value=data_ss[b'avatar_num'], inline=True)
            embed.add_field(name="Selected", value=selected_upgrades, inline=True)
            embed.add_field(name="Other", value=other_upgrades, inline=True)

        embed.set_footer(text="Requested by {0} ({1}#{2}). React with 🆗 to delete this message.".format(ctx.message.author.display_name, ctx.message.author.name, ctx.message.author.discriminator), icon_url="https://i.imgur.com/Ou1k4lD.png")
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")

        message = await ctx.send(embed=embed)
        await message.add_reaction('🆗')
        try:
            await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=120.0)
            await message.delete()
        except asyncio.TimeoutError:
            await message.delete()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def id2nick(self, ctx, account_id: str, masterserver: str='ac'):
        client = await translate_masterserver(masterserver)
        result = await id2nick(account_id, masterserver=masterserver)
        await ctx.send(f'Client: {client}\nID: {account_id}\nNickname: **{result.decode() if result is not None and not isinstance(result, dict) else f"N/A {result}"}**') # This
    
    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def nick2id(self, ctx, nickname: str, masterserver: str='ac'):
        client = await translate_masterserver(masterserver)
        result = await nick2id(nickname, masterserver=masterserver)
        await ctx.send(f"Client: {client}\nNickname: {result['nickname']}\nID: **{result['account_id']}**")
    
    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def snot(self, ctx): # Not yet
        async with aiohttp.ClientSession() as session:
            # await administration.send_notification(session)
            return


def setup(bot):
    bot.add_cog(Masterserver(bot))
    bot.loop.create_task(authenticate_and_update_info('ac'))
    bot.loop.create_task(authenticate_and_update_info('rc'))
    bot.loop.create_task(authenticate_and_update_info('tc'))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)
