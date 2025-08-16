import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Literal

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

def check_admin_permission(user: discord.Member) -> bool:
    """检查用户是否有管理员权限"""
    return (user.guild_permissions.administrator or 
            user.guild_permissions.manage_guild or
            user.guild_permissions.manage_channels or
            user.id == user.guild.owner_id)

def get_user_stats(user_id: int, guild_id: int, days: Optional[int] = None) -> dict:
    """获取用户的投票统计"""
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    # 构建时间条件
    time_condition = ""
    params = [user_id, guild_id]
    
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        time_condition = "AND timestamp >= ?"
        params.append(cutoff_date.isoformat())
    
    # 获取好票数
    cursor.execute(f'''
        SELECT COUNT(*) FROM votes 
        WHERE target_id = ? AND vote_type = '好票' AND guild_id = ? {time_condition}
    ''', params)
    good_votes = cursor.fetchone()[0]
    
    # 获取坏票数
    cursor.execute(f'''
        SELECT COUNT(*) FROM votes 
        WHERE target_id = ? AND vote_type = '坏票' AND guild_id = ? {time_condition}
    ''', params)
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

def get_leaderboard_data(guild_id: int, days: Optional[int] = None, limit: int = 10):
    """获取排行榜数据"""
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    
    # 构建时间条件
    time_condition = ""
    params = [guild_id]
    
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        time_condition = "AND timestamp >= ?"
        params.append(cutoff_date.isoformat())
    
    # 获取排行榜数据
    cursor.execute(f'''
        SELECT target_id,
               SUM(CASE WHEN vote_type = '好票' THEN 1 ELSE 0 END) as good_votes,
               SUM(CASE WHEN vote_type = '坏票' THEN 1 ELSE 0 END) as bad_votes,
               COUNT(*) as total_votes
        FROM votes 
        WHERE guild_id = ? {time_condition}
        GROUP BY target_id
        HAVING total_votes > 0
        ORDER BY good_votes DESC, total_votes DESC
        LIMIT ?
    ''', params + [limit])
    
    results = cursor.fetchall()
    conn.close()
    return results

