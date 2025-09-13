import discord
from bingo_game import Game, Player, games
from bingo_card_generator import generate_card_image

# 在这里我们将定义所有的UI视图 (Views) 和模态框 (Modals)

def create_lobby_embed(game: Game):
    """创建一个游戏大厅的嵌入消息"""
    embed = discord.Embed(
        title=f"🎯 宾果游戏大厅: {game.name}",
        color=0x00ff00 if game.status == "preparing" else 0xffff00
    )
    
    # 游戏状态
    status_text = {
        "preparing": "⏳ 准备中",
        "started": "🎮 游戏进行中",
        "finished": "🏁 游戏已结束"
    }.get(game.status, "❓ 未知状态")
    
    embed.add_field(name="游戏状态", value=status_text, inline=True)
    embed.add_field(name="创建者", value=f"<@{game.creator_id}>", inline=True)
    embed.add_field(name="参与人数", value=f"{len(game.players)}/∞", inline=True)
    
    # 参与者列表
    if game.players:
        players_list = "\n".join([f"• <@{player_id}>" for player_id in game.players.keys()])
        embed.add_field(name="参与者", value=players_list, inline=False)
    else:
        embed.add_field(name="参与者", value="暂无玩家加入", inline=False)
    
    # 词汇数量
    embed.add_field(name="词汇数量", value=f"{len(game.words)} 个词汇", inline=True)
    
    return embed

def create_game_embed(game: Game):
    """创建游戏进行中的嵌入消息"""
    embed = discord.Embed(
        title=f"🎮 宾果游戏进行中: {game.name}",
        color=0x00ff00
    )
    
    embed.add_field(name="游戏状态", value="🎮 游戏进行中", inline=True)
    embed.add_field(name="创建者", value=f"<@{game.creator_id}>", inline=True)
    embed.add_field(name="参与人数", value=f"{len(game.players)}", inline=True)
    
    # 参与者列表
    if game.players:
        players_list = "\n".join([f"• <@{player_id}>" for player_id in game.players.keys()])
        embed.add_field(name="参与者", value=players_list, inline=False)
    
    embed.add_field(name="操作说明", value="点击下方按钮进行游戏操作", inline=False)
    
    return embed

class MarkWordModal(discord.ui.Modal, title="标记单词"):
    """标记单词的模态框"""
    
    def __init__(self, game_name: str):
        super().__init__()
        self.game_name = game_name
    
    word = discord.ui.TextInput(
        label="要标记的单词",
        placeholder="请输入要标记的单词...",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.game_name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game_name]
        user_id = interaction.user.id
        
        if user_id not in game.players:
            await interaction.response.send_message("❌ 你还没有加入这个游戏！", ephemeral=True)
            return
        
        if game.status != "started":
            await interaction.response.send_message("❌ 游戏尚未开始或已结束！", ephemeral=True)
            return
        
        player = game.players[user_id]
        word_to_mark = self.word.value.strip()
        
        # 查找并标记单词
        found = False
        for r in range(game.dimension):
            for c in range(game.dimension):
                if player.card[r][c] == word_to_mark:
                    if player.marked[r][c]:
                        await interaction.response.send_message(f"⚠️ 单词 '{word_to_mark}' 已经被标记过了！", ephemeral=True)
                        return
                    player.marked[r][c] = True
                    found = True
                    break
            if found:
                break
        
        if not found:
            await interaction.response.send_message(f"❌ 在你的卡片上没有找到单词 '{word_to_mark}'！", ephemeral=True)
            return
        
        # 检查是否获胜
        if player.check_bingo():
            await interaction.response.send_message(f"🎉 恭喜！你标记了 '{word_to_mark}' 并获得了宾果！", ephemeral=False)
        else:
            await interaction.response.send_message(f"✅ 成功标记单词 '{word_to_mark}'！", ephemeral=True)

class GameView(discord.ui.View):
    """游戏进行中的视图"""
    
    def __init__(self, game: Game):
        super().__init__(timeout=None)  # 游戏进行中不设超时
        self.game = game
    
    @discord.ui.button(label="🎯 显示我的卡片", style=discord.ButtonStyle.primary)
    async def show_card_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """显示玩家的宾果卡片"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        if user_id not in game.players:
            await interaction.response.send_message("❌ 你还没有加入这个游戏！", ephemeral=True)
            return
        
        player = game.players[user_id]
        
        try:
            # 生成卡片图片
            card_image = generate_card_image(player.card, player.marked)
            file = discord.File(card_image, filename=f"{interaction.user.name}_bingo_card.png")
            
            await interaction.response.send_message(
                f"🎯 这是你在游戏 **{game.name}** 中的宾果卡片：",
                file=file,
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message("❌ 生成卡片图片时出错！", ephemeral=True)
    
    @discord.ui.button(label="✏️ 标记单词", style=discord.ButtonStyle.green)
    async def mark_word_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """标记单词按钮"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        if user_id not in game.players:
            await interaction.response.send_message("❌ 你还没有加入这个游戏！", ephemeral=True)
            return
        
        if game.status != "started":
            await interaction.response.send_message("❌ 游戏尚未开始或已结束！", ephemeral=True)
            return
        
        # 显示标记单词的模态框
        modal = MarkWordModal(self.game.name)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📊 游戏状态", style=discord.ButtonStyle.secondary)
    async def game_status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """显示游戏状态"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        
        embed = discord.Embed(
            title=f"📊 游戏状态: {game.name}",
            color=0x00ff00
        )
        
        embed.add_field(name="游戏状态", value="🎮 进行中", inline=True)
        embed.add_field(name="参与人数", value=f"{len(game.players)}", inline=True)
        embed.add_field(name="词汇总数", value=f"{len(game.words)}", inline=True)
        
        # 显示所有参与者
        if game.players:
            players_info = []
            for player_id in game.players.keys():
                players_info.append(f"• <@{player_id}>")
            embed.add_field(name="参与者", value="\n".join(players_info), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🛑 结束游戏", style=discord.ButtonStyle.danger)
    async def end_game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """结束游戏按钮（仅创建者可用）"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        # 检查是否是创建者
        if user_id != game.creator_id:
            await interaction.response.send_message("❌ 只有游戏创建者才能结束游戏！", ephemeral=True)
            return
        
        # 结束游戏
        game.status = "finished"
        
        # 禁用所有按钮
        for item in self.children:
            item.disabled = True
        
        # 更新消息
        embed = discord.Embed(
            title=f"🏁 游戏已结束: {game.name}",
            description="游戏已被创建者结束。感谢所有参与者！",
            color=0xff9900
        )
        
        # 显示最终参与者
        if game.players:
            players_list = "\n".join([f"• <@{player_id}>" for player_id in game.players.keys()])
            embed.add_field(name="参与者", value=players_list, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"🏁 游戏 **{game.name}** 已结束！感谢大家的参与！", ephemeral=False)

