"""
Contains classes for enabling audio playing for the Discord Bot
"""

import asyncio
import discord
import youtube_dl

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    """
    The Youtube Downloader class for handling YT video downloads
    """
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, event_loop=None, stream=False):
        """
        Reads a youtube video from a url, downloads it for playing and
        parses the url to get the video name

        Keyword arguments:
        url -- the url of the youtube video to parse
        loop -- whether to loop the video
        stream -- whether the audio should be streamed rather than downloaded

        Returns:
        An ffmpeg audio class with the required file that has been downloaded
        """
        loop = event_loop or asyncio.get_event_loop()
        data = await event_loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Audio():
    def __init__(self, bot):
        self.bot = bot
        self.player = None

    async def join(self, ctx, channel: discord.VoiceChannel):
        """
        Gets the bot to join a voice channel

        Keyword arguments:
        ctx -- the context for the message
        channel -- the channel to join
        """

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    async def create_player(self, song_url, voice, volume=0.3):
        """
        Creates the audio player to allow for playing of youtube videos

        Keyword arguments:
        song_url -- youtube URL of the video to take audio from
        voice -- audio channel of the user
        volume -- how loud the bot is when playing the video (default 0.3)
        """
        # the arguments ensure that the bot stays connected, fixes the random stop error
        self.player = await voice.create_ytdl_player(
            song_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        )
        self.player.volume = volume
        self.player.start()

    async def play_audio(self, ctx, url):
        """
        A very primitive audio player for processing short youtube videos
        and playing them to the given voice channel

        Keyword arguments:
        message -- contains the youtube URL to read
        channel -- audio channel of the user that sent the message

        Returns:
        response -- the message for the bot to send
        """
        async with ctx.typing():
            player = await YTDLSource.from_url(url, event_loop=self.bot.loop, stream=True)
            ctx.voice_client.play(
                player,
                after=lambda e: print(f'Player error: {e}') if e else None
            )

        await ctx.send(f'Now playing: {player.title}')

    async def change_volume(self, ctx, volume: int):
        """
        Changes the audio player's volume

        Keyword arguments:
        ctx -- the context for the message
        volume -- the volume, as an integer, to change the bot to
        """
        # TODO: validate user's rank so people can't randomly change the volume
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")
