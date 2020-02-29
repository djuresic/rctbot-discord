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
            new_content = old_content[:-41] + "⚠ This report has was deemed valid by {0}, but a smilar or related one had already been submitted.".format(self.senior_tester_name)
            await is_this_valid.edit(content=new_content)

        else:
            old_content = is_this_valid.content
            new_content = old_content[:-41] + "✅ This report has been approved by {0}.".format(self.senior_tester_name)
            await is_this_valid.edit(content=new_content)

        return #aaaaaaalllllriiiight

def setup(bot):
    bot.add_cog(BugReports(bot))
    print('Bug Reports loaded.')
