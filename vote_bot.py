import discord
from discord.ext import commands
import sqlite3
import os
from datetime import datetime
from typing import Optional

# 配置
BOT_TOKEN = os.getenv('VOTE_BOT_TOKEN', "你的投票机器人TOKEN")

# 创建机器人实例
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 数据库初始化
def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    # 创建投票表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            vote_type TEXT NOT NULL,
            guild_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(voter_id, target_id, guild_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int, guild_id: int) -> dict:
    """获取用户的投票统计"""
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    # 获取好票数
    cursor.execute('''
        SELECT COUNT(*) FROM votes 
        WHERE target_id = ? AND vote_type = '好票' AND guild_id = ?
    ''', (user_id, guild_id))
    good_votes = cursor.fetchone()[0]
    
    # 获取坏票数
    cursor.execute('''
        SELECT COUNT(*) FROM votes 
        WHERE target_id = ? AND vote_type = '坏票' AND guild_id = ?
    ''', (user_id, guild_id))
    bad_votes = cursor.fetchone()[0]
    
    conn.close()
    return {'good_votes': good_votes, 'bad_votes': bad_votes}

def cast_vote(voter_id: int, target_id: int, vote_type: str, guild_id: int) -> bool:
    """投票功能"""
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    try:
        # 使用 INSERT OR REPLACE 来处理重复投票
        cursor.execute('''
            INSERT OR REPLACE INTO votes (voter_id, target_id, vote_type, guild_id)
            VALUES (?, ?, ?, ?)
        ''', (voter_id, target_id, vote_type, guild_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"投票错误: {e}")
        conn.close()
        return False

@bot.event
async def on_ready():
    """机器人启动事件"""
    print(f'🗳️ 投票机器人 {bot.user} 已启动！')
    print(f'机器人ID: {bot.user.id}')
    print('-----')
    
    # 初始化数据库
    init_database()
    
    # 同步斜杠命令
    try:
        synced = await bot.tree.sync()
        print(f"同步了 {len(synced)} 个斜杠命令")
    except Exception as e:
        print(f"同步命令失败: {e}")

@bot.tree.command(name="vote", description="给其他成员投票（好票或坏票）")
async def vote_command(interaction: discord.Interaction, 
                      用户: discord.Member, 
                      票型: str):
    """投票命令"""
    
    # 验证票型
    if 票型 not in ['好票', '坏票']:
        await interaction.response.send_message(
            "❌ 请选择正确的票型：好票 或 坏票", 
            ephemeral=True
        )
        return
    
    # 检查是否给自己投票
    if interaction.user.id == 用户.id:
        await interaction.response.send_message(
            "❌ 不能给自己投票哦！", 
            ephemeral=True
        )
        return
    
    # 检查目标是否是机器人
    if 用户.bot:
        await interaction.response.send_message(
            "❌ 不能给机器人投票！", 
            ephemeral=True
        )
        return
    
    # 执行投票
    success = cast_vote(
        interaction.user.id, 
        用户.id, 
        票型, 
        interaction.guild.id
    )
    
    if success:
        await interaction.response.send_message(
            f"✅ 已为 {用户.display_name} 投出{票型}！\n"
            f"💡 投票完全匿名，只有管理员能查看统计数据。", 
            ephemeral=True
        )
        
        # 在控制台记录（用于调试）
        print(f"{interaction.user.name} 给 {用户.name} 投了{票型}")
    else:
        await interaction.response.send_message(
            "❌ 投票失败，请稍后再试。", 
            ephemeral=True
        )

@bot.tree.command(name="stats", description="查看成员的投票统计（仅管理员）")
async def stats_command(interaction: discord.Interaction, 
                       用户: Optional[discord.Member] = None):
    """统计命令 - 仅管理员可用"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    # 默认查看命令执行者
    if 用户 is None:
        用户 = interaction.user
    
    # 获取统计数据
    stats = get_user_stats(用户.id, interaction.guild.id)
    
    # 创建统计嵌入消息
    embed = discord.Embed(
        title=f"📊 {用户.display_name} 的投票统计",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="👍 好票", 
        value=f"**{stats['good_votes']}** 票", 
        inline=True
    )
    
    embed.add_field(
        name="👎 坏票", 
        value=f"**{stats['bad_votes']}** 票", 
        inline=True
    )
    
    total_votes = stats['good_votes'] + stats['bad_votes']
    embed.add_field(
        name="📈 总票数", 
        value=f"**{total_votes}** 票", 
        inline=True
    )
    
    if total_votes > 0:
        good_percentage = (stats['good_votes'] / total_votes) * 100
        embed.add_field(
            name="✨ 好评率", 
            value=f"**{good_percentage:.1f}%**", 
            inline=False
        )
    
    embed.set_thumbnail(url=用户.display_avatar.url)
    embed.set_footer(text="💡 投票数据仅管理员可见")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="leaderboard", description="查看服务器投票排行榜（仅管理员）")
async def leaderboard_command(interaction: discord.Interaction):
    """排行榜命令 - 仅管理员可用"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    # 获取排行榜数据
    cursor.execute('''
        SELECT target_id,
               SUM(CASE WHEN vote_type = '好票' THEN 1 ELSE 0 END) as good_votes,
               SUM(CASE WHEN vote_type = '坏票' THEN 1 ELSE 0 END) as bad_votes,
               COUNT(*) as total_votes
        FROM votes 
        WHERE guild_id = ?
        GROUP BY target_id
        HAVING total_votes > 0
        ORDER BY good_votes DESC, total_votes DESC
        LIMIT 10
    ''', (interaction.guild.id,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        await interaction.response.send_message(
            "📊 还没有投票记录！", 
            ephemeral=True
        )
        return
    
    # 创建排行榜嵌入消息
    embed = discord.Embed(
        title="🏆 服务器投票排行榜",
        description="根据好票数量排序（前10名）",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    leaderboard_text = ""
    for i, (user_id, good_votes, bad_votes, total_votes) in enumerate(results, 1):
        try:
            user = await bot.fetch_user(user_id)
            user_name = user.display_name if hasattr(user, 'display_name') else user.name
        except:
            user_name = f"用户{user_id}"
        
        good_percentage = (good_votes / total_votes) * 100 if total_votes > 0 else 0
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        leaderboard_text += f"{medal} **{user_name}**\n"
        leaderboard_text += f"　　👍 {good_votes} | 👎 {bad_votes} | ✨ {good_percentage:.1f}%\n\n"
    
    embed.description = leaderboard_text
    embed.set_footer(text="💡 排行榜数据仅管理员可见")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="my_votes", description="查看我投出的票（仅自己可见）")
async def my_votes_command(interaction: discord.Interaction):
    """查看自己的投票历史"""
    
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT target_id, vote_type, timestamp
        FROM votes 
        WHERE voter_id = ? AND guild_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (interaction.user.id, interaction.guild.id))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        await interaction.response.send_message(
            "📊 你还没有投过票！", 
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="📝 我的投票记录",
        description=f"最近 {len(results)} 条投票记录",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    votes_text = ""
    for target_id, vote_type, timestamp in results:
        try:
            user = await bot.fetch_user(target_id)
            user_name = user.display_name if hasattr(user, 'display_name') else user.name
        except:
            user_name = f"用户{target_id}"
        
        vote_emoji = "👍" if vote_type == "好票" else "👎"
        votes_text += f"{vote_emoji} {user_name} - {vote_type}\n"
    
    embed.description = votes_text
    embed.set_footer(text="💡 只有你能看到这些信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """错误处理"""
    print(f'命令错误: {error}')

if __name__ == '__main__':
    try:
        print("🗳️ 正在启动投票机器人...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ 错误：无效的机器人令牌。请检查BOT_TOKEN设置。")
    except Exception as e:
        print(f"❌ 启动机器人时发生错误: {e}")
