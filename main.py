import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pytube import YouTube
import atexit
import re
from youtube_search import YoutubeSearch
from asyncio import sleep
load_dotenv('envi.env')
TOKEN = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix="!")
filename = "audio.mp3"
video_length = 0

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

def play_music(voice):
    voice.play(discord.FFmpegPCMAudio(source=filename))

@client.command()
async def play(ctx, url : str):
    current_song = os.path.isfile(filename)
    try:
        if current_song:
            os.remove(filename)
    except PermissionError:
        await ctx.send("Wait for the current music to end or use the '!stop' command")

    author = ctx.message.author.voice
    if not author:
        await ctx.send("You have to be in a voice channel to play a song!")
    channel = author.channel
    await channel.connect()
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice is None or not voice.is_connected():
        await channel.connect()

    if author:
        if is_url(url):
            yt = YouTube(url)
            audio = yt.streams.filter(only_audio=True).first()
            out_file = audio.download(output_path=".")
            base, ext = os.path.splitext(out_file)
            await ctx.send("Playing " + yt.title)
            video_length = yt.length
        else:
            result = YoutubeSearch(url, max_results=1).to_dict()
            for v in result:
                youtube_url = "https://www.youtube.com" + v['url_suffix']
                yt = YouTube(youtube_url)
                audio = yt.streams.filter(only_audio=True).first()
                out_file = audio.download(output_path=".")
                base, ext = os.path.splitext(out_file)
                os.rename(out_file, filename)
                await ctx.send("Currently playing " + yt.title)
                video_length = yt.length

            play_music(voice)
            while voice.is_playing():
                await sleep(1)
            await voice.disconnect()
            os.remove(filename)


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("No audio is playing currently!")

@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("No audio is playing currently!")

@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

def exit_handler():
    os.remove(filename)

atexit.register(exit_handler)

client.run(TOKEN)