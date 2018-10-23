import os
import subprocess
import platform
import json
import discord
from discord.ext import commands
from dotmap import DotMap
import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
from utils import colorscale, upload_to_aws
import asyncio
import datetime

char = "snowcolas"
realm = "hyjal"
region = "us"
calculate_scale_factors = 1
html = "john.html"
armory = f'{region},{realm},{char}'

data_loc = os.environ.get("DATA_LOC", default='char_data/')


class Colors:
    PClass = {
        'Knight': '#C41F3B',
        'Demon': '#A330C9',
        'Druid': '#FF7D0A',
        'Hunter': '#ABD473',
        'Mage': '#40C7EB',
        'Monk': '#00FF96',
        'Paladin': '#F58CBA',
        'Priest': '#FFFFFF',
        'Rogue': '#FFF569',
        'Shaman': '#0070DE',
        'Warlock': '#8787ED',
        'Warrior': '#C79C6E',
    }


class SimC:
    def __init__(self, bot, simc_path):
        self.bot = bot
        self.simc = simc_path
        if platform.system() == "Windows":
            self.simc += ".exe"
        try:
            json_data = open(f"{char_data}results.json").read()
            self.data = DotMap(json.loads(json_data))
        except Exception:
            print("unable to load json_data")

    def run_sim(
            self,
            armory,
            item,
            calculate_scale_factors=0,
            fname="results",
    ):

        commands = [
            f"{self.simc}", f"armory={armory}",
            f"calculate_scale_factors={calculate_scale_factors}",
            f"html={data_loc}{fname}.html", f"json2={data_loc}{fname}.json"
        ]
        if item is not None:
            commands.append("copy=New_item")
            commands.append(item)
            #commands.append(option)

        sim = subprocess.check_output(commands)
        json_data = open(f"{data_loc}{fname}.json").read()
        self.data = DotMap(json.loads(json_data))

        return sim

    def get_PAWN_String(self):
        sim = self.data
        scale_factors = sim.sim.players[0].scale_factors
        player = sim.sim.players[0]
        player_info = {
            "name": player["name"],
            "spec": player["specialization"].split()[0],
            "class": player["specialization"].split()[1]
        }
        first = True
        PAWN_String = f'Pawn: v1: "{player_info["name"]}-{player_info["spec"]}" '
        for key, val in scale_factors.items():
            temp = f"{key}={val}"
            if first:
                PAWN_String += temp
                first = False
            else:
                PAWN_String += ", " + temp

        return PAWN_String

    def save_plot(self, df, filename):
        style.use('ggplot')

        fname = filename
        image_loc = 'images/'
        plot_width = 20
        plot_height = 1.75 * len(df['mean'])

        fig, ax = plt.subplots(figsize=(plot_width, plot_height))

        items = df.index
        y_pos = np.arange(len(items))
        performance = df['mean']
        error = df['error']
        color = Colors.PClass[df['class'][0]]
        darker = colorscale(color, .7)
        bgcolor = '#2C2F33'

        ax.set_xlim(0, max(df['max']) * 1.1)
        ax.grid(False)
        ax.set_facecolor(bgcolor)
        ax.tick_params(axis='y', which='major', labelsize=50, colors=color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_xaxis().set_visible(False)

        ax.barh(
            y_pos,
            performance,
            edgecolor=color,
            color=color,
            xerr=error,
            align='center',
            height=0.9,
            error_kw=dict(elinewidth=4, capsize=30, capthick=4, ecolor=darker))

        for i, item in enumerate(df['mean']):
            ax.text(
                max(df['max']) + 200,
                y_pos[i] + .15,
                str(item),
                color=color,
                fontweight='bold',
                fontsize=50)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(items)
        ax.invert_yaxis()  # labels read top-to-bottom

        plt.tight_layout()
        timestamp = datetime.datetime.now().strftime("%d%m%y%f")
        fname += timestamp
        plt.savefig(f"{image_loc}{fname}.png", transparent=True)

        return f"{fname}.png", color

    def get_dps(self, char_name):
        """
        Returns a data frame of:
        [mean, min, max, median, error, class] for each player in sim
        """

        df = pd.DataFrame()
        s = []
        jsond = json.loads(open(f"{data_loc}{char_name}.json").read())
        players = jsond['sim']['players']

        for player in players:
            name = player['name']
            mean = int(player['collected_data']['dps']['mean'])
            minn = int(player['collected_data']['dps']['min'])
            maxx = int(player['collected_data']['dps']['max'])
            median = int(player['collected_data']['dps']['median'])
            player_class = player["specialization"].split()[-1]
            if player_class == "Hunter":
                if player["specialization"].split()[-2] == "Demon":
                    player_class = "Demon"
                else:
                    player_class = "Hunter"

            series = pd.Series(
                [mean, minn, maxx, median, player_class], name=name)
            s.append(series)

        df = pd.concat(s, axis=1).T
        df.columns = ['mean', 'min', 'max', 'median', 'class']
        df['error'] = (df['max'] - df['min']) / 2

        return df

    @commands.command(pass_context=True, no_pm=True)
    async def sim(
            self,
            ctx,
            toon,
            item=None,
            region='us',
    ):  # charname-server
        _toon = toon.split('-')

        msg = await self.bot.say("working...")

        armory = f"{region},{_toon[1]},{_toon[0]}"
        simulation = self.run_sim(armory, item, fname=toon)
        info = self.get_dps(toon)
        print(info)
        plot = self.save_plot(info, toon)

        report, png = upload_to_aws(toon, plot[0])

        embed = discord.Embed(
            title=f"Your simcraft report for {toon}",
            decription="\n\n",
            color=discord.Colour.teal())

        embed.set_author(
            name='Simcraft Report',
            icon_url=
            'https://avatars3.githubusercontent.com/u/1552677?s=400&v=4',
        )

        embed.set_thumbnail(
            url='http://www.simulationcraft.org/img/bfalogo.png')
        embed.set_image(url=png)
        embed.add_field(
            name="Full HTML Report", value=f"[{toon}]({report})", inline=False)
        embed.add_field(name="Simcraft Version", value="801-02", inline=False)
        embed.add_field(name="Fight Length", value="300 seconds", inline=True)
        embed.add_field(name="Fight Type", value="Patchwerk", inline=True)

        await self.bot.edit_message(msg, new_content="Finished", embed=embed)

        #TODO: return ilvl
        #TODO: return character lvl
        #TODO: fix spacing between label on plot


#main_hand=,id=163871,enchant_id=5963,bonus_id=5125/1532/4786,reforge=28

#main = SimC("bot", "C:\Simulationcraft(x64)\simc")

#main.run_sim(armory, fname='busted')
#info = main.get_dps('busted')
#print(info)
#main.save_plot(info)
#main.request_sim('angrygoose-hyjal')