@bot.event
async def on_ready():
    """机器人启动事件"""
    print(f'🗳️ 投票机器人 V2 {bot.user} 已启动！')
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
@app_commands.describe(
    用户="要投票的成员",
    票型="选择票型"
)
@app_commands.choices(票型=[
    app_commands.Choice(name="👍 好票", value="好票"),
    app_commands.Choice(name="👎 坏票", value="坏票"),
])
async def vote_command(interaction: discord.Interaction, 
                      用户: discord.Member, 
                      票型: Literal["好票", "坏票"]):
    """投票命令"""
    
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
        vote_emoji = "👍" if 票型 == "好票" else "👎"
        await interaction.response.send_message(
            f"✅ 已为 **{用户.display_name}** 投出{vote_emoji}{票型}！\n"
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
@app_commands.describe(
    用户="要查看统计的成员",
    周期="统计周期"
)
@app_commands.choices(周期=[
    app_commands.Choice(name="📊 全部时间", value="all"),
    app_commands.Choice(name="📅 最近半月（15天）", value="15"),
    app_commands.Choice(name="📆 最近一月（30天）", value="30"),
    app_commands.Choice(name="🗓️ 最近三月（90天）", value="90"),
])
async def stats_command(interaction: discord.Interaction, 
                       用户: Optional[discord.Member] = None,
                       周期: Literal["all", "15", "30", "90"] = "all"):
    """统计命令 - 仅管理员可用"""
    
    # 检查权限
    if not check_admin_permission(interaction.user):
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！\n"
            "📋 需要以下权限之一：管理员、管理服务器、管理频道、或服务器所有者", 
            ephemeral=True
        )
        return
    
    # 默认查看命令执行者
    if 用户 is None:
        用户 = interaction.user
    
    # 获取统计数据
    days = None if 周期 == "all" else int(周期)
    stats = get_user_stats(用户.id, interaction.guild.id, days)
    
    # 创建统计嵌入消息
    period_text = "全部时间" if 周期 == "all" else f"最近{周期}天"
    
    embed = discord.Embed(
        title=f"📊 {用户.display_name} 的投票统计",
        description=f"统计周期：**{period_text}**",
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
@app_commands.describe(
    周期="排行榜周期",
    显示数量="显示前几名（最多20名）"
)
@app_commands.choices(周期=[
    app_commands.Choice(name="🏆 累计总榜", value="all"),
    app_commands.Choice(name="📅 半月榜（15天）", value="15"),
    app_commands.Choice(name="📆 月榜（30天）", value="30"),
    app_commands.Choice(name="🗓️ 季榜（90天）", value="90"),
])
async def leaderboard_command(interaction: discord.Interaction,
                             周期: Literal["all", "15", "30", "90"] = "all",
                             显示数量: int = 10):
    """排行榜命令 - 仅管理员可用"""
    
    # 检查权限
    if not check_admin_permission(interaction.user):
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！\n"
            "📋 需要以下权限之一：管理员、管理服务器、管理频道、或服务器所有者", 
            ephemeral=True
        )
        return
    
    # 限制显示数量
    if 显示数量 > 20:
        显示数量 = 20
    elif 显示数量 < 1:
        显示数量 = 10
    
    # 获取排行榜数据
    days = None if 周期 == "all" else int(周期)
    results = get_leaderboard_data(interaction.guild.id, days, 显示数量)
    
    if not results:
        period_text = "累计总榜" if 周期 == "all" else f"最近{周期}天"
        await interaction.response.send_message(
            f"📊 {period_text}还没有投票记录！", 
            ephemeral=True
        )
        return
    
    # 创建排行榜嵌入消息
    period_text = "🏆 累计总榜" if 周期 == "all" else f"📅 最近{周期}天排行榜"
    
    embed = discord.Embed(
        title=f"{period_text}",
        description=f"根据好票数量排序（前{len(results)}名）",
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
        
        # 奖牌图标
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"**{i}.**"
        
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
        # 格式化时间
        time_str = datetime.fromisoformat(timestamp).strftime("%m-%d %H:%M")
        votes_text += f"{vote_emoji} {user_name} - {vote_type} `{time_str}`\n"
    
    embed.description = votes_text
    embed.set_footer(text="💡 只有你能看到这些信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="vote_help", description="查看投票机器人使用帮助")
async def vote_help_command(interaction: discord.Interaction):
    """帮助命令"""
    
    embed = discord.Embed(
        title="🗳️ 投票机器人使用指南",
        description="一个匿名投票系统，保护用户隐私",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    # 普通用户命令
    embed.add_field(
        name="👥 普通用户命令",
        value=(
            "`/vote @用户 票型` - 给其他成员投票\n"
            "`/my_votes` - 查看自己的投票历史\n"
            "`/vote_help` - 查看帮助信息"
        ),
        inline=False
    )
    
    # 管理员命令
    embed.add_field(
        name="👑 管理员命令",
        value=(
            "`/stats @用户 [周期]` - 查看用户投票统计\n"
            "`/leaderboard [周期] [数量]` - 查看排行榜"
        ),
        inline=False
    )
    
    # 功能特点
    embed.add_field(
        name="✨ 功能特点",
        value=(
            "🔒 **完全匿名** - 投票者身份保密\n"
            "📊 **多周期统计** - 支持半月/月/季度/总榜\n"
            "👑 **管理员权限** - 只有管理员能查看统计\n"
            "🔄 **可修改投票** - 可以改变之前的投票"
        ),
        inline=False
    )
    
    embed.set_footer(text="💡 投票完全匿名，只有管理员能查看统计数据")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """错误处理"""
    print(f'命令错误: {error}')

if __name__ == '__main__':
    try:
        print("🗳️ 正在启动投票机器人 V2...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ 错误：无效的机器人令牌。请检查BOT_TOKEN设置。")
    except Exception as e:
        print(f"❌ 启动机器人时发生错误: {e}")
