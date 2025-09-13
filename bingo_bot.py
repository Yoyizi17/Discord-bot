import discord
from discord import app_commands
import math

from bingo_game import Game, Player, games
from bingo_card_generator import generate_card_image
from bingo_ui import LobbyView, create_lobby_embed

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()

class BingoCommands(app_commands.Group):
    pass

bingo = BingoCommands(name="bingo", description="Bingo game commands")
tree.add_command(bingo)

@bingo.command(name="create", description="创建一个新的宾果游戏")
@app_commands.describe(name="游戏名称")
async def bingo_create(interaction: discord.Interaction, name: str):
    if name in games:
        await interaction.response.send_message(f"游戏 '{name}' 已存在。", ephemeral=True)
        return

    game = Game(name=name, creator=interaction.user)
    games[name] = game

    embed = create_lobby_embed(game)
    view = LobbyView(game)
    
    await interaction.response.send_message(embed=embed, view=view)

@bingo.command(name="addwords", description="为游戏添加词汇")
@app_commands.describe(name="游戏名称", words="词汇列表，用逗号分隔")
async def bingo_addwords(interaction: discord.Interaction, name: str, words: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if interaction.user.id != game.creator_id:
        await interaction.response.send_message("只有游戏创建者才能添加词条。", ephemeral=True)
        return

    if game.status != "preparing":
        await interaction.response.send_message("游戏已开始或已结束，无法添加词条。", ephemeral=True)
        return

    word_list = [w.strip() for w in words.split(',') if w.strip()]
    num_words = len(word_list)
    dimension = int(math.sqrt(num_words))

    if dimension * dimension != num_words:
        await interaction.response.send_message(f"词条数量必须是 N*N 的形式 (例如: 9, 16, 25)。你提供了 {num_words} 个词条。", ephemeral=True)
        return

    game.words = word_list
    game.dimension = dimension
    await interaction.response.send_message(f"已为游戏 {name} 添加 {num_words} 个词条，卡片尺寸为 {dimension}x{dimension}。", ephemeral=True)

# 旧的bingo_status命令已移除，现在通过UI按钮控制游戏状态

# 旧的bingo_list命令已移除，游戏信息现在通过UI界面显示

# 旧的bingo_join命令已移除，现在通过UI按钮加入游戏

# 旧的bingo_reroll命令已移除，卡片在加入游戏时自动生成

# 旧的bingo_mark命令已移除，现在通过UI按钮和模态框标记单词

# 旧的bingo_show命令已移除，现在通过UI按钮查看卡片

# 旧的bingo_participants命令已移除，参与者信息现在通过UI界面显示

# 运行机器人
client.run("YOUR_BOT_TOKEN")