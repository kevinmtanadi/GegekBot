import os
import discord
from discord.ext import commands
from pytube import YouTube
import re
from youtube_search import YoutubeSearch
from asyncio import sleep
from dotenv import load_dotenv

load_dotenv()


intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus.so')

class Song:
    def __init__(self, title, url, id, length):
        self.id = id
        self.title = title
        self.url = url
        self.length = length

songQueue = []
filename = "audio.mp3"

isLooping = False

def is_url(url):
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if url is not None and regex.search(url):
        return True
    return False

def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()

def play_music(voice):
    voice.play(discord.FFmpegPCMAudio(source=filename))

intents.voice_states = True

@client.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        # Exiting if the bot it's not connected to a voice channel
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()

@client.command()
async def add(ctx, *, url : str):
    id = 0
    author = ctx.message.author.voice
    if not author:
        await ctx.send("You have to be in a voice channel to play a song!")
    else:
        if isLooping:
            await ctx.send("Stop the loop using /loop before adding any new song")
        else:
            if (is_url(url)):
                yt = YouTube(url)
                songQueue.append(Song(yt.title, url, id, yt.length))
            else:
                result = YoutubeSearch(url, max_results=1).to_dict()
                for v in result:
                    youtube_url = "https://www.youtube.com" + v['url_suffix']
                    yt = YouTube(youtube_url)
                    songQueue.append(Song(yt.title, youtube_url, id, yt.length))
            id += 1
            await ctx.send("Song added to the queue!")

@client.command()
async def loop(ctx):
    isLooping = not isLooping
    if isLooping:
        await ctx.send("Currently looping")
    else:
        await ctx.send("Stopped looping")


@client.command()
async def queue(ctx):
    if len(songQueue) > 0:
        i = 1
        songList = "Current song queue :\n"
        for songs in songQueue:
            songList += str(i) + ". " + songs.title + "\n"
            i += 1
        await ctx.send(songList)
    else:
        await ctx.send("There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue")

@client.command()
async def play(ctx):
    if os.path.isfile(filename):
        os.remove(filename)
    if len(songQueue) == 0:
        await ctx.send("There is no song on the queue. Use !add [music title or youtube link] to add a song to the queue")
    else:
        author = ctx.message.author.voice
        if not author:
            await ctx.send("You have to be in a voice channel to play a song!")
        channel = author.channel
        try:
            await channel.connect()
        except:
            print("Bot already connected")
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

        if voice is None or not voice.is_connected():
            await channel.connect()

        while len(songQueue) > 0:
            currentSong = songQueue[0]

            for obj in songQueue:
                print(obj.title)

            yt = YouTube(currentSong.url)
            audio = yt.streams.filter(only_audio=True).first()
            out_file = audio.download(output_path=".")
            os.rename(out_file, filename)
            await ctx.send("Current playing " + yt.title)
            play_music(voice)

            while currentSong.length > 0:
                await sleep(1)
                currentSong.length -= 1

            if isLooping:
                songQueue.append(currentSong)

            songQueue.remove(currentSong)
            os.remove(filename)

        await voice.disconnect()

@client.command()
async def stop(ctx):
    author = ctx.message.author.voice
    songQueue.clear()
    if not author:
        await ctx.send("You have to be in a voice channel!")
    else:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            await ctx.send("The bot is not connected to a voice channel.")
        else:
            voice.stop()
            if voice.is_connected():
                await ctx.send("The audio is stopped.")
                await voice.disconnect()
            else:
                await voice.disconnect()
                await ctx.send("The bot is not connected to a voice channel.")

@client.command()
async def clear(ctx):
    if len(songQueue) > 1:
        await ctx.send("The song queue is emptied")
    else:
        await ctx.send("There is currently no song in the queue!")


@client.command()
async def skip(ctx):
    author = ctx.message.author.voice
    if not author:
        await ctx.send("You have to be in a voice channel!")
    else:
        currentSong = songQueue[0]
        currentSong.length = 0
        ctx.voice_client.stop()

@client.command()
async def remove(ctx, arg : int):
    if len(songQueue) >= 1:
        if arg > len(songQueue):
            await ctx.send("There are only " + str(len(songQueue)) + "songs in the queue!")
        else:
            songToDelete = songQueue[arg-1]
            await ctx.send("Successfully deleted " + str(songToDelete.title) + " from to queue")
            songQueue.remove(songToDelete)

    else:
        await ctx.send("There is currently no song in the queue!")

client.run(os.getenv('TOKEN'))