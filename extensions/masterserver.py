from hashlib import md5, sha256 # for srp later

import discord
from discord.ext import commands

import aiohttp

import phpserialize

import config

from extensions.checks import is_tester, in_whitelist


class Masterserver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_tester()
    async def version(self, ctx):
        """Check all RC client versions."""

        async with ctx.message.channel.typing():

            rc_patcher = f'http://{config.HON_NAEU_RC_MASTERSERVER}/patcher/patcher.php'

            wrc_query = {'version' : '0.0.0.0', 'os' : f'wrc-{config.HON_NAEU_RC_OS_PART}', 'arch' : 'i686'}
            lrc_query = {'version' : '0.0.0.0', 'os' : f'lrc-{config.HON_NAEU_RC_OS_PART}', 'arch' : 'x86-biarch'}
            mrc_query = {'version' : '0.0.0.0', 'os' : f'mrc-{config.HON_NAEU_RC_OS_PART}', 'arch' : 'universal'}
            
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


    @commands.command(name="honstats")
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def show_simple_stats(self, ctx, nickname=None):
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
    async def show_simple_stats_rc(self, ctx, nickname=None):
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
    async def srp(self, ctx):
        """secure remote password authentication""" #TO DO: remove py 2.7 syntax, fix srp, secrets to conf, f in async, aiohttp, global for cookie
        try:
            import srp
        except:
            pass
        from urllib.request import Request
        from urllib.request import urlopen
        from urllib.parse import urlencode, quote
        #...

def setup(bot):
    bot.add_cog(Masterserver(bot))
    print('Masterserver is being loaded.')
