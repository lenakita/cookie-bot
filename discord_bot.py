import os
from discord.ext import commands
from discord import Game, opus
from audio import Audio

class CookieBot(commands.Cog):
    def __init__(self, key_store_path: str = ''):
        if not key_store_path:
            return

        keys = []
        with open(key_store_path, 'r') as key_file:
            keys = key_file.readlines()
            for idx, key in enumerate(keys):
                keys[idx] = key.split(":")[1].strip()

        self.bot_token = keys[0]
        self.bot_id = keys[1]

    def setup_bot(self):
        """
        Initialises the bot and sets its presence message
        """
        try:
            self.bot = commands.Bot(command_prefix='!')
            self.bot.add_cog(self)
            self.audio = Audio(self.bot)
        except Exception as err:
            print(f"Exception setting the bot {err}")
        @self.bot.event
        async def on_ready():
            # requires the type argument of 1 to make the presence visible
            await self.bot.change_presence(activity=Game(name="with cookie dough", type=1))
            print(f"Logged in as\n{self.bot.user.name}\n{self.bot.user.id}\n------------")

    def run(self):
        """
        Uses the bot token provided from the file to run the bot
        """
        self.bot.run(self.bot_token)

    """
    Each command method takes the same parameters:

    Keyword arguments:
    ctx -- message information
    args -- extra arguments passed with the message

    Command decorator arguments:
    name -- message contents required to trigger the method, along with bot_prefix
    pass_context -- allows for original message to be passed as a parameter (default True)
    no_pm -- source of message from channel or private message (default True)
    """
    @commands.command(name='test', pass_context=True, no_pm=True)
    async def test(self, ctx, args=''):
        """
        Test method
        """
        # FIXME: remove test emoji and find way to parse emoji ID from chat
        #  discord.Emoji docs: https://gist.github.com/scragly/b8d20aece2d058c8c601b44a689a47a0
        await ctx.send("I'm a test cat <a:komicat:882384257455099924>")

    @commands.command(name='request', pass_context=True, no_pm=True)
    async def yt_player(self, ctx, args=''):
        """
        Plays audio from youtube requested in the message
        """
        message = ctx.message.content
        channel = ctx.message.author.voice_channel
        await self.audio.play_audio(message, channel)

    @commands.command(name='stop', pass_context=True, no_pm=True)
    async def audio_stop(self, ctx, args=''):
        """
        Stops the audio from playing,
        must be a method as it is a command that needs to overwrite play_audio
        """
        self.audio.stop = True

    @commands.command(name='queue', pass_context=True, no_pm=True)
    async def audio_queue(self, ctx, args=''):
        """
        Adds a song to the queue using the !queue command
        """
        song_url = ctx.message.content.split(" ")[1]
        # appends the song to the list attribute for use in play_audio
        self.audio.song_list.append(song_url)
        # also gets the video title and states the song has been added to the queue
        video_title = self.audio.extract_video_title(song_url)
        await ctx.send(f"{video_title} added to the queue")


if __name__ == "__main__":
    key_store_path = os.path.join(os.path.dirname(__file__), 'keys.txt')
    bot = CookieBot(key_store_path)
    bot.setup_bot()
    bot.run()
