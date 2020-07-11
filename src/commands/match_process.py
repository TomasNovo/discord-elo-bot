from discord import Embed
from main import GAMES
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from utils.decorators import check_category, check_channel, is_arg_in_modes
from utils.utils import team_name, get_elem_from_embed


class Match_process(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.waiting_for_approval = {}
        self.correctly_submitted = {}


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """

        @param user: discord.User
        @type reaction: discord.Reaction
        """
        reaction.emoji = str(reaction)
        if user.id == self.bot.user.id or not reaction.message.embeds \
                or reaction.emoji not in "✅❌":
            return
        embed = get_elem_from_embed(reaction)
        if embed["function"] != "autosubmit":
            return
        mode, id, winner = embed["mode"], embed["id"], int(embed["key"])
        game = GAMES[user.guild.id]
        if id not in self.waiting_for_approval[mode]:
            return
        queue = self.waiting_for_approval[mode][id]
        if user.id not in game.leaderboards[mode] or\
            game.leaderboards[mode][user.id] not in queue:
            await reaction.message.remove_reaction(reaction.emoji, user)
            return

        if mode not in self.correctly_submitted:
            self.correctly_submitted[mode] = set()
        if id in self.correctly_submitted[mode]:
            return
        # The message got enough positive reaction (removing bot's one)
        if reaction.message.reactions[0].count - 1 >= queue.max_queue // 2 + 1:
            text, worked = game.add_archive(mode, id, winner)
            if worked:
                self.waiting_for_approval[mode].pop(id, None)
                self.correctly_submitted[mode].add(id)
            await reaction.message.channel.send(embed=Embed(color=0xFF0000 if winner == 1 else 0x0000FF,
                description=text))

            return
        if reaction.message.reactions[1].count - 1 >= queue.max_queue // 2:
            self.waiting_for_approval[mode].pop(id, None)
            await reaction.message.channel.send(embed=Embed(color=0x000000,
                description=f"The game {id} in the mode {mode} wasn't accepted.\n\
                            Please submit again"))



    @commands.command(aliases=['as'])
    @check_category('Elo by Anddy')
    @check_channel('autosubmit')
    @is_arg_in_modes(GAMES)
    async def autosubmit(self, ctx, mode, id_game, winner):
        """Submit the score of a game.

        Example: !s 1 7 1
        in the mode 1vs1, in the 7th game, the team 1 (red) won.
        This will update NOT the rankings until the game is approved.
        """
        game = GAMES[ctx.guild.id]
        if not id_game.isdigit() or not winner.isdigit():
            raise commands.errors.MissingRequiredArgument
        mode, id_game, winner = int(mode), int(id_game), int(winner)
        if not id_game in game.undecided_games[mode]:
            await ctx.send(embed=Embed(color=0x000000,
                description="The game is not in undecided games!"))
            return
        queue = game.undecided_games[mode][id_game]
        if not mode in self.waiting_for_approval:
            self.waiting_for_approval[mode] = {}
        self.waiting_for_approval[mode][id_game] = queue
        nb_yes = int(queue.max_queue // 2 + 1)
        nb_no = int(queue.max_queue // 2)
        res = f"<@{ctx.author.id}> is saying that {team_name(winner)} won.\n"
        res += f"Do you confirm ? {nb_yes} ✅ are needed to make it official.\n"
        res += f'{nb_no} ❌ {"is" if nb_no == 1 else "are"} needed to cancel it.\n'
        res += "Any attempt to mess up the result will lead to a ban."

        msg = await ctx.send(queue.ping_everyone(),
            embed=Embed(title="autosubmit",
            color=0xFF0000 if winner == 1 else 0x0000FF,
            description=res)\
                .add_field(name="name", value="autosubmit") \
                .add_field(name="winner", value=winner) \
                .add_field(name="mode", value=mode) \
                .add_field(name="id", value=id_game) \
                .set_footer(text=f"[ 1 / 1 ]"))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")








    @commands.command(aliases=['s', 'game'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def submit(self, ctx, mode, id_game, winner):
        """Submit the score of a game.

        Example: !s 1 7 1
        in the mode 1vs1, in the 7th game, the team 1 (red) won.
        This will update the rankings.
        """
        game = GAMES[ctx.guild.id]
        if not id_game.isdigit() or not winner.isdigit():
            raise commands.errors.MissingRequiredArgument
        mode, id_game, winner = int(mode), int(id_game), int(winner)
        text, worked = game.add_archive(mode, id_game, winner)
        await ctx.send(embed=Embed(color=0xFF0000 if winner == 1 else 0x0000FF,
                                   description=text))
        if worked and mode in self.waiting_for_approval:
            self.waiting_for_approval[mode].pop(id_game, None)

    @commands.command()
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def undo(self, ctx, mode, id_game):
        """Undo a game.

        Example: !undo 1 7
        in the mode 1vs1, in the 7th game.
        This will reset the ranking updates of this match.
        The game will be in undecided.
        """
        game = GAMES[ctx.guild.id]
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.undo(int(mode), int(id_game))))

    @commands.command(aliases=['c', 'clear'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def cancel(self, ctx, mode, id_game):
        """Cancel the game given in arg.

        Example: !cancel 1 3
        will cancel the game with the id 3 in the mode 1vs1.
        """
        game = GAMES[ctx.guild.id]
        if game.cancel(int(mode), int(id_game)):
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"The game {id_game} has been canceled"))
        else:
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"Couldn't find the game {id_game} in the current games."))

    @commands.command(aliases=['uc', 'uclear'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def uncancel(self, ctx, mode, id_game):
        """Uncancel the game given in arg.

        Example: !uncancel 1 3
        will uncancel the game with the id 3 in the mode 1vs1.
        """
        game = GAMES[ctx.guild.id]
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.uncancel(int(mode), int(id_game))))

    @commands.command(aliases=['u'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def undecided(self, ctx, mode):
        """Display every undecided games.

        Example: !undecided 2
        Will show every undecided games in 2vs2, with the format below.
        id: [id], Red team: [player1, player2], Blue team: [player3, player4]."""
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.undecided(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")

    @commands.command(aliases=['cl'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def canceled(self, ctx, mode):
        """Display every canceled games of a specific mode.

        Example: !cl 2
        Will show every canceled games in 2vs2.
        """
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.canceled(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")

    @commands.command(aliases=['a'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def archived(self, ctx, mode):
        """Display every games of a specific mode.

        Example: !archived 2
        Will show every games in 2vs2, with the format below.
        id: [id], Winner: Team Red/Blue, Red team: [player1, player2],
        Blue team: [player3, player4]."""
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.archived(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")


def setup(bot):
    bot.add_cog(Match_process(bot))
