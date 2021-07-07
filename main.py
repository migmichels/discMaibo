from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, CommandNotFound, MissingRequiredArgument
from hangman import Hangman
from os import getenv
from dotenv import load_dotenv
import random, boto3, requests

sns = boto3.client("sns",
                   region_name="us-east-1", 
                   aws_access_key_id=getenv('KEY_ID'),
                   aws_secret_access_key=getenv('ACCESS_KEY'))

s3 = boto3.resource('s3')
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


@bot.command(brief = 'Rolls a d20. good luck, traveler!')
async def d20(ctx):
    print(random.randint(0, 20))
    await ctx.send(str(random.randint(0, 20)))

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
        elif (message.content.startswith('!k') and message.content.split()[1].upper() == game.word):
            game.win = True

    if game.win:
        await channel.send('Congratulations, You won!')
    else:
        await channel.send('You lost :(')

    await channel.send('Game over!')

@bot.command(brief = 'Sends a message to the specified channel')
async def snd(ctx, arg):
    await bot.get_channel(arg).send(int(ctx.message.content.split('$')[2]))

@bot.command(brief = 'Uploads the attached file to the bucket maibo on s3')
async def up(ctx):
    fileObj = ctx.message.attachments[0]
    with open('files/file', 'wb') as file:
        file.write(requests.get(fileObj).content)
        s3.meta.client.upload_file('files/file', 'maibo', fileObj.filename)
    open("files/file", "w").close()

bot.run(getenv('TOKEN'))