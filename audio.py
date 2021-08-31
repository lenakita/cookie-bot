import asyncio
import lxml
import youtube_dl
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError

SLEEP_TIME = 1

class Audio():
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.video_title = ""

        self.song_list = []
        self.stop = False
        self.player = None
        self.response = ""

    async def create_player(self, song_url, voice, volume=0.3):
        """
        Creates the audio player to allow for playing of youtube videos
        
        Keyword arguments:
        song_url -- youtube URL of the video to take audio from
        voice -- audio channel of the user
        volume -- how loud the bot is when playing the video (default 0.3)
        """
        # the arguments ensure that the bot stays connected, fixes the random stop error
        self.player = await voice.create_ytdl_player(song_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        self.player.volume = volume
        self.player.start()

    async def play_audio(self, message: str, channel):
        """
        A very primitive audio player for processing short youtube videos and playing them to the given voice channel
        
        Keyword arguments:
        message -- contains the youtube URL to read
        channel -- audio channel of the user that sent the message
        Returns:
        response -- the message for the bot to send
        """
        song_url = message.split(" ")[1]
        self.video_title = self.extract_video_title(song_url)
        self.song_list.append(song_url)
        self.stop = False
        try:
            await self.play_loop(channel, song_url)
        except AttributeError as att_err:
            print('The following attribute error occurred in play_audio {}'.format(att_err))

    def extract_video_title(self, url: str) -> str:
        """
        Gets the video title using lxml
        
        Keyword arguments:
        url -- the URL of the youtube video which is parsed to get the title from XML of the webpage
        """
        youtube = lxml.etree.HTML(urlopen(url).read())
        video_title = youtube.xpath("//span[@id='eow-title']/@title")
        print(''.join(video_title))
        video_title = ''.join(video_title)
        return video_title
    
    async def play_loop(self, channel, song_url):
        """
        Loops whilst the audio is playing, checking the status of the player throughout
        Keyword arguments:
        voice -- the voice channel to join, a discord.py voice_channel object
        song_url -- the youtube URL of the audio to play
        """
        if not self.is_playing:
            await self.bot.say(f"Now playing {self.video_title}")
            voice = await self.bot.join_voice_channel(channel)
            await self.create_player(song_url, voice)
            self.is_playing = True

            while self.is_playing:
                while not self.player.is_done():
                    await self.check_player_status(voice)
                self.song_list.pop(0)

                await asyncio.sleep(3)

                if len(self.song_list) > 0:
                    self.initialise_song(voice)
                else:
                    await voice.disconnect()
                    self.is_playing = False
        else:
            self.check_song_list()

    async def initialise_song(self, voice):
        """
        Used to create a new player if a song is added to the queue, and none are already present
        Keyword arguments:
        voice -- the voice channel to join, a discord.py voice_channel object
        """
        song_url = self.song_list[0]
        video_title = self.extract_video_title(song_url)
        self.video_title = video_title
        await self.bot.say(f"Now playing {self.video_title}")
        await self.create_player(song_url, voice)
    
    def check_song_list(self):
        """
        Loops over the list of songs in the queue to get rid of the remaining songs
        """
        for idx in range(len(self.song_list)):
            if idx > 1:
                self.song_list.pop(idx)
    
    async def check_player_status(self, voice):
        """
        Checks the current status of the audio player to see if it should stop
        Keyword arguments:
        voice -- the current voice channel the bot is in
        """
        if not self.stop:
            await asyncio.sleep(SLEEP_TIME)
        else:
            await voice.disconnect()
            self.is_playing = False
