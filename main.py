from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, CommandNotFound, MissingRequiredArgument
from hangman import Hangman
from os import getenv
from dotenv import load_dotenv
import random, boto3, requests

load_dotenv()
bot = commands.Bot(command_prefix='!')

sns = boto3.client('sns',
                region_name='us-east-1', 
                aws_access_key_id=getenv('KEY_ID'),
                aws_secret_access_key=getenv('ACCESS_KEY'))
s3 = boto3.client('s3',
                region_name='us-east-1', 
                aws_access_key_id=getenv('KEY_ID'),
                aws_secret_access_key=getenv('ACCESS_KEY'))
rekognition = boto3.client('rekognition',
                region_name='us-east-1', 
                aws_access_key_id=getenv('KEY_ID'),
                aws_secret_access_key=getenv('ACCESS_KEY'))
db = boto3.resource('dynamodb',
                region_name='us-east-1', 
                aws_access_key_id=getenv('KEY_ID'),
                aws_secret_access_key=getenv('ACCESS_KEY'))

extBlock = ['bat', 'pem', 'cmd', 'env', 'dll']
extImgs = ['ras', 'xwd', 'bmp', 'jfif', 'jpe', 'jpg', 'jpeg', 'xpm', 'ief', 'pbm', 'tif', 'gif', 'ppm', 'xbm', 'tiff', 'rgb', 'pgm', 'png', 'pnm']
swearword = ['CARALHO', 'PUTA', ' CU ', 'BUCETA', 'PARIU', 'FUDER', 'FDP', 'NIGGA', 'PORRA', 'PAPIBAQUIGRAFO', 'OTORRINOLARINGOLOGISTA', 'HEIL HITLER', 'HEIL NAZI']

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

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user or ctx.content.startswith('!'):
        await bot.process_commands(ctx)
        return

    if ctx.attachments != []:
        fileObj = ctx.attachments[0]

        if fileObj.filename.split('.')[-1] in extImgs:
            
            resp = rekognition.detect_moderation_labels(Image={'Bytes' : requests.get(fileObj).content})
            for label in resp['ModerationLabels']:
                if label['Confidence'] <= 65:
                    await ctx.delete()
                    fileObj.filename = 'SPOILER_' + fileObj.filename
                    await ctx.channel.send(file=await fileObj.to_file())
                    return

    contains = False
    i=0
    while i<len(swearword) and not(contains):
        contains = swearword[i] in ctx.content.upper()
        i+=1

    
    table = db.Table('BlackList')
    if contains:
        i-= 1

        """sns.publish(TopicArn="arn:aws:sns:us-east-1:038893253008:swearWord", 
            Message=f"{ctx.author} mandou uma mensagem no canal {ctx.channel} contendo a palavra \'{swearword[i]}\'",
            Subject="Palavrão no canal")"""

        try:
            table.update_item(
                Key = {
                    'userTag' : str(ctx.author)
                },
                UpdateExpression = f'SET words = list_append(words, :s )',
                ExpressionAttributeValues = {':s' : [swearword[i]]}
            )
        except:
            table.put_item(
                Item = {
                    'userTag' : str(ctx.author),
                    'words' : [str(swearword[i])]
                })


@bot.command()
async def rm(ctx, arg, arg1):
    print(arg, arg1)
    channel = await bot.get_channel(int(arg))
    msg = await channel.fetch_message(int(arg1))
    await msg.delete()

@bot.command(brief = 'Rolls a d20. good luck, traveler!')
async def d20(ctx):
    await ctx.send(str(random.randint(0, 20)))

@bot.command(brief = 'Starts a new hangman game')
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

        elif (message.content.startswith('!stop')):
            await channel.send('Game over!')
            return

    if game.win:
        await channel.send('Congratulations, You won!')
    else:
        await channel.send('You lost :(')

    await channel.send('Game over!')

@bot.command(brief = 'Sends a message to the specified channel')
async def snd(ctx, arg):
    await bot.get_channel(int(arg)).send(ctx.message.content.split('$')[1])

@bot.command(brief = 'Uploads the attached file to the bucket maibo on s3')
async def up(ctx):
    fileObj = ctx.message.attachments[0]
    if fileObj.filename.split('.')[-1].lower() in extBlock:
        await ctx.channel.send('The extension\'s file is not allowed')
        return

    with open('.temp', 'wb') as file:
        file.write(requests.get(fileObj).content)
        s3.upload_file('files/file', getenv('BUCKET'), fileObj.filename)
    open("files/file", "w").close()

@bot.command(brief = 'Publish a message to the topic')
async def msg(ctx):
    sns.publish(TopicArn=getenv('ARN_TOPIC'), 
            Message=f"{ctx.message.author.name} from Discord:{ctx.message.content.split('!msg')[1]}",
            Subject="msg from Discord, by:" + ctx.message.author.name)

@bot.command()
async def bl(ctx):
    table = db.Table('BlackList')
    response = table.scan()
    data = response['Items']

    """while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
        print(response)"""
    
    bList = 'Black List:\n'
    i = 0
    while i < len(data):
        bList+= '\n' + data[i]['userTag'] + '\n'
        ii = 0
        while ii < len(data[i]['words']):
            bList+= '   ' + data[i]['words'][ii] + '\n'
            ii+= 1
        i+= 1

    await ctx.channel.send(bList)

bot.run(getenv('TOKEN'))