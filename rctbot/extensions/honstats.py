import aiohttp
import discord
from discord.ext import commands

import rctbot.config

from rctbot.core.logging import record_usage  # NOTE: discord.py 1.4
from rctbot.core.driver import CLIENT

from rctbot.hon.masterserver import Client
from rctbot.hon.utils import get_name_color, get_avatar, hero_name


class HoNStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]

    # TODO: Match stats command.

    @commands.command(aliases=["rstats", "retail"])
    @commands.guild_only()
    @commands.after_invoke(record_usage)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(10, per=commands.BucketType.guild, wait=False)
    async def stats(self, ctx, nickname: str):
        "Retail player statistics."
        nickname = nickname.replace("\\", "")
        async with aiohttp.ClientSession() as session:
            client = Client("ac", session=session)
            simple = await client.show_simple_stats(nickname)
            campaign = await client.show_stats(nickname, "campaign")
            # print(campaign)
        if b"selected_upgrades" not in campaign:
            return await ctx.send(
                f"{ctx.author.mention} Nickname {discord.utils.escape_markdown(nickname)} does not exist!",
                delete_after=10.0,
            )
        embed = discord.Embed(
            title=client.client_name,
            type="rich",
            description="Player Statistics",
            url=f"http://www.heroesofnewerth.com/playerstats/ranked/{nickname}",
            color=(await get_name_color(simple)),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="Level", value=campaign[b"level"].decode(), inline=True,
        )
        embed.add_field(
            name="Account Created", value=campaign[b"create_date"].decode(), inline=True,
        )
        embed.add_field(
            name="Last Activity",
            value=campaign[b"last_activity"].decode()
            if b"last_activity" in campaign and campaign[b"last_activity"] is not None
            else "\u2063",
            inline=True,
        )
        embed.add_field(
            name="Standing", value=rctbot.config.HON_STANDING_MAP[campaign[b"standing"].decode()], inline=True,
        )
        embed.add_field(
            name="Clan Name", value=campaign[b"name"].decode() if b"name" in campaign else "\u2063", inline=True,
        )
        embed.add_field(
            name="Clan Rank", value=campaign[b"rank"].decode() if b"rank" in campaign else "\u2063", inline=True,
        )
        if b"cam_games_played" in campaign:
            con_total = int(campaign[b"cam_games_played"].decode())
        else:
            con_total = 0
        if b"cam_wins" in campaign:
            con_wins = int(campaign[b"cam_wins"].decode())
        else:
            con_wins = 0
        if con_total > 0:
            con_win_rate = round((con_wins / con_total) * 100)
        else:
            con_win_rate = 0
        embed.add_field(
            name="Total Games",
            value=f'{campaign[b"total_games_played"]} ({campaign[b"total_discos"]} Disconnects)',
            inline=True,
        )
        embed.add_field(
            name="CoN Games",
            value=f'{con_total} ({campaign[b"cam_discos"].decode() if b"cam_discos" in campaign else 0} Disconnects)',
            inline=True,
        )
        embed.add_field(
            name="Mid Wars Games",
            value=f'{campaign[b"mid_games_played"].decode()} ({campaign[b"mid_discos"].decode()} Disconnects)',
            inline=True,
        )

        con_rank = int(campaign[b"current_level"]) if b"current_level" in campaign else 0
        con_rank_highest = int(campaign[b"highest_level_current"]) if b"highest_level_current" in campaign else 0
        con_rank_percent = round(campaign[b"level_percent"], 2) if b"level_percent" in campaign else 0
        rank_data = {
            20: {"name": "Immortal", "image": "https://i.imgur.com/em0NhHz.png"},
            19: {"name": "Legendary I", "image": "https://i.imgur.com/OttPTfr.png"},
            18: {"name": "Legendary II", "image": "https://i.imgur.com/0M6ht3c.png"},
            17: {"name": "Diamond I", "image": "https://i.imgur.com/j3tcf3d.png"},
            16: {"name": "Diamond II", "image": "https://i.imgur.com/gZGYIVa.png"},
            15: {"name": "Diamond III", "image": "https://i.imgur.com/lt7m4zE.png"},
            14: {"name": "Gold I", "image": "https://i.imgur.com/aMVvZ40.png"},
            13: {"name": "Gold II", "image": "https://i.imgur.com/p3M9lFF.png"},
            12: {"name": "Gold III", "image": "https://i.imgur.com/rfb0SAn.png"},
            11: {"name": "Gold IV", "image": "https://i.imgur.com/5l7a5Vl.png"},
            10: {"name": "Silver I", "image": "https://i.imgur.com/slkd8EJ.png"},
            9: {"name": "Silver II", "image": "https://i.imgur.com/rcDllgP.png"},
            8: {"name": "Silver III", "image": "https://i.imgur.com/nBTQSM3.png"},
            7: {"name": "Silver IV", "image": "https://i.imgur.com/cx6YPn7.png"},
            6: {"name": "Silver V", "image": "https://i.imgur.com/gGjhDIM.png"},
            5: {"name": "Bronze I", "image": "https://i.imgur.com/3vTVsdC.png"},
            4: {"name": "Bronze II", "image": "https://i.imgur.com/lH6LCnT.png"},
            3: {"name": "Bronze III", "image": "https://i.imgur.com/Q4fHFT1.png"},
            2: {"name": "Bronze IV", "image": "https://i.imgur.com/OfOolSK.png"},
            1: {"name": "Bronze V", "image": "https://i.imgur.com/XW9tUlV.png"},
            0: {"name": "Unranked", "image": "https://i.imgur.com/h0RcR5h.png"},
        }
        mmr_list = [
            1000,
            1250,
            1275,
            1300,
            1330,
            1360,
            1400,
            1435,
            1470,
            1505,
            1540,
            1575,
            1610,
            1645,
            1685,
            1725,
            1765,
            1805,
            1850,
            1900,
            1950,
            2500,
        ]
        mmr = mmr_list[con_rank] + (mmr_list[con_rank + 1] - mmr_list[con_rank]) * (con_rank_percent / 100)
        # embed.add_field(name="MMR", value=f"{mmr}", inline=True)
        embed.add_field(
            name="Rank", value=rank_data[con_rank]["name"], inline=True,
        )
        embed.set_thumbnail(url=rank_data[con_rank]["image"])
        embed.add_field(
            name="Rank Progress", value=f"{con_rank_percent}%", inline=True,
        )
        embed.add_field(
            name="Highest Rank", value=rank_data[con_rank_highest]["name"], inline=True,
        )

        embed.add_field(
            name="Wins", value=f"{con_wins}", inline=True,
        )

        cam_losses = campaign[b"cam_losses"].decode() if b"cam_losses" in campaign else 0
        cam_concedes = campaign[b"cam_concedes"].decode() if b"cam_concedes" in campaign else 0

        embed.add_field(
            name="Losses", value=f"{cam_losses} ({cam_concedes} Conceded)", inline=True,
        )
        embed.add_field(
            name="Win Rate", value=f"{con_win_rate}%", inline=True,
        )

        kills = int(campaign[b"cam_herokills"].decode()) if b"cam_herokills" in campaign else 0
        deaths = int(campaign[b"cam_deaths"].decode()) if b"cam_deaths" in campaign else 0
        assists = int(campaign[b"cam_heroassists"].decode()) if b"cam_heroassists" in campaign else 0
        embed.add_field(
            name="Kills", value=kills, inline=True,
        )
        embed.add_field(
            name="Deaths", value=deaths, inline=True,
        )
        embed.add_field(
            name="Assists", value=assists, inline=True,
        )

        cam_gold = int(campaign[b"cam_gold"].decode()) if b"cam_gold" in campaign else 0
        cam_secs = int(campaign[b"cam_secs"].decode()) if b"cam_secs" in campaign else 0
        average_gpm = round((cam_gold / (cam_secs / 60)), 2) if cam_secs > 0 else 0

        lifetime = (
            f"K:D Ratio: {round(kills/deaths, 2) if deaths > 0 else kills}:{1 if deaths > 0 else 0}"
            f"\nK+A:D Ratio: {round((kills+assists)/deaths, 2) if deaths > 0 else kills + assists}:{1 if deaths > 0 else 0}"
            f'\nWards Placed: {campaign[b"cam_wards"].decode() if b"cam_wards" in campaign else 0}'
            f'\nBuildings Razed: {campaign[b"cam_razed"].decode() if b"cam_razed" in campaign else 0}'
            f'\nConsumables Used: {campaign[b"cam_consumables"].decode() if b"cam_consumables" in campaign else 0}'
            f'\nBuybacks: {campaign[b"cam_buybacks"].decode() if b"cam_buybacks" in campaign else 0}'
            f'\nConcede Votes: {campaign[b"cam_concedevotes"].decode() if b"cam_concedevotes" in campaign else 0}'
        )

        average = (
            f'Game Length: {"{:02d}:{:02d}".format(*divmod(round(campaign[b"avgGameLength"]), 60)) if b"avgGameLength" in campaign else "00:00"}'
            f'\nK/D/A: {campaign[b"k_d_a"].decode() if b"k_d_a" in campaign else 0}'
            f'\nCreep Kills: {campaign[b"avgCreepKills"] if b"avgCreepKills" in campaign else 0}'
            f'\nCreep Denies: {campaign[b"avgDenies"] if b"avgDenies" in campaign else 0}'
            f'\nNeutral Kills: {campaign[b"avgNeutralKills"] if b"avgNeutralKills" in campaign else 0}'
            f"\nGPM: {average_gpm}"
            f'\nXPM: {campaign[b"avgXP_min"] if b"avgXP_min" in campaign else 0}'
            f'\nAPM: {campaign[b"avgActions_min"] if b"avgActions_min" in campaign else 0}'
            f'\nWards Placed: {campaign[b"avgWardsUsed"] if b"avgWardsUsed" in campaign else 0}'
        )

        streaks = (
            f'Serial Killer (3): {campaign[b"cam_ks3"].decode() if b"cam_ks3" in campaign else 0}'
            f'\nUltimate Warrior (4): {campaign[b"cam_ks4"].decode() if b"cam_ks4" in campaign else 0}'
            f'\nLegendary (5): {campaign[b"cam_ks5"].decode() if b"cam_ks5" in campaign else 0}'
            f'\nOnslaught (6): {campaign[b"cam_ks6"].decode() if b"cam_ks6" in campaign else 0}'
            f'\nSavage Sick (7): {campaign[b"cam_ks7"].decode() if b"cam_ks7" in campaign else 0}'
            f'\nDominating (8): {campaign[b"cam_ks8"].decode() if b"cam_ks8" in campaign else 0}'
            f'\nChampion (9): {campaign[b"cam_ks9"].decode() if b"cam_ks9" in campaign else 0}'
            f'\nBloodbath (10): {campaign[b"cam_ks10"].decode() if b"cam_ks10" in campaign else 0}'
            f'\nImmortal (15): {campaign[b"cam_ks15"].decode() if b"cam_ks15" in campaign else 0}'
        )

        multikills = (
            f'Double Tap: {campaign[b"cam_doublekill"].decode() if b"cam_doublekill" in campaign else 0}'
            f'\nHat-Trick: {campaign[b"cam_triplekill"].decode() if b"cam_triplekill" in campaign else 0}'
            f'\nQuad Kill: {campaign[b"cam_quadkill"].decode() if b"cam_quadkill" in campaign else 0}'
            f'\nAnnihilation: {campaign[b"cam_annihilation"].decode() if b"cam_annihilation" in campaign else 0}'
        )

        misc = (
            f'Bloodlust: {campaign[b"cam_bloodlust"].decode() if b"cam_bloodlust" in campaign else 0}'
            f'\nSmackdown: {campaign[b"cam_smackdown"].decode() if b"cam_smackdown" in campaign else 0}'
            f'\nHumiliation: {campaign[b"cam_humiliation"].decode() if b"cam_humiliation" in campaign else 0}'
            f'\nNemesis: {campaign[b"cam_nemesis"].decode() if b"cam_nemesis" in campaign else 0}'
            f'\nRetribution: {campaign[b"cam_retribution"].decode() if b"cam_retribution" in campaign else 0}'
        )

        heroes = []
        for number in range(1, 6):
            hero = campaign[f"favHero{number}_2".encode()].decode()
            if hero != "":
                hero = hero_name(campaign[f"favHero{number}_2".encode()].decode())
                heroes.append(f'{hero} ({campaign[f"favHero{number}Time".encode()]}%)')

        embed.add_field(
            name="Most Played Heroes", value="\n".join(heroes) if len(heroes) > 0 else "\u2063", inline=True,
        )
        embed.add_field(
            name="Lifetime Statistics", value=lifetime, inline=True,
        )
        embed.add_field(
            name="Average Statistics", value=average, inline=True,
        )
        embed.add_field(
            name="Streaks", value=streaks, inline=True,
        )
        embed.add_field(
            name="Multi-Kills", value=multikills, inline=True,
        )
        embed.add_field(
            name="Miscellaneous", value=misc, inline=True,
        )
        embed.set_author(
            name=simple[b"nickname"].decode(),
            url=f"https://forums.heroesofnewerth.com/member.php?{simple[b'account_id'].decode()}",
            icon_url=(await get_avatar(simple[b"account_id"].decode())),
        )
        embed.set_footer(
            text="Displays detailed statistics for Champions of Newerth (Forests of Caldavar Campaign) only.",
            icon_url="https://i.imgur.com/q8KmQtw.png",
        )
        tester = await self.testers.find_one({"account_id": int(simple[b"account_id"].decode())})
        if tester and tester["signature"]["purchased"]:
            if tester["signature"]["url"] != "":
                embed.set_image(url=tester["signature"]["url"])
            else:
                embed.add_field(
                    name="You own a Discord Embedded Signature!",
                    value="Set it up using the `.signature` command to make Merrick even more jealous of you.",
                    inline=False,
                )
        await ctx.send(embed=embed)

    @stats.error
    async def stats_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"{ctx.author.mention} {error}", delete_after=8.0)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author.mention} You must specify a nickname.", delete_after=8.0)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"{ctx.author.mention} You are on cooldown! Try again in {round(error.retry_after, 2)} seconds.",
                delete_after=8.0,
            )
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                (
                    f"{ctx.author.mention} Too many people are using this command!"
                    f" It can only be used 10 times per Discord server concurrently."
                ),
                delete_after=8.0,
            )
        # raise error


def setup(bot):
    bot.add_cog(HoNStats(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(HoNStats(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
