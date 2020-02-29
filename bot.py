#!/usr/bin/env python

"""
RCTBot

Copyright (c) 2020 Danijel Jurešić

Licensed under the MIT License.
"""

import os
import asyncio
import platform #sys
import random
import json
import timeit
import collections
from time import time, gmtime, strftime
from datetime import datetime
from hashlib import md5

import discord
from discord.ext import commands

import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

import aiohttp
# import youtube_dl TO DO: music port

import phpserialize

from extensions.checks import * # well, let's leave this here for now till I figure out which ones are actually needed

# note to myself: ctx.author: shorthand for Message.author, also applies to: guild, channel

# TO DO:
# oh yeah it's f strings time!
# remove unnecessary "global"s, port: on_member_join, announce_testing, keep_alive, games, distribute, trivia, mvp, joined, mute, table, ttt, hangman, whois, pr
# detailed platform data
# remove utf-8 from encode/decode, it's the default in py 3
# option for remote config and empty config file creation

import config # What have I done...

#dynamic
FETCH_SHEET_PASS = 0

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

BOT_STARTUP_EXTENSIONS = []
BOT_DISABLED_EXTENSIONS = []

with os.scandir('extensions') as it:
    for entry in it:
        if entry.name.endswith('.py') and entry.is_file():
            extension_name = entry.name.strip('.py')
            if extension_name not in BOT_DISABLED_EXTENSIONS:
                BOT_STARTUP_EXTENSIONS.append(f'extensions.{extension_name}')


bot = commands.Bot(command_prefix=['!', '.'], description=winter_solstice)

if __name__ == "__main__":
    for extension in BOT_STARTUP_EXTENSIONS:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))


#-------------------- Forums & Bug Reports --------------------
#TO DO: universal login function
@bot.command()
@commands.has_any_role('Manage Roles', 'Overlord', 'Frostburn Staff', 'Senior Tester', 'Senior Tester Candidate')
async def create(ctx, patch:str=None, link:str=None):
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

        subforum_url = 'https://forums.heroesofnewerth.com/forumdisplay.php?{0}'.format(config.HON_FORUM_RCT_BUGS_SUBFORUM_ID)
        
        await ctx.send('Threads have been created and can be viewed here: {0}'.format(subforum_url))
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


#TO DO: this needs to be prettier
@bot.command()
@commands.has_any_role('Manage Roles', 'Overlord', 'Frostburn Staff', 'Senior Tester', 'Senior Tester Candidate')
async def hero(ctx):

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
                for x in config.PLAYER_SLASH_HERO:
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
                for x in config.PLAYER_SLASH_HERO:
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
                for x in config.PLAYER_SLASH_HERO:
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
    author = ctx.message.author
    log_channel = bot.get_channel(config.DISCORD_NOTES_CHANNEL_ID)

    token_generator = f'https://{config.HON_ALT_DOMAIN}/site/create-access-token'
    cat_query = {'discordId' : author.id, 'password' : config.HON_CAT_PASSWORD}
    
    async with aiohttp.ClientSession() as session:

        async with session.get(token_generator, params=cat_query) as resp:
            token = await resp.text()

    notes_url = f'https://{config.HON_ALT_DOMAIN}/{token}'
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


#-------------------- Events, Error Handling & Debugging --------------------
@bot.command()
@in_whitelist(config.DISCORD_WHITELIST_IDS)
async def dev_permission_test(ctx):
    await ctx.send("{.mention} You do have permission.".format(ctx.message.author))


@bot.event
async def on_ready():
    print('{0} ({0.id}) reporting for duty from {1}! All shall respect the law that is my {2}!'.format(bot.user, platform.platform(), config.CONFIG_FILE))
    watching = discord.Activity(name="Heroes of Newerth", type=discord.ActivityType.watching)
    #streaming = discord.Streaming(platform="Twitch", name="Heroes of Newerth", game="Heroes of Newerth", url="https://www.twitch.tv/", twitch_name="")
    await bot.change_presence(activity=watching, status=discord.Status.dnd, afk=False)
    print('------')

@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)

    if message.guild is None and ctx.valid: #TO DO: with guild_only and dm_allowed
        #print([f.__name__ for f in ctx.command.checks])
        if ctx.command.name not in config.DISCORD_DM_COMMANDS:
            print("{0.name}#{0.discriminator} ({0.id}) tried to invoke {1} in Direct Message: {2}".format(message.author, ctx.command, message.content))
            return

    # if ctx.valid:
    #     if ctx.command in config.DISCORD_DM_COMMANDS and message.author.id not in config.DISCORD_WHITELIST_IDS:
    #         await message.author.send("You do not have permission.")
    #     else:
    #         await bot.process_commands(message)
    # else:
    #     pass

    if message.channel.id == config.DISCORD_ANNOUNCEMENTS_CHANNEL_ID:
        if config.DISCORD_FORUMS_ROLE_ID in message.raw_role_mentions:

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
                
                content = message.content.split(config.DISCORD_FORUMS_ROLE_ID)[1].strip(' ')
                announcement = "{0}\n\n\nMade by: [COLOR=#00cc99]{1.display_name}[/COLOR] ({1.name}#{1.discriminator})".format(content, message.author)
                poststarttime = str(int(time()))
                posthash = md5(announcement.encode('utf-8')).hexdigest() #"This is fine."

                new_reply_url = 'https://forums.heroesofnewerth.com/newreply.php'
                post_params = {'do' : 'postreply', 't' : config.HON_FORUM_ANNOUNCEMENTS_THREAD_ID}
                post_data = {'ajax':'1',
                            'ajax_lastpost':'',
                            'do':'postreply',
                            'fromquickreply':'1',
                            'loggedinuser':config.HON_FORUM_USER_ACCOUNT_ID,
                            'securitytoken':securitytoken,
                            'message':announcement,
                            'message_backup':announcement,
                            'p':'who cares',
                            'parseurl':'1',
                            'post_as':config.HON_FORUM_USER_ACCOUNT_ID,
                            'posthash':posthash,
                            'poststarttime':poststarttime,
                            's':'',
                            'securitytoken':securitytoken,
                            'signature':'1',
                            'specifiedpost':'0',
                            't':config.HON_FORUM_ANNOUNCEMENTS_THREAD_ID,
                            'wysiwyg':'0'}
                
                async with session.post(new_reply_url, params=post_params, data=post_data) as resp:
                    await resp.text()

    await bot.process_commands(message)


#-------------------- Background Tasks --------------------
async def fetch_sheet():
    await bot.wait_until_ready()
    global FETCH_SHEET_PASS

    def get_creds():
        return ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES)
    
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

        #update dynamic
        config.LIST_OF_LISTS = await rewards_worksheet.get_all_values()
        config.LIST_OF_LISTS_TRIVIA = await trivia_worksheet.get_all_values()
        config.SETTINGS = await settings_worksheet.col_values(2)
        config.PLAYER_SLASH_HERO = await games_worksheet.col_values(13)

        config.DATABASE_READY = True
        
        count_pass += 1
        FETCH_SHEET_PASS = count_pass
        if count_pass <= 2:
            print ('fetch_sheet pass {0}'.format(FETCH_SHEET_PASS))

        await asyncio.sleep(60)


bot.remove_command('help')

bot.loop.create_task(fetch_sheet())

bot.run(config.DISCORD_TOKEN)