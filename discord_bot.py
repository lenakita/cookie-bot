"""
A general purpose Discord Bot for playing audio, amongst other things
"""

import os
from discord.ext import commands
from discord import Game
from audio import Audio

class CookieBot(commands.Cog):
    """
    The main bot class where the commands are defined
    """
    def __init__(self, key_store_file: str = ''):
        if not key_store_file:
            return

        keys = []
        with open(key_store_file, 'r', encoding='utf-8') as key_file:
            keys = key_file.readlines()
            for idx, key in enumerate(keys):
                keys[idx] = key.split(":")[1].strip()

        self.bot_token = keys[0]
        self.bot_id = keys[1]

    def setup_bot(self):
        """
        Initialises the bot and sets its presence message
        """
        self.bot = commands.Bot(command_prefix='!')
        self.bot.add_cog(self)
        self.audio = Audio(self.bot)
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
    async def test(self, ctx):
        """
        :komicat:
        """
        # FIXME: remove test emoji and find way to parse emoji ID from chat
        #  discord.Emoji docs: https://gist.github.com/scragly/b8d20aece2d058c8c601b44a689a47a0
        await ctx.send("I'm a test cat <a:komicat:882384257455099924>")

    @commands.command(name='join', pass_context=True, no_pm=True)
    async def join(self, ctx):
        """
        Has the bot join the requester's channel
        """
        channel = ctx.author.voice.channel
        await self.audio.join(ctx, channel)

    @commands.command(name='play', pass_context=True, no_pm=True)
    async def yt_player(self, ctx):
        """
        Plays audio from youtube requested in the message
        """
        song_url = ctx.message.content.split(" ")[1]
        await self.audio.play_audio(ctx, song_url)

    @commands.command(name='volume', pass_context=True, no_pm=True)
    async def volume(self, ctx):
        """
        Changes the volume of the bot to the specified value
        """
        volume = ctx.message.content.split(" ")[1]
        if not volume.isdigit():
            await ctx.send("That is not a valid volume, please provide an integer")
            return
        if int(volume) > 200:
            await ctx.send("Normalising volume to the maximum of 200%")
            volume = 200
        await self.audio.change_volume(ctx, int(volume))

    @commands.command(name='stop', pass_context=True, no_pm=True)
    async def audio_stop(self, ctx):
        """
        Stops the audio from playing
        Must be a method as it is a command that needs to overwrite play_audio
        """
        await ctx.voice_client.disconnect()

    @yt_player.before_invoke
    async def ensure_voice(self, ctx):
        """
        Ensures that when the youtube player is invoked the requesting user is
        connected to a voice channel
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


if __name__ == "__main__":
    key_store_path = os.path.join(os.path.dirname(__file__), 'keys.txt')
    bot = CookieBot(key_store_path)
    bot.setup_bot()
    bot.run()
