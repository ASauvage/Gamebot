import asyncio
import os
import discord
import socket
import qrcode
import mysql.connector
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import *
from qrcode.image.styles.colormasks import *
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv(dotenv_path="config")
token = os.getenv('TOKEN')
prefix = os.getenv('PREFIX')
host_ = os.getenv('HOST')
user_ = os.getenv('DBUSER')
password_ = os.getenv('PASSWORD')
database_ = os.getenv('DATABASE')
versionnum = os.getenv('VERSIONNUM')
logchannelid = 0
tcpport = 5555


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", tcpport))

game_message = None
gamestart = False
logchannel = None
current_goal = ""
gamename = ""

emojiList = [
    873325386774233098,  # up
    873325386946207796,  # down
    873325387269165106,  # left
    873325387055243274,  # right
    873325386505797683,  # a
    873325386660970516,  # b
    873325386371579935,  # select
    873325386749083678  # start
]


class Gamebot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix, help_command=None)

    async def on_ready(self):
        global logchannel
        print("[main.py] We have logged in as {0.user}".format(self))
        await self.change_presence(status=discord.Status.online)
        logchannel = self.get_channel(logchannelid)


bot = Gamebot()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"Error: Missing Required Argument // {error}")
        await ctx.message.delete()
        print("[main.py] Error: MissingRequiredArgument")
    elif isinstance(error, commands.BadArgument):
        await ctx.channel.send(f"Error: Bad Argument // {error}")
        await ctx.message.delete()
        print("[main.py] Error: Bad Argument")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.channel.send(f"Error: Missing Permissions // {error}")
        await ctx.message.delete()
        print("[main.py] Error: Missing Permissions")
    elif isinstance(error, commands.ChannelNotReadable):
        await ctx.channel.send(f"Error: Channel Not Readable // {error}")
        await ctx.message.delete()
        print("[main.py] Error: Channel Not Readable")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.channel.send(
            f"Sorry {ctx.author.mention}, but your not allowed to use this command in private message")
        print("[main.py] Error : No Private Message")
    else:
        print(f"[main.py] Error: Unknown // {error}")


@bot.event
async def on_reaction_add(reaction, user):
    if not user == bot.user and reaction.message == game_message:
        for x in range(8):
            if bot.get_emoji(emojiList[x]) == reaction.emoji:
                global logchannel
                global current_goal

                await reaction.message.add_reaction("✅")

                mydb = mysql.connector.connect(host=host_, user=user_, password=password_, database=database_)
                mycursor = mydb.cursor()

                mycursor.execute(f"SELECT `{reaction.emoji.name}` FROM `stats` WHERE `game_name` = '{gamename}'")
                request = mycursor.fetchone()

                mycursor.execute(
                    f"UPDATE `stats` SET `{reaction.emoji.name}` = {request[0] + 1} WHERE `game_name` = '{gamename}'")
                mydb.commit()

                s.sendall(b"but_%b" % str(x).encode('UTF-8'))
                print(f"[main.py] {x} pressed")

                while True:
                    ss = s.recv(255)
                    if ss == b"done":
                        break

                file = discord.File(fp=f"screeshot/{gamename}.png", filename=f"{gamename}.png")
                embed = discord.Embed(title=f"{user} press button {reaction.emoji}",
                                      description=f"inuput n°{request[0] + 1}",
                                      color=0xcc0227)
                embed.set_footer(text=f"bot latency: {round(bot.latency * 1000)}ms.")
                embed.set_image(url=f"attachement://{gamename}.png")

                history = await logchannel.send(file=file, embed=embed)

                embed = discord.Embed(title=gamename, description=f"**__Current goal:__**\n\n{current_goal}",
                                      color=0x6C3483)
                embed.set_image(url=history.attachments[0].url)

                await game_message.edit(embed=embed)

                await reaction.message.remove_reaction("✅", bot.user)
                await reaction.message.remove_reaction(reaction, user)

                mycursor.close()
                mydb.close()
                break


