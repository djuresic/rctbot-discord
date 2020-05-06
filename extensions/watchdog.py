import asyncio
import string  # This
import codecs  # This
from io import BytesIO  # This
from zipfile import ZipFile
from datetime import datetime, timezone

import aiohttp
from discord.ext import tasks, commands
from discord.utils import escape_markdown

import config
from extensions.checks import is_senior  # core.checks
import extensions.spreadsheet as spreadsheet  # core.spreadsheet Soon:tm:

# Porting pr, watchdog and zucclist to prod bot...
# pr, now process, uses discord.ext.tasks to achieve the same goal as before.

# This whole module needs a massive cleanup. (var names too pls <3)


class Watchdog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counter = 0
        self.log_channel = config.DISCORD_WATCHDOG_CHANNEL_ID
        self.word_list = config.HON_WORD_LIST
        # self.process.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.process.cancel()  # pylint: disable=no-member

    # Something is fucky here...
    # The entire bot becomes unresponsive even though the loop runs just fine.
    @tasks.loop(minutes=60.0)
    async def process(self):
        client = await spreadsheet.set_client()
        rct_ss = await client.open("RCT Spreadsheet")
        watchdog_ws = await rct_ss.worksheet("Watchdog")
        watchlist_ws = await rct_ss.worksheet("Watchlist")

        isDone = await watchdog_ws.col_values(1)
        MatchID = await watchdog_ws.col_values(3)
        Links = await watchdog_ws.col_values(12)
        watchlist = await watchlist_ws.col_values(1)

        channel = self.bot.get_channel(self.log_channel)

        watchlist_lower = [x.lower() for x in watchlist]
        MatchIDs = []
        S3Links = []
        count = -1
        await channel.send("Watchdog triggered.")
        for i in MatchID:
            count = count + 1
            if i != "" and str(isDone[count]) == "1":
                MatchIDs.append(i)
                S3Links.append(Links[count])
        # counter=len(MatchIDs)
        # for i in range(0,counter,1):
        # S3Links.append(Links[i])
        # for i in S3Links:
        # if i=='':
        # MatchIDs.remove(MatchIDs[S3Links.index(i)])
        # for i in S3Links:
        # if i=='':
        # S3Links.remove(i)
        # print(len(S3Links))
        # print(len(MatchIDs))
        # print(S3Links)
        # print(MatchIDs)
        S3Zip = []
        for i in S3Links:
            # if i!='':
            S3Zip.append(i.replace("honreplay", "zip"))
        # print(len(S3Zip))
        for i in range(0, len(S3Zip), 1):
            j = i
            # replay=requests.get(S3Zip[i], stream=True)
            # print("passed_request")
            saveFile = []
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(S3Zip[i]) as resp:
                        resp = await resp.read()

                        # This needs a better solution
                        def extract_match_log(response, match_id):
                            zip_file = ZipFile(BytesIO(response))
                            return zip_file.read(f"m{match_id}.log")

                        loop = asyncio.get_running_loop()

                        # matchLog = ZipFile(BytesIO(resp))
                        # await asyncio.sleep(3)
                        # matchLog = matchLog.read("m{0}.log".format(MatchIDs[i]))
                        matchLog = await loop.run_in_executor(
                            None, extract_match_log, resp, MatchIDs[i]
                        )
                        await asyncio.sleep(1)
            except:
                await channel.send(
                    "Could not fetch logs for **{0}**.".format(MatchIDs[i])
                )
                # await bot.say("Could not process {0}.".format(MatchIDs[i]))
                continue
            # matchLog=zipfile.ZipFile(io.StringIO(replay)).read("m{0}.log".format(MatchIDs[i]))
            # print("passed_zip")
            matchLogUni = await loop.run_in_executor(
                None, codecs.decode, matchLog, "utf8", "ignore"
            )  # Is this even necessary?
            tempStr = ""
            matchLogUni = matchLogUni.strip()
            for i in range(0, len(matchLogUni), 1):
                if matchLogUni[i] == "\n":
                    saveFile.append(
                        "".join(x for x in tempStr if x in string.printable)
                    )
                    tempStr = ""
                else:
                    tempStr += matchLogUni[i]

            replayDate = saveFile[0].split(":", 1)[1].split(" ")[0].strip('"')
            replayTime = saveFile[0].split(":", 1)[1].split(" ")[1]
            replayTime = replayTime.split(":", 1)[1].strip('"')
            players = []
            playersNb = []
            c = 0
            for i in range(0, len(saveFile), 1):
                if c == 10:
                    break
                if saveFile[i].startswith("PLAYER_CONNECT"):
                    c += 1
                    player = (
                        saveFile[i]
                        .split(":", 1)[1]
                        .split(":", 1)[1]
                        .split(" ", 1)[0]
                        .strip('"')
                    )
                    playerNb = saveFile[i].split(":", 1)[1].split(" ", 1)[0]
                    players.append(player)
                    playersNb.append(playerNb)
            RCTPlayers = []
            RCTPlayersNb = []
            for i in range(0, len(players), 1):
                current_player_name = players[i]
                if "]" in current_player_name:
                    current_player_name_stripped = current_player_name.split("]")[1]
                else:
                    current_player_name_stripped = current_player_name
                if (
                    current_player_name.startswith("[RCC]")
                    or current_player_name.startswith("[RCT]")
                    or current_player_name_stripped.lower() in watchlist_lower
                ):
                    RCTPlayers.append(players[i])
                    RCTPlayersNb.append(playersNb[i])
            # print(RCTPlayers)
            # print(RCTPlayersNb)
            RCTChat = []
            for i in range(0, len(saveFile), 1):
                if saveFile[i].startswith("PLAYER_CHAT"):
                    # pNb=saveFile[i].split(':',1)[1].split(' ',1)[0]
                    pNb = saveFile[i].split("player:")[1][:1]
                    if pNb in RCTPlayersNb:
                        index = RCTPlayersNb.index(pNb)
                        playerOfMsg = RCTPlayers[index]
                        # message=saveFile[i].split(':',1)[1].split(' ',1)[1].split(' ',1)[1].split(':',1)[1].strip('"')
                        message = saveFile[i].split('msg:"')[1]
                        Orgmessage = message.strip('"\r')
                        # chatType=saveFile[i].split(':',1)[1].split(':',1)[1]
                        chatType = saveFile[i].split('target:"')[1][:4]
                        # chatType=chatType.split(' ',1)[0].strip('"')
                        # chatType=chatType.strip('"')
                        message = Orgmessage.lower()
                        if chatType == "team":
                            chat = "T"
                        else:
                            chat = "A"
                        bw_detected = False
                        for bad_word in self.word_list:
                            if bad_word in message:
                                bw_detected = True
                                break
                        if bw_detected:
                            RCTChat.append(
                                "[{2}]{0}: {1} {3}".format(
                                    playerOfMsg, Orgmessage, chat, "⚠️"
                                )
                            )
                        else:
                            RCTChat.append(
                                "[{2}]{0}: {1}".format(playerOfMsg, Orgmessage, chat)
                            )

            await channel.send(
                "Match ID: **{2}**\nDate: **{0}**\nTime: **{1}**\n\n".format(
                    replayDate, replayTime[:8], MatchIDs[j]
                ),
            )
            # await bot.say("Match ID: **{2}*\nDate: **{0}**\nTime: **{1}**\n---------------------------------------------------------".format(replayDate,replayTime[:8],MatchIDs[j]))
            # await bot.say('-------------------------------------------------------------------------')
            for i in RCTChat:
                # await bot.say(i)
                try:
                    await channel.send(escape_markdown(i))
                except:
                    await channel.send("Uh oh, something went wrong. :(")
                await asyncio.sleep(1)
        count = -1
        for i in MatchID:
            count = count + 1
            if i != "" and str(isDone[count]) == "1":
                await watchdog_ws.update_cell(count + 1, 1, 2)
        await channel.send("Processed **{0}** Match IDs.".format(len(MatchIDs)))

    @process.before_loop
    async def before_process(self):
        await self.bot.wait_until_ready()
        print("Watchdog task started.")

    @process.after_loop
    async def after_process(self):
        print("Watchdog task stopped.")

    @commands.group(hidden=True)
    @is_senior()
    async def watchdog(self, ctx):
        pass

    @watchdog.command(name="counter")
    async def _counter(self, ctx):
        await ctx.send(f"Times successful: {self.counter}")


def setup(bot):
    bot.add_cog(Watchdog(bot))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