class LobbyView(discord.ui.View):
    """游戏大厅的视图，包含加入、开始、取消等按钮"""
    def __init__(self, game: Game):
        super().__init__(timeout=300)  # 5分钟超时
        self.game = game

    @discord.ui.button(label="🎯 加入游戏", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """加入游戏按钮"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        # 检查游戏状态
        if game.status != "preparing":
            await interaction.response.send_message("❌ 游戏已开始或已结束，无法加入！", ephemeral=True)
            return
        
        # 检查是否已经加入
        if user_id in game.players:
            await interaction.response.send_message("⚠️ 你已经加入了这个游戏！", ephemeral=True)
            return
        
        # 检查是否有足够的词汇
        if len(game.words) < game.dimension * game.dimension:
            await interaction.response.send_message("❌ 游戏词汇不足，无法加入！请等待创建者添加更多词汇。", ephemeral=True)
            return
        
        # 加入游戏
        player = game.add_player(user_id)
        if player:
            # 更新嵌入消息
            embed = create_lobby_embed(game)
            await interaction.response.edit_message(embed=embed, view=self)
            
            # 发送确认消息
            await interaction.followup.send(f"✅ <@{user_id}> 成功加入游戏 **{game.name}**！", ephemeral=False)
        else:
            await interaction.response.send_message("❌ 加入游戏失败！", ephemeral=True)

    @discord.ui.button(label="🚪 退出游戏", style=discord.ButtonStyle.red)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """退出游戏按钮"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        # 检查是否已经加入游戏
        if user_id not in game.players:
            await interaction.response.send_message("⚠️ 你还没有加入这个游戏！", ephemeral=True)
            return
        
        # 检查是否是创建者
        if user_id == game.creator_id:
            await interaction.response.send_message("❌ 创建者不能退出游戏！请使用取消游戏按钮。", ephemeral=True)
            return
        
        # 退出游戏
        if user_id in game.players:
            del game.players[user_id]
            
            # 更新嵌入消息
            embed = create_lobby_embed(game)
            await interaction.response.edit_message(embed=embed, view=self)
            
            # 发送确认消息
            await interaction.followup.send(f"👋 <@{user_id}> 已退出游戏 **{game.name}**！", ephemeral=False)
        else:
            await interaction.response.send_message("❌ 退出游戏失败！", ephemeral=True)

    @discord.ui.button(label="🚀 开始游戏", style=discord.ButtonStyle.primary)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """开始游戏按钮"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        # 检查是否是创建者
        if user_id != game.creator_id:
            await interaction.response.send_message("❌ 只有游戏创建者才能开始游戏！", ephemeral=True)
            return
        
        # 检查游戏状态
        if game.status != "preparing":
            await interaction.response.send_message("❌ 游戏已开始或已结束！", ephemeral=True)
            return
        
        # 检查参与者数量
        if len(game.players) < 1:
            await interaction.response.send_message("❌ 至少需要1名玩家才能开始游戏！", ephemeral=True)
            return
        
        # 检查词汇数量
        if len(game.words) < game.dimension * game.dimension:
            await interaction.response.send_message("❌ 需要足够的词汇才能开始游戏！", ephemeral=True)
            return
        
        # 开始游戏
        game.status = "started"
        
        # 切换到GameView
        embed = create_game_embed(game)
        view = GameView(game)
        
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.followup.send(f"🎮 游戏 **{game.name}** 已开始！\n参与者可以点击按钮查看卡片和标记单词。", ephemeral=False)

    @discord.ui.button(label="❌ 取消游戏", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """取消游戏按钮"""
        if self.game.name not in games:
            await interaction.response.send_message("❌ 游戏不存在！", ephemeral=True)
            return
        
        game = games[self.game.name]
        user_id = interaction.user.id
        
        # 检查是否是创建者
        if user_id != game.creator_id:
            await interaction.response.send_message("❌ 只有游戏创建者才能取消游戏！", ephemeral=True)
            return
        
        # 取消游戏
        del games[self.game.name]
        
        # 禁用所有按钮
        for item in self.children:
            item.disabled = True
        
        # 更新消息
        embed = discord.Embed(
            title=f"❌ 游戏已取消: {self.game.name}",
            description="游戏已被创建者取消。",
            color=0xff0000
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"🗑️ 游戏 **{self.game.name}** 已被取消！", ephemeral=False)