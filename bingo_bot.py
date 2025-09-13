import discord
from discord import app_commands
import math

from bingo_game import Game, Player, games
from bingo_card_generator import generate_card_image
from bingo_ui import LobbyView, create_lobby_embed, MainMenuView, create_main_menu_embed

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()

@tree.command(name="bingo", description="打开Bingo游戏菜单")
async def bingo_menu(interaction: discord.Interaction):
    """显示Bingo游戏主菜单"""
    embed = create_main_menu_embed()
    view = MainMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# 旧的bingo_status命令已移除，现在通过UI按钮控制游戏状态

# 旧的bingo_list命令已移除，游戏信息现在通过UI界面显示

# 旧的bingo_join命令已移除，现在通过UI按钮加入游戏

# 旧的bingo_reroll命令已移除，卡片在加入游戏时自动生成

# 旧的bingo_mark命令已移除，现在通过UI按钮和模态框标记单词

# 旧的bingo_show命令已移除，现在通过UI按钮查看卡片

# 旧的bingo_participants命令已移除，参与者信息现在通过UI界面显示

# 运行机器人
client.run("YOUR_BOT_TOKEN")