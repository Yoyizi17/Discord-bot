import discord
from discord import app_commands
import math

from bingo_game import Game, Player, games
from bingo_card_generator import generate_card_image

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()

@tree.command(name="bingo_create", description="创建一个新的宾果游戏")
@app_commands.describe(name="游戏名称")
async def bingo_create(interaction: discord.Interaction, name: str):
    if name in games:
        await interaction.response.send_message(f"名为 {name} 的游戏已存在。", ephemeral=True)
    else:
        games[name] = Game(name, interaction.user.id)
        await interaction.response.send_message(f"游戏 {name} 已创建！", ephemeral=True)

@tree.command(name="bingo_addwords", description="为宾果游戏添加词条 (N*N 数量)")
@app_commands.describe(name="游戏名称", words="用逗号分隔的词条列表")
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

@tree.command(name="bingo_status", description="设置宾果游戏的状态")
@app_commands.describe(name="游戏名称", status="游戏状态 (preparing, started)")
async def bingo_status(interaction: discord.Interaction, name: str, status: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if interaction.user.id != game.creator_id:
        await interaction.response.send_message("只有游戏创建者才能更改游戏状态。", ephemeral=True)
        return

    if status not in ["preparing", "started"]:
        await interaction.response.send_message("无效的状态。请使用 'preparing' 或 'started'。", ephemeral=True)
        return

    game.status = status
    await interaction.response.send_message(f"游戏 {name} 的状态已更新为 {status}。", ephemeral=True)

@tree.command(name="bingo_list", description="列出所有可用的宾果游戏")
async def bingo_list(interaction: discord.Interaction):
    if not games:
        await interaction.response.send_message("当前没有正在进行的宾果游戏。", ephemeral=True)
        return

    embed = discord.Embed(title="可用的宾果游戏", color=discord.Color.blue())
    for name, game in games.items():
        embed.add_field(name=name, value=f"状态: {game.status}\n创建者: <@{game.creator_id}>", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="bingo_join", description="加入一个宾果游戏")
@app_commands.describe(name="游戏名称")
async def bingo_join(interaction: discord.Interaction, name: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if game.status != "preparing":
        await interaction.response.send_message("游戏已经开始，无法加入。", ephemeral=True)
        return

    if interaction.user.id in game.players:
        await interaction.response.send_message("你已经加入过这个游戏了。", ephemeral=True)
        return

    player = game.add_player(interaction.user.id)
    card_image = generate_card_image(player.card, player.marked)

    file = discord.File(card_image, filename=f"{name}_card.png")
    await interaction.response.send_message(f"你已成功加入游戏 {name}! 这是你的宾果卡。", file=file, ephemeral=True)

@tree.command(name="bingo_reroll", description="重新生成你的宾果卡")
@app_commands.describe(name="游戏名称")
async def bingo_reroll(interaction: discord.Interaction, name: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if interaction.user.id not in game.players:
        await interaction.response.send_message("你还没有加入这个游戏。", ephemeral=True)
        return

    if game.status != "preparing":
        await interaction.response.send_message("游戏已经开始，无法重新生成卡片。", ephemeral=True)
        return

    player = game.generate_player_card(interaction.user.id)
    card_image = generate_card_image(player.card, player.marked)

    file = discord.File(card_image, filename=f"{name}_card.png")
    await interaction.response.send_message("你的宾果卡已重新生成。", file=file, ephemeral=True)

@tree.command(name="bingo_mark", description="在你的宾果卡上标记一个词")
@app_commands.describe(name="游戏名称", word="要标记的词")
async def bingo_mark(interaction: discord.Interaction, name: str, word: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if interaction.user.id not in game.players:
        await interaction.response.send_message("你还没有加入这个游戏。", ephemeral=True)
        return

    if game.status != "started":
        await interaction.response.send_message("游戏尚未开始，不能标记词语。", ephemeral=True)
        return

    player = game.players[interaction.user.id]
    found = False
    for r in range(game.dimension):
        for c in range(game.dimension):
            if player.card[r][c] == word:
                player.marked[r][c] = True
                found = True
                break
        if found:
            break

    if not found:
        await interaction.response.send_message(f"在你的卡片上没有找到词语 '{word}'。", ephemeral=True)
        return

    await interaction.response.send_message(f"你已在游戏 {name} 中标记了 '{word}'。", ephemeral=True)

@tree.command(name="bingo_show", description="向其他人展示你的宾果卡")
@app_commands.describe(name="游戏名称")
async def bingo_show(interaction: discord.Interaction, name: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if interaction.user.id not in game.players:
        await interaction.response.send_message("你还没有加入这个游戏。", ephemeral=True)
        return

    player = game.players[interaction.user.id]
    card_image = generate_card_image(player.card, player.marked)

    file = discord.File(card_image, filename=f"{interaction.user.name}_card.png")
    await interaction.response.send_message(f"{interaction.user.mention} 的宾果卡:", file=file)

@tree.command(name="bingo_participants", description="查看宾果游戏的参与者")
@app_commands.describe(name="游戏名称")
async def bingo_participants(interaction: discord.Interaction, name: str):
    if name not in games:
        await interaction.response.send_message(f"游戏 {name} 不存在。", ephemeral=True)
        return

    game = games[name]
    if not game.players:
        await interaction.response.send_message(f"游戏 {name} 还没有参与者。", ephemeral=True)
        return

    embed = discord.Embed(title=f"游戏 '{name}' 的参与者", color=discord.Color.green())
    participants = "\n".join([f"<@{player_id}>" for player_id in game.players])
    embed.description = participants

    await interaction.response.send_message(embed=embed, ephemeral=True)

# 运行机器人
client.run("YOUR_BOT_TOKEN")