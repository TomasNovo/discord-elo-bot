"""Module used to represent every commands an admin is able to do."""

import discord
from utils.decorators import check_category, check_channel, is_arg_in_modes
from discord import Embed
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from GAMES import GAMES


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['fr'])
    @check_category('Solo elo')
    @has_permissions(manage_roles=True)
    async def force_remove(self, ctx, name):
        """Remove the player from the current queue."""
        if not name[3: -1].isdigit():
            await ctx.send("You better ping the player")
        name = int(name[3: -1])
        mode = int(ctx.channel.name.split('vs')[0])
        game = GAMES[ctx.guild.id]
        queue = game.queues[mode]
        await ctx.send(queue.remove_player(game.leaderboards[mode]
                      [name]))

    @commands.command()
    @has_permissions(kick_members=True)
    @check_category('Elo by Anddy')
    @check_channel('bye')
    async def force_quit(self, ctx, name):
        """Delete the seized user from the registered players.

        Example: !force_quit @Anddy
        The command is the same than quit_elo except that the user has to make
        someone else quit the Elo.
        This can be used only in Bye channel.
        Can't be undone."""
        game = GAMES[ctx.guild.id]
        name = name[3: -1]
        if not name.isdigit():
            await ctx.send("You better ping the player !")
            return
        name = int(name)
        game.erase_player_from_queues(name)
        game.erase_player_from_leaderboards(name)

        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=f'<@{name}> has been removed from the rankings'))


    @commands.command(aliases=['cq', 'c_queue'])
    @has_permissions(manage_roles=True)
    @check_category('Solo elo')
    async def clear_queue(self, ctx):
        """Clear the current queue."""
        game = GAMES[ctx.guild.id]
        mode = int(ctx.channel.name.split('vs')[0])
        last_id = game.queues[mode].game_id
        if not game.queues[mode].has_queue_been_full:
            game.queues[mode] = queue_elo.Queue(
                2 * mode, game.queues[mode].mode, last_id)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The queue is now empty"))



    @commands.command()
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('bans')
    async def ban(self, ctx, name, time, unity, reason=""):
        """Bans the player for a certain time.

        unity must be in s, m, h, d (secs, mins, hours, days).
        reason must be into " "
        """
        name = name[3: -1]
        if not name.isdigit():
            await ctx.send("You better ping the player !")
            return
        if not time.isdigit():
            raise commands.errors.MissingRequiredArgument
        name = int(name)
        formats = {"s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24}
        total_sec = int(time) * formats[unity]
        GAMES[ctx.guild.id].ban_player(name, total_sec, reason)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The player has been banned ! Check !bans"))


    @commands.command()
    @check_category('Elo by Anddy')
    @check_channel('bans')
    @has_permissions(manage_roles=True)
    async def unban(self, ctx, name):
        """Unban the player."""
        name = name[3: -1]
        if not name.isdigit():
            await ctx.send("You better ping the player !")
            return
        name = int(name)
        GAMES[ctx.guild.id].unban_player(name)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The player has been unbanned ! Check !bans"))



    @commands.command()
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    async def setelo(self, ctx, mode, name, elo):
        """Set the elo to the player in the specific mode."""
        GAMES[ctx.guild.id].set_elo(int(mode), int(name[3: -1]), int(elo))
        await ctx.send("Worked!")

    @commands.command()
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    async def setallstats(self, ctx, mode, name, *stats):
        """Set the stats to the player in the specific mode.
        Let any stat to -1 to not let it change.
        In order:
            [elo, wins, losses, nb_matches, wlr, most_wins_in_a_row,
            most_losses_in_a_row, current_win_streak,
            current_lose_streak, double_xp]
            The wlr will anyway be calculated at the end.
        """
        player = GAMES[ctx.guild.id].leaderboards[int(mode)][int(name[3: -1])]
        stats_name = Player.STATS[1: -1]
        if len(stats) > len(stats_name):
            await ctx.send("Too much arguments ! I'll cancel in case you messed up")
            return

        for i, stat in enumerate(stats):
            try:
                stat = int(stat)
                if stat >= 0:
                    setattr(player, stats_name[i], stat)
            except ValueError:
                await ctx.send(f"Wrong format for {stats_name[i]}.")

        player.wlr = player.wins / player.losses if player.losses != 0 else 0
        await ctx.send("Worked!")



def setup(bot):
    bot.add_cog(Admin(bot))