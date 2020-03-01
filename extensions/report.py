import asyncio
from time import time
from hashlib import md5

import discord
from discord.ext import commands

import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

import aiohttp

import config
from extensions.checks import is_tester


class BugReports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.OPEN_REPORTS = []
        self.senior_tester_name = ''
    
    #TO DO: universal login function
    @commands.command()
    @commands.has_any_role('Manage Roles', 'Overlord', 'Frostburn Staff', 'Senior Tester', 'Senior Tester Candidate') # TO DO: alternative
    async def create(self, ctx, patch:str=None, link:str=None):
        if patch is None or link is None:
            await ctx.send('The correct format is `.create <version> <patch notes link or Discord>`')
            return
        await ctx.send('Please wait.')

        index = 'https://forums.heroesofnewerth.com/index.php'
        login_url = 'https://forums.heroesofnewerth.com/login.php'
        login_params = {'do' : 'login'}
        login_data = {'cookieuser':'1',
                    'do':'login',
                    's':'',
                    'securitytoken':'guest',
                    'vb_login_md5password':config.HON_FORUM_USER_MD5_PASSWORD,
                    'vb_login_md5password_utf':config.HON_FORUM_USER_MD5_PASSWORD,
                    'vb_login_password':'',
                    'vb_login_password_hint':'Password',
                    'vb_login_username':config.HON_FORUM_USER}

        async with aiohttp.ClientSession() as session:

            async with session.post(login_url, params=login_params, data=login_data) as resp:
                await resp.text()
            
            async with session.get(index) as resp:
                index_get = await resp.text()
                securitytoken = index_get.split('SECURITYTOKEN = "')[1][:51]

            poststarttime = str(int(time()))

            patch_search = "-" + patch.replace(".", "-")

            message_mechanics_general = f"[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{patch} Bugs - Mechanics[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Mechanics bugs only (and general bugs that don't belong in the other bug threads but aren't art or sound).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{link}\"]{link}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind."
            message_tooltips = f"[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{patch} Bugs - Tooltips[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Tooltip bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{link}\"]{link}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind."
            
            #to correct
            posthash_mechanics_general = md5(message_mechanics_general.encode('utf-8')).hexdigest()
            posthash_tooltips = md5(message_tooltips.encode('utf-8')).hexdigest()

            thread_mechanics_general = f"{patch} Bugs - Mechanics"
            thread_tooltips = f"{patch} Bugs - Tooltips"

            thread_mechanics_general_search = f"{patch_search}-Bugs-Mechanics\" id=\"thread_title_"
            thread_tooltips_search = f"{patch_search}-Bugs-Tooltips\" id=\"thread_title_"

            newthread_mechanics_general = {'do':'postthread',
                    'f':config.HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                    'iconid':'0',
                    'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
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
                    'f':config.HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                    'iconid':'0',
                    'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
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

            if config.HON_FORUM_CREATE_ALL_THREADS:
                message_ui = f"[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{patch} - Bugs (UI)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Interface bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{link}\"]{link}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind."
                message_sound = f"[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{patch} - Bugs (Sound)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Sound bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{link}\"]{link}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind."
                message_art = f"[CENTER][FONT=verdana][SIZE=3][B][COLOR=#ff6600]{patch} - Bugs (Art)[/COLOR][/B][/SIZE]\n[COLOR=#a9a9a9]Art bugs only (and other bugs that could possibly fit in this thread).[/COLOR][/FONT][/CENTER]\n\n\nPatch notes can be found here: [URL=\"{link}\"]{link}[/URL]\n\n\n[COLOR=#ff6600][B]General Rules[/B][/COLOR]\n- Always include version number and build date in your report in the format specified below. To check the build date and version number, simply open your console  (Ctrl+F8) and then type \"version\" without the quotation marks and press  Enter.\n- Remember to include which alt avatar a bug occurs on if you are testing a hero.\n- Only use Imgur ([URL]https://imgur.com/[/URL]) to host and link images in your reports. It's a standard for us & the URLs are short enough so Staff can handle mass reports easier. Guide on how to step up your screenshots to the next level can be found [URL=\"https://forums.heroesofnewerth.com/showthread.php?589119-Guide-How-to-screenshots\"]here[/URL].\n- Only report RCT-specific bugs that occur on this client. Do not report retail bugs in the RCT Bugs subforum. Why this is so can be seen [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16498264&viewfull=1#post16498264\"]here[/URL].\n- If you're posting crash logs, you have to include a brief description  of why you think you crashed or what you were doing at the time you crashed.\n- The only language used in your reports should be English.\n- Do not report HoN Store related sound bugs with regards to new avatars.\n\n\n[COLOR=#ff6600][B]Format[/B][/COLOR]\nYou are expected to make your reports in the format below. Reports made by RCTBot naturally follow this format.\n[QUOTE][FONT=Tahoma][I]Version: 0.xx.xxx\nBuild date: Day Month Year\n\n<Description of bug>[/I][/FONT][/QUOTE]\n[COLOR=#0099FF]Example:[/COLOR]\n[QUOTE][FONT=Tahoma][I]Version: 0.27.231.1\nBuild date: 2 April 2018\n\n[/I][/FONT]This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.[/QUOTE]\n\n\nIf you are reporting a bug directly, paste only the plain text image URL  when linking images in your posts. Only use quotes, not spoilers.  Reasons for this are listed [URL=\"https://forums.heroesofnewerth.com/showthread.php?585781-RCT-Bugs-Posting-Rules&p=16511525&viewfull=1#post16511525\"]here[/URL]. To report a bug via Discord, use the [COLOR=#00cc99].report[/COLOR]  command and follow the instructions while having all the above rules in mind."

                #to correct
                posthash_ui = md5(message_ui.encode('utf-8')).hexdigest()
                posthash_sound = md5(message_sound.encode('utf-8')).hexdigest()
                posthash_art = md5(message_art.encode('utf-8')).hexdigest()

                thread_ui = f"{patch} Bugs - UI"
                thread_sound = f"{patch} Bugs - Sound"
                thread_art = f"{patch} Bugs - Art"

                thread_ui_search = f"{patch_search}-Bugs-UI\" id=\"thread_title_"
                thread_sound_search = f"{patch_search}-Bugs-Sound\" id=\"thread_title_"
                thread_art_search = f"{patch_search}-Bugs-Art\" id=\"thread_title_"


                newthread_ui = {'do':'postthread',
                        'f':config.HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                        'iconid':'0',
                        'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
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
                        'f':config.HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                        'iconid':'0',
                        'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
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
                        'f':config.HON_FORUM_RCT_BUGS_SUBFORUM_ID,
                        'iconid':'0',
                        'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
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
                newthread_params = {'do' : 'postthread', 'f' : config.HON_FORUM_RCT_BUGS_SUBFORUM_ID}
                async with session.post(newthread_url, params=newthread_params, data=newthread_data) as resp:
                    await resp.text()
                return

            await post_thread(newthread_mechanics_general)
            await post_thread(newthread_tooltips)
    
            if config.HON_FORUM_CREATE_ALL_THREADS:
                await post_thread(newthread_ui)
                await post_thread(newthread_art)
                await post_thread(newthread_sound)

            subforum_url = f'https://forums.heroesofnewerth.com/forumdisplay.php?{config.HON_FORUM_RCT_BUGS_SUBFORUM_ID}'
            
            await ctx.send(f'Threads have been created and can be viewed here: {subforum_url}')
            await asyncio.sleep(1)

            await ctx.send('Updating settings...')

            async with session.get(subforum_url) as resp:
                content = await resp.text()
                thread_mechanics_general_id = content.split(thread_mechanics_general_search)[1][:6]
                thread_tooltips_id = content.split(thread_tooltips_search)[1][:6]

                if config.HON_FORUM_CREATE_ALL_THREADS:
                    thread_ui_id = content.split(thread_ui_search)[1][:6]
                    thread_sound_id = content.split(thread_sound_search)[1][:6]
                    thread_art_id = content.split(thread_art_search)[1][:6]

            try:
                def get_creds():
                    return ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES)

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

                if config.HON_FORUM_CREATE_ALL_THREADS:
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
    @commands.command()
    @is_tester()
    async def report(self, ctx):
        report_author = ctx.message.author
        bug_reports_channel = self.bot.get_channel(config.DISCORD_BUGS_CHANNEL_ID)

        if report_author not in bug_reports_channel.members or report_author.id not in config.DISCORD_WHITELIST_IDS: #TO DO: this has to go
            return

        if report_author in self.OPEN_REPORTS:
            already_pending_content = "You already have a bug report pending, please complete that one first."
            already_pending_message = await report_author.send("{.mention} ".format(report_author) + already_pending_content)
            await asyncio.sleep(8)
            await already_pending_message.edit(content=already_pending_content)
            return

        self.OPEN_REPORTS.append(report_author)

        report_author_discord_id = str(report_author.id)
        for x in config.LIST_OF_LISTS:
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
        if config.HON_FORUM_CREATE_ALL_THREADS:
            await bc_message.add_reaction(bc_message, '🎨')
            await asyncio.sleep(0.1)
            await bc_message.add_reaction(bc_message, '🔊')
            await asyncio.sleep(0.1)
            await bc_message.add_reaction(bc_message, '💻')
            await asyncio.sleep(0.1)
        await bc_message.add_reaction('❌')

        bc_embed.add_field(name="Mechanic/General", value='⚙')
        bc_embed.add_field(name="Tooltips", value='📋')
        if config.HON_FORUM_CREATE_ALL_THREADS:
            bc_embed.add_field(name="Art", value='🎨')
            bc_embed.add_field(name="Sound", value='🔊')
            bc_embed.add_field(name="User Interface", value='💻')
        bc_embed.add_field(name="Cancel", value='❌')
        await bc_message.edit(content=bc_content, embed=bc_embed)

        emojis_dict = {
                    '⚙': {'category': 'Mechanics/General', 'threadid': config.SETTINGS[7]},
                    '📋': {'category': 'Tooltips', 'threadid': config.SETTINGS[11]},
                    '🎨': {'category': 'Art', 'threadid': config.SETTINGS[8]},
                    '🔊': {'category': 'Sound', 'threadid': config.SETTINGS[9]},
                    '💻': {'category': 'User Interface', 'threadid': config.SETTINGS[10]}
                    }

        #reaction_symbols = [reaction.emoji for reaction in bc_message.reactions if reaction.emoji in emojis_dict.keys()] #no clue why bc_message.reactions returns an empty list every time
        if config.HON_FORUM_CREATE_ALL_THREADS:
            reaction_symbols = ['📋','⚙','🎨','🔊','💻','❌']
        else:
            reaction_symbols = ['📋','⚙','❌']

        reaction, user = await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in reaction_symbols and reaction.message.id == bc_message.id)
        await bc_message.edit(content=None, embed=bc_embed)
        ##await self.bot.delete_message(ctx.message)

        if reaction.emoji == '❌':
            cancel_report_content = "Process cancelled. Use `.report` to start over."
            cancel_report_message = await report_author.send("{.mention} ".format(report_author) + cancel_report_content)
            self.OPEN_REPORTS.remove(report_author)
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
        
        reaction, user = await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in ['✅','❌'] and reaction.message.id == proceed_prompt_message.id)
        await proceed_prompt_message.edit(content=proceed_prompt_content)
        
        if reaction.emoji == '❌':
            proceed_prompt_no_content = "Process cancelled. Use `.report` to start over."
            proceed_prompt_no_message = await report_author.send("{.mention} ".format(report_author) + proceed_prompt_no_content)
            self.OPEN_REPORTS.remove(report_author)
            await asyncio.sleep(8)
            await proceed_prompt_no_message.edit(content=proceed_prompt_no_content)
            return

        ask_for_version_content = "Please enter the **version** of the RCT client. Format: `<0.xx.xxx>` e.g. `0.27.231.1`"
        ask_for_version_message = await report_author.send("{.mention} ".format(report_author) + ask_for_version_content)
        rc_version_message = await self.bot.wait_for('message', check=lambda m: m.author == report_author)
        await ask_for_version_message.edit(content=ask_for_version_content)

        ask_for_build_date_content = "Please enter the **build date** of the RCT client. Format: `<Day Month Year>` e.g. `2 April 2018`"
        ask_for_build_date_message = await report_author.send("{.mention} ".format(report_author) + ask_for_build_date_content)
        build_date_message = await self.bot.wait_for('message', check=lambda m: m.author == report_author)
        await ask_for_build_date_message.edit(content=ask_for_build_date_content)

        ask_for_screenshots_content = "Please enter the **number of screenshots** your have. Format : `<integer>` e.g.  `2`\nIn case you don't have any screenshots or want to include them in the description instead, enter `0` to proceed."
        ask_for_screenshots_message = await report_author.send("{.mention} ".format(report_author) + ask_for_screenshots_content)
        number_of_screenshots_message = await self.bot.wait_for('message', check=lambda m: m.author == report_author)
        await ask_for_screenshots_message.edit(content=ask_for_screenshots_content)

        screenshots_list = []
        try:
            number_of_screenshots = int(number_of_screenshots_message.content)
            if number_of_screenshots > config.HON_FORUM_SCREENSHOT_LIMIT:
                number_of_screenshots = config.HON_FORUM_SCREENSHOT_LIMIT
                too_many_screenshots_content = "That might be too many screenshots. Your entry has been changed to `{}`. If the screenshots excluded were necessary, please add them to the description.".format(number_of_screenshots)
                too_many_screenshots_message = await report_author.send("{.mention} ".format(report_author) + too_many_screenshots_content)
                await asyncio.sleep(8)
                await too_many_screenshots_message.edit(content=too_many_screenshots_content)

            for i in range(1, number_of_screenshots+1, 1):
                ask_for_screenshot_link_content = "Please enter the **screenshot link** number {} of the bug. e.g. `https://i.imgur.com/D0Yn9JC.png`".format(i)
                ask_for_screenshot_link_message = await report_author.send("{.mention} ".format(report_author) + ask_for_screenshot_link_content)
                screenshot_link_message = await self.bot.wait_for('message', check=lambda m: m.author == report_author)
                screenshots_list.append(screenshot_link_message.content)
                await ask_for_screenshot_link_message.edit(content=ask_for_screenshot_link_content)

        except:
            screenshots_not_integer_content = "Your input was not an integer. If this is a mistake, please add your screenshots to the bug description."
            screenshots_not_integer_message = await report_author.send("{.mention} ".format(report_author) + screenshots_not_integer_content)
            await asyncio.sleep(8)
            await screenshots_not_integer_message.edit(content=screenshots_not_integer_content)

        ask_for_description_content = "Please enter the **description** of the bug, up to 2000 characters. Use `Shift + Enter` for new lines, `Enter` to submit. e.g. `This avatar's skill does not play a sound, does not work at all (results in nothing after being cast) and has no visuals.`"
        ask_for_description_message = await report_author.send("{.mention} ".format(report_author) + ask_for_description_content)
        bug_description_message = await self.bot.wait_for('message', check=lambda m: m.author == report_author)
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

        reaction, user = await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == report_author and reaction.emoji in ['✅','❌'] and reaction.message.id == final_report_prompt_message.id)
        await final_report_prompt_message.edit(content=final_report_prompt_content)

        if reaction.emoji == '❌':
            final_report_discarded_content = "Your report has been discarded."
            final_report_discarded_message = await report_author.send("{.mention} ".format(report_author) + final_report_discarded_content)
            self.OPEN_REPORTS.remove(report_author)
            await asyncio.sleep(8)
            await final_report_discarded_message.edit(content=final_report_discarded_content)
            return

        index = 'https://forums.heroesofnewerth.com/index.php'
        login_url = 'https://forums.heroesofnewerth.com/login.php'
        login_params = {'do' : 'login'}
        login_data = {'cookieuser':'1',
                    'do':'login',
                    's':'',
                    'securitytoken':'guest',
                    'vb_login_md5password':config.HON_FORUM_USER_MD5_PASSWORD,
                    'vb_login_md5password_utf':config.HON_FORUM_USER_MD5_PASSWORD,
                    'vb_login_password':'',
                    'vb_login_password_hint':'Password',
                    'vb_login_username':config.HON_FORUM_USER}
        
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
            return ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES)

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
        self.OPEN_REPORTS.remove(report_author)
        await is_this_valid.add_reaction('✅')
        await is_this_valid.add_reaction('❌')
        await is_this_valid.add_reaction('⚠')

        await asyncio.sleep(0.5)

        def check(reaction, user):
            if reaction.message.id != is_this_valid.id or reaction.emoji not in ['✅','❌','⚠']: 
                return False
            guild = bug_reports_channel.guild
            check_user_roles = user.roles
            frostburn = discord.utils.get(guild.roles, name="Senior Tester")
            senior = discord.utils.get(guild.roles, name="Frostburn Staff")
            if senior in check_user_roles or frostburn in check_user_roles:
                senior_tester_id = str(user.id)
                for x in config.LIST_OF_LISTS:
                    if x[32] == senior_tester_id:
                        senior_tester_verified_name = x[1]
                        break
                self.senior_tester_name = '{0} ({1.name}#{1.discriminator})'.format(senior_tester_verified_name, user)
            return senior in check_user_roles or frostburn in check_user_roles

        #validate=await self.bot.wait_for_reaction(['✅','❌','⚠'],message=is_this_valid,check=check)
        reaction, user = await self.bot.wait_for('reaction_add', check=check)

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
            new_content = old_content[:-41] + "❌ This report has been rejected by {0}.".format(self.senior_tester_name)
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
            new_content = old_content[:-41] + "⚠ This report was deemed valid by {0}, but a smilar or related one had already been submitted.".format(self.senior_tester_name)
            await is_this_valid.edit(content=new_content)

        else:
            old_content = is_this_valid.content
            new_content = old_content[:-41] + "✅ This report has been approved by {0}.".format(self.senior_tester_name)
            await is_this_valid.edit(content=new_content)

        return #aaaaaaalllllriiiight

def setup(bot):
    bot.add_cog(BugReports(bot))
    print('Bug Reports loaded.')