@bot.command(name="init")
@commands.guild_only()
@commands.has_permissions(manage_channels=True)
async def init(ctx, Game_Name: str):
    global gamestart

    if not gamestart:
        if os.path.isfile(f"roms/{Game_Name}.gb"):
            global game_message
            global gamename
            global current_goal

            gamename = Game_Name

            await bot.change_presence(activity=discord.Game(Game_Name), status=discord.Status.do_not_disturb)
            history = await logchannel.send(content=f"{ctx.author} start the game {gamename}",
                                            file=discord.File(fp=f"files/game_pic/{gamename}.png",
                                                              filename=f"{gamename}.png"))

            embed = discord.Embed(title=gamename, description="**__Current goal:__**\n\nFinish this game",
                                  color=0x6C3483)
            embed.set_image(url=history.attachments[0].url)

            game_message = await ctx.channel.send(embed=embed)
            s.sendall(b"gamestart.%b" % Game_Name.encode('UTF-8'))

            for x in emojiList:
                print(x)
                print(bot.get_emoji(x))
                await game_message.add_reaction(bot.get_emoji(x))

            gamestart = True
            print(f"[main.py] ROM {Game_Name} loaded")
        else:
            await ctx.channel.send(f"ROM {Game_Name} is inaccessible or missing")
            print(f"[main.py] ROM {Game_Name} is inaccessible or missing")
    else:
        await ctx.channel.send("A ROM is already running")
        print(f"[main.py] A ROM is already running")
    await ctx.message.delete()


@bot.command(name="save")
async def save(ctx):
    if gamestart:
        global current_goal

        my_file = open(f"roms/saves/{gamename}.goal", "w")
        my_file.write(current_goal)
        my_file.close()

        s.sendall(b"save")
        s.recv(255)
        await ctx.channel.send(f"Save Created for {gamename}")
    else:
        await ctx.channel.send("No game curently running")
    await ctx.message.delete()


@bot.command(name="load")
async def load(ctx):
    global gamestart

    if gamestart:
        s.sendall(b"load")
        s.recv(255)
        global game_message
        global current_goal

        my_file = open(f"roms/saves/{gamename}.goal", "r")
        current_goal = my_file.read()
        my_file.close()

        history = await logchannel.history(limit=1).flatten()

        embed = discord.Embed(title=gamename, description=f"**__Current goal:__**\n\n{current_goal}",
                              color=0x6C3483)
        embed.set_image(url=history[0].attachments[0].url)

        await game_message.edit(embed=embed)
        await ctx.channel.send(f"Save loaded for {gamename}")
    else:
        await ctx.channel.send("No game curently running")
    await ctx.message.delete()


@bot.command(name="stop")
@commands.has_permissions(manage_messages=True, manage_channels=True)
async def stop(ctx):
    global gamestart

    if gamestart:
        test = await ctx.channel.send(f"Are you sure you want to stop the game currently running ({gamename}) ?")
        await test.add_reaction("👍")
        await test.add_reaction("👎")

        def check(reaction, user):
            return user == ctx.author and reaction.message.channel == ctx.channel and (
                    str(reaction.emoji) == "👍" or str(reaction.emoji) == "👎")

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            await test.delete()
        except asyncio.TimeoutError:
            await ctx.channel.send(f"{ctx.author} took too long to react.")
            await test.delete()
            return

        if str(reaction.emoji) == "👍":
            global game_message

            test = await ctx.channel.send(f"Do you want to save before stop the game ?")
            await test.add_reaction("👍")
            await test.add_reaction("👎")

            def check1(reaction, user):
                return user == ctx.author and reaction.message.channel == ctx.channel and (
                        str(reaction.emoji) == "👍" or str(reaction.emoji) == "👎")

            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check1)
                await test.delete()
            except asyncio.TimeoutError:
                await ctx.channel.send(f"{ctx.author} took too long to react.")
                await test.delete()
                return

            if str(reaction.emoji) == "👍":
                global current_goal

                my_file = open(f"roms/saves/{gamename}.goal", "w")
                my_file.write(current_goal)
                my_file.close()

                s.sendall(b"save")
                s.recv(255)

            s.sendall(b"stop")
            s.recv(255)
            await bot.change_presence(status=discord.Status.online)
            await ctx.channel.send(f"game {gamename} stopped by {ctx.author}")
            await game_message.delete()

            gamestart = False
            game_message = None
    else:
        await ctx.channel.send("No game curently running")
    await ctx.message.delete()


@bot.command(name="goal")
async def goal(ctx, *Goal):
    global gamestart

    if gamestart:
        global game_message
        global current_goal
        goalt = ""
        for x in Goal:
            goalt += x

        current_goal = goalt

        history = await logchannel.history(limit=1).flatten()

        embed = discord.Embed(title=gamename, description=f"**__Current goal:__**\n\n{current_goal}",
                              color=0x6C3483)
        embed.set_image(url=history[0].attachments[0].url)

        await game_message.edit(embed=embed)
        await ctx.channel.send(f"Current Goal changed to {current_goal}")
        print(f"[main.py] Current Goal changed to {current_goal}")
    else:
        await ctx.channel.send("No game curently running")
        print(f"[main.py] Goal: No game curently running")
    await ctx.message.delete()


