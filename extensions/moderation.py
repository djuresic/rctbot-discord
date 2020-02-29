import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['clear', 'delete'])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, number:int, offender:discord.Member=None):
        channel = ctx.message.channel
        if number < 2 or number > 99:
            message = await ctx.send('Invalid number of messages.')
            await message.add_reaction('🆗')
            await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
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
            await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
            await message.delete()

        else:
            #messages = await channel.history(limit=number).flatten()
            deleted = await channel.purge(limit=number+1) #accounting for command invoking message
            message = await ctx.send('Deleted the last {} messages.'.format(len(deleted)))
            await message.add_reaction('🆗')
            await self.bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.message.author and reaction.emoji == '🆗' and reaction.message.id == message.id, timeout=30.0)
            await message.delete()

def setup(bot):
    bot.add_cog(Moderation(bot))
    print('Moderation loaded.')
