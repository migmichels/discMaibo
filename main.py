from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, CommandNotFound, MissingRequiredArgument
from hangman import Hangman
from os import getenv
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return

    if isinstance(error, MissingRequiredArgument):
        return

    if isinstance(error, CommandInvokeError):
        return

    raise error

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

@bot.command(brief = 'Starts a new game')
async def hangman(ctx, arg):
    game = Hangman(arg)
    channel = ctx.channel

    if len(ctx.message.content.split()) == 3:
        ctxAux = ctx
        channel = bot.get_channel(int(ctxAux.message.content.split()[2]))

    await channel.send(' '.join(str(x) for x in game.correctLetters).replace('_', '\\_'))
    await channel.send('Difficult: ' + game.difficult + '%')

    while not(game.win or game.lost):
        message = await bot.wait_for('message', check=lambda message: message.channel == channel)
        
        if (message.content.startswith('!g')):
            game.attempt(message.content.split()[1])
            already = ', '.join(str(x) for x in game.already)

            await channel.send(f'Alredy used: {already}\n{game.boyStr}        ' + ' '.join(str(x) for x in game.correctLetters).replace('_', '\\_'))
        elif (message.content.startswith('!t') and message.content.split()[1].upper() == game.word):
            game.win = True

    if game.win:
        await channel.send('Congratulations, You won!')
    else:
        await channel.send('You lost :(')

    await channel.send('Game over!')


bot.run(getenv('TOKEN'))