@bot.command(name="gamelist")
async def gamelist(ctx):
    onlyfiles = [f for f in os.listdir("roms/") if os.path.isfile(os.path.join("roms/", f))]
    embed = discord.Embed(title=f"List of available games", color=0x221188)
    embed.set_thumbnail(url=bot.user.avatar_url)

    for x in onlyfiles:
        if x[-1] == "b":
            embed.add_field(name=x, value="-", inline=False)
    await ctx.channel.send(embed=embed)
    print("[main.py] List of game printed")
    await ctx.message.delete()


@bot.command(name="savelist")
async def savelist(ctx):
    if gamestart:
        onlyfiles = [f for f in os.listdir("roms/saves") if os.path.isfile(os.path.join("roms/saves", f))]
        if len(onlyfiles) > 0:
            embed = discord.Embed(title=f"List of available save", description=f"{gamename}", color=0x221188)
            embed.set_thumbnail(url=bot.user.avatar_url)

            for x in onlyfiles:
                embed.add_field(name=x, value='-', inline=False)
            await ctx.channel.send(embed=embed)
            print(f"[main.py] List of save printed for {gamename}")
        else:
            await ctx.channel.send(f"No save found for {gamename}")
            print(f"[main.py] No save found for {gamename}")
    else:
        await ctx.channel.send("No game curently running")
        print(f"[main.py] Savelist: No game curently running")
    await ctx.message.delete()


@bot.command(name="stats")
async def help(ctx, Game_Name: str):
    mydb = mysql.connector.connect(host=host_, user=user_, password=password_, database=database_)
    mycursor = mydb.cursor()

    mycursor.execute(
        f"SELECT `but_up`, `but_down`, `but_right`, `but_left`, `but_a`, `but_b`, `but_select`, `but_start` FROM `stats` WHERE (`game_name` = '{Game_Name}')")
    request = mycursor.fetchone()

    try:
        file = discord.File(fp=f"files/game_pic/{Game_Name}.png", filename=f"{Game_Name}.png")
        embed = discord.Embed(title=f"{Game_Name} stats", color=0x221188)

        embed.set_thumbnail(url=f"attachment://{Game_Name}.png")
        embed.add_field(name="<:but_left:867121579481759825>", value=f"{request[3]} input", inline=False)
        embed.add_field(name="<:but_up:867121579460001823>", value=f"{request[0]} input", inline=False)
        embed.add_field(name="<:but_right:867121579493687296>", value=f"{request[2]} input", inline=False)
        embed.add_field(name="<:but_down:867121579476254780>", value=f"{request[1]} input", inline=False)
        embed.add_field(name="<:but_a:867121579447418911>", value=f"{request[4]} input", inline=False)
        embed.add_field(name="<:but_b:867121579569577984>", value=f"{request[5]} input", inline=False)
        embed.add_field(name="<:but_select:867121579518984292>", value=f"{request[6]} input", inline=False)
        embed.add_field(name="<:but_start:867121579535761450>", value=f"{request[7]} input", inline=False)

        await ctx.channel.send(file=file, embed=embed)
        print(f"[main.py] Stats loaded for {Game_Name}")
    except LookupError:
        await ctx.channel.send(f"Can't find stats for a game named {Game_Name}")
        print(f"[main.py] Error load {Game_Name} stats")

    mycursor.close()
    mydb.close()
    await ctx.message.delete()


@bot.command(name="pokedex")
async def pokedex(ctx, Index):
    mydb = mysql.connector.connect(host=host_, user=user_, password=password_, database=database_)
    mycursor = mydb.cursor()

    mycursor.execute(f"SELECT * FROM `pokedex` WHERE `ID` = {Index} OR `name` = {Index}")
    request = mycursor.fetchone()

    if len(request) == 1:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(f"https://pokemondb.net/pokedex/{request[1]}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black",
                            back_color="white",
                            image_factory=StyledPilImage,
                            color_mask=SquareGradiantColorMask(back_color=(255, 255, 255),
                                                               center_color=(44, 47, 51),
                                                               edge_color=(44, 47, 51)),
                            module_drawer=SquareModuleDrawer())

        img.save("files/qrcode.png")

        file = discord.File(fp=f"files/pokedex/{request[0]}.png", filename=f"{request[0]}.png")

        embed = discord.Embed(title=request[1], description=request[4], color=0xff0000)
        embed.set_thumbnail(url=f"")
        embed.set_footer(text=f"n°{request[0]} - {request[15]}")
        embed.set_image(url=f"attachements://{request[0]}.png")
        embed.add_field(name=f"{request[2]} {request[3]}",
                        value=f"Height: {request[5]} m  |  Weight: {request[6]} kg",
                        inline=False)
        embed.add_field(name=f"Evolution: {request[7]}",
                        value=f"Evolution requirement: {request[8]}",
                        inline=False)
        embed.add_field(name="Base stats:",
                        value=f"HP: {request[9]}\nAttack: {request[10]}\nDefense: {request[11]}\nSp.Atk: {request[12]}\nSp.Def: {request[13]}\nSpeed: {request[14]}",
                        inline=False)

        await ctx.channel.send(file=file, embed=embed)
    else:
        await ctx.channel.send(f"No pokemon with index {Index}")
    await ctx.message.delete()


