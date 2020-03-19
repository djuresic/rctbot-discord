import binascii
import six
from hashlib import md5, sha256

import discord
from discord.ext import commands

import aiohttp

import utils.phpserialize as phpserialize
import srp

import config
from extensions.checks import is_tester, in_whitelist
# import extensions.administration as administration


async def translate_masterserver(masterserver, short=True):
    translation = {
        'ac': {
            'client': 'Heroes of Newerth',
            'short': 'Retail'
        },
        'rc': {
            'client': 'Heroes of Newerth Release Candidate',
            'short': 'RCT'
        },
        'tc': {
            'client': 'Heroes of Newerth Private Test',
            'short': 'SBT'
        }
    }
    if short:
        name = translation[masterserver]['short']
    else:
        name = translation[masterserver]['client']
    return name


async def initial_authentication():
    data = await authenticate('ac', config.HON_USERNAME, config.HON_PASSWORD)
    rc_data = await authenticate('rc', config.HON_RC_USERNAME, config.HON_RC_PASSWORD)
    tc_data = await authenticate('tc', config.HON_TC_USERNAME, config.HON_TC_PASSWORD)

    config.HON_NAEU_COOKIE = data[b'cookie'].decode()
    print("ac cookie set")
    config.HON_NAEU_RC_COOKIE = rc_data[b'cookie'].decode()
    print("rc cookie set")
    config.HON_NAEU_TC_COOKIE = tc_data[b'cookie'].decode()
    print("tc cookie set")


async def request(session, query, masterserver='ac', path=None, cookie=False, deserialize=True): # default to RC masterserver instead
    # print(query)
    clients = {
        'ac': {
            'hostname': config.HON_NAEU_MASTERSERVER,
            'version': config.HON_UA_VERSION,
            'cookie': config.HON_NAEU_COOKIE
        },
        'rc': {
            'hostname': config.HON_NAEU_RC_MASTERSERVER,
            'version': config.HON_UA_RC_VERSION,
            'cookie': config.HON_NAEU_RC_COOKIE
        },
        'tc': {
            'hostname': config.HON_NAEU_TC_MASTERSERVER,
            'version': config.HON_UA_TC_VERSION,
            'cookie': config.HON_NAEU_TC_COOKIE
        }
    }

    if path is None:
        path = 'client_requester.php'

    if cookie:
        query['cookie'] = clients[masterserver]['cookie']

    hostname = clients[masterserver]['hostname']
    version = clients[masterserver]['version']
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
    user = srp.User(six.b(login), None, hash_alg=srp.SHA256, ng_type=srp.NG_CUSTOM, n_hex=six.b(config.HON_S2_N), g_hex=six.b(config.HON_S2_G))
    _, A = user.start_authentication()
    query['A'] = binascii.hexlify(A).decode()
    result = await request(session, query, masterserver=masterserver)
    if b'B' not in result: return result
    s = binascii.unhexlify(result[b'salt'])
    B = binascii.unhexlify(result[b'B'])
    salt2 = result[b'salt2']
    user.password = six.b(sha256(six.b(md5(six.b(md5(password.encode()).hexdigest()) + salt2 + six.b(config.HON_SRP_SS)).hexdigest()) + six.b(config.HON_SRP_SL)).hexdigest())
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


    @commands.command(name="honstats")
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def show_simple_stats(self, ctx, nickname=None): # Rewrite
        """show_simple_stats ac"""

        ac_client_requester = 'http://' + config.HON_NAEU_MASTERSERVER + '/client_requester.php'

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

    @commands.command(name="rchonstats")
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def show_simple_stats_rc(self, ctx, nickname=None): # Rewrite
        """show_simple_stats rc"""

        rc_client_requester = 'http://' + config.HON_NAEU_RC_MASTERSERVER + '/client_requester.php'

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

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def readc(self, ctx):
        await ctx.send(f'ac: {config.HON_NAEU_COOKIE}; rc: {config.HON_NAEU_RC_COOKIE}; tc: {config.HON_NAEU_TC_COOKIE}')

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def forcesrp(self, ctx):
        data = await authenticate('ac', config.HON_USERNAME, config.HON_PASSWORD)
        rc_data = await authenticate('rc', config.HON_RC_USERNAME, config.HON_RC_PASSWORD)
        tc_data = await authenticate('tc', config.HON_TC_USERNAME, config.HON_TC_PASSWORD)
        config.HON_NAEU_COOKIE = data[b'cookie'].decode()
        config.HON_NAEU_RC_COOKIE = rc_data[b'cookie'].decode()
        config.HON_NAEU_TC_COOKIE = tc_data[b'cookie'].decode()
        # ip = data[b'ip'].decode()
        # account_id = data[b'account_id'].decode()
        # nickname = data[b'nickname'].decode()
        # chat_url = data[b'chat_url'].decode()
        # chat_port = data[b'chat_port'].decode()
        # auth_hash = data[b'auth_hash'].decode()
        await ctx.send(f'ac: {config.HON_NAEU_COOKIE}; rc: {config.HON_NAEU_RC_COOKIE}; tc: {config.HON_NAEU_TC_COOKIE}')
        # await ctx.send(f"{ip}, {cookie}, {account_id}, {nickname}, {chat_url}, {chat_port}, {auth_hash}")
    
    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def mstq(self, ctx, matchid: str, masterserver: str='ac'):
        async with aiohttp.ClientSession() as session:
            match = await request(session, {'f': 'get_match_stats', 'match_id[]': matchid}, masterserver=masterserver, cookie=True)
            print(match)
            # await ctx.send(match)
    
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
    bot.loop.create_task(initial_authentication())
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)
