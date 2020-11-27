import aiohttp
import discord
from discord.ext import commands

from rctbot.core import checks
from rctbot.core.rct import TesterManager
from rctbot.hon.acp2 import ACPClient
from rctbot.hon.masterserver import Client

# testers add <nickname>
# testers reinstate <nickname>
# testers remove <nickname>
# testers create <nickname>
# testers access <nickname>
# testers access grant <nickname>
# testers access deny <nickname>


class RCTUserAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["tester", "t", "useradmin", "ua"])
    @checks.is_senior()
    async def testers(self, ctx):
        pass

    @testers.command(name="add", aliases=["+"])
    async def _testers_add(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.add(nickname)).discord_message)

    @testers.command(name="reinstate")
    async def _testers_reinstate(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.reinstate(nickname)).discord_message)

    @testers.command(name="remove", aliases=["-"])
    async def _testers_remove(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.remove(nickname)).discord_message)

    @testers.command(name="link_discord", aliases=["linkdiscord", "link"])
    @commands.is_owner()
    async def _testers_link_discord(self, ctx, member: discord.Member):
        manager = TesterManager()
        await ctx.send((await manager.link_discord(member)).discord_message)

    @testers.command(name="create", aliases=["ca"])
    async def _testers_create(self, ctx, nickname: str, masterserver: str = "rc"):
        nickname = nickname.replace("\\", "")
        async with aiohttp.ClientSession() as session:
            game = Client(masterserver="ac", session=session)
            nickname = (await game.nick2id(nickname))["nickname"]
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            account_id, nickname, password = await acp.create_account(nickname)
            nickname = discord.utils.escape_markdown(nickname)
            await ctx.send(f"Created **{nickname}** ({account_id}). Use: **{password}**")

    @testers.group(aliases=["a"], invoke_without_command=True)
    async def access(self, ctx, nickname: str, masterserver: str = "rc"):
        nickname = nickname.replace("\\", "")
        translation = {"WTC": "SBT", "WRC": "RCT"}
        async with ACPClient(ctx.author, masterserver=masterserver) as acp:
            if account_id := await acp.nickname_to_aid(nickname):
                current_access = await acp.user_test_access(account_id)
        nickname = discord.utils.escape_markdown(nickname)
        current_access = translation[current_access] if current_access in translation else current_access
        await ctx.send(f"Current access permissions for **{nickname}**: {current_access}")

    @access.command(name="view", aliases=["check", "v", "c", "/"])
    async def _testers_access_view(self, ctx, nickname: str, masterserver: str = "rc"):
        nickname = nickname.replace("\\", "")
        translation = {"WTC": "SBT", "WRC": "RCT"}
        async with ACPClient(ctx.author, masterserver=masterserver) as acp:
            if account_id := await acp.nickname_to_aid(nickname):
                current_access = await acp.user_test_access(account_id)
        nickname = discord.utils.escape_markdown(nickname)
        current_access = translation[current_access] if current_access in translation else current_access
        await ctx.send(f"Current access permissions for **{nickname}**: {current_access}")

    @access.command(name="grant", aliases=["give", "g", "+"])
    async def _testers_access_grant(self, ctx, nickname: str, masterserver: str = "rc"):
        nickname = nickname.replace("\\", "")
        required_clicks = {"None": 2, "WTC": 1, "WRC": 0, "Both": 0}
        clicks_done = 0
        async with ACPClient(ctx.author, masterserver=masterserver) as acp:
            if account_id := await acp.nickname_to_aid(nickname):
                current_access = await acp.user_test_access(account_id)
                clicks = required_clicks[current_access]
                for _ in range(clicks):
                    if await acp.toggle_test_access(account_id):
                        clicks_done += 1
        nickname = discord.utils.escape_markdown(nickname)
        if clicks_done == clicks and clicks == 0:
            await ctx.send(f"**{nickname}** already has RCT access.")
        elif clicks_done == clicks:
            await ctx.send(f"Granted **{nickname}** RCT access.")
        else:
            await ctx.send(f"Could not grant **{nickname}** RCT access!")

    @access.command(name="deny", aliases=["remove", "d", "r", "-"])
    async def _testers_access_deny(self, ctx, nickname: str, masterserver: str = "rc"):
        nickname = nickname.replace("\\", "")
        required_clicks = {"None": 0, "WTC": 0, "WRC": 2, "Both": 2}
        clicks_done = 0
        async with ACPClient(ctx.author, masterserver=masterserver) as acp:
            if account_id := await acp.nickname_to_aid(nickname):
                current_access = await acp.user_test_access(account_id)
                clicks = required_clicks[current_access]
                for _ in range(clicks):
                    if await acp.toggle_test_access(account_id):
                        clicks_done += 1
        nickname = discord.utils.escape_markdown(nickname)
        if clicks_done == clicks and clicks == 0:
            await ctx.send(f"**{nickname}** already does not have RCT access.")
        elif clicks_done == clicks:
            await ctx.send(f"Denied **{nickname}** RCT access.")
        else:
            await ctx.send(f"Could not deny **{nickname}** RCT access!")