@bot.command(name="log")
@commands.has_permissions(administrator=True)
async def log(ctx, ChannelID: int):
    newchannel = bot.get_channel(ChannelID)
    if newchannel is None:
        await ctx.channel.send(f"No channel found for ID {ChannelID}, verify if I have access to this channel")
    else:
        global logchannel
        await newchannel.send(f"This channel has been designed to be the log's channel of {bot.user.mention}")
        logchannel = newchannel
        await ctx.channel.send(f"Log's channel is now {logchannel.name} on server {logchannel.guild}")
    await ctx.message.delete()


@bot.command(name="botprefix")
@commands.has_permissions(administrator=True)
async def botprefix(ctx, Prefix):
    global prefix

    await ctx.channel.send(f"Prefix {prefix} change to {Prefix} for {bot.user}")
    bot.command_prefix = Prefix
    prefix = Prefix


@bot.command(name="version")
async def version(ctx):
    file = open("changelog.txt")
    content = file.read()

    embed = discord.Embed(title="Game Bot Advance", description=f"V{versionnum}", color=0x221188)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.set_footer(text="By Brainless")

    embed.add_field(name="Emulation of Game Boy's game on public discord server and multiple minigames",
                    value="Developed in Python3.7",
                    inline=False)
    embed.add_field(name="Changelogs:",
                    value=content)

    await ctx.channel.send(embed=embed)
    await ctx.message.delete()


@bot.command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Game Bot Advance", description="\n\n", color=0x221188)
    embed.set_thumbnail(url=bot.user.avatar_url)

    embed.add_field(name=f"{prefix}help",
                    value=f"Show this help menu\nExample: {prefix}help",
                    inline=False)
    embed.add_field(name=f"{prefix}init Game_Name",
                    value=f"Initializes the emulator in the channel (Require manage channel permission)\nExample: {prefix}init Pokemon-Version_Rouge",
                    inline=False)
    embed.add_field(name=f"{prefix}stop",
                    value=f"Stop the emulator in the channel  (Require manage guild and manage channel permission)\nExample: {prefix}stop",
                    inline=False)
    embed.add_field(name=f"{prefix}goal Goal",
                    value=f"Change the goal sentence for the current game\nExample: {prefix}goal Win the game",
                    inline=False)
    embed.add_field(name=f"{prefix}gamelist",
                    value=f"Display all the games available\nExample: {prefix}gamelist",
                    inline=False)
    embed.add_field(name=f"{prefix}savelist",
                    value=f"Display all the save available for a game\nExample: {prefix}savelist \"Pokemon-Version_Rouge\"",
                    inline=False)
    embed.add_field(name=f"{prefix}stats Game_Name",
                    value=f"Display the stats of the named game\nExample: {prefix}stats \"Pokemon-Version_Rouge\"",
                    inline=False)
    embed.add_field(name=f"{prefix}load",
                    value=f"Load a save for the current game (use {prefix}init before)\nExample: {prefix}load",
                    inline=False)
    embed.add_field(name=f"{prefix}pokedex Index",
                    value=f"Display some information about first generation Pokemon\nExample: {prefix}pokedex 54 or {prefix}pokedex Charmander",
                    inline=False)
    embed.add_field(name=f"{prefix}log IDchannel",
                    value=f"Change the log channel (Require administrator permission)\nExample: {prefix}log 872895837758455849",
                    inline=False)
    embed.add_field(name=f"{prefix}save",
                    value=f"Create a save from the current game\nExample: {prefix}save",
                    inline=False)

    embed.set_footer(text="By Brainless")
    await ctx.channel.send(embed=embed)
    print("[main.py] help command printed")
    await ctx.message.delete()


bot.run(token)
