import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime
from typing import Optional, Literal
import json

# 配置
BOT_TOKEN = os.getenv('DM_TRACKER_BOT_TOKEN', "你的私信追踪机器人TOKEN")

# 创建机器人实例
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True  # 重要：需要私信权限

bot = commands.Bot(command_prefix='!', intents=intents)

# 数据库初始化
def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect('dm_users.db')
    cursor = conn.cursor()
    
    # 创建私信用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dm_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT,
            first_message_time DATETIME NOT NULL,
            last_message_time DATETIME NOT NULL,
            total_messages INTEGER DEFAULT 1,
            last_message_content TEXT,
            avatar_url TEXT
        )
    ''')
    
    # 创建私信消息记录表（可选，用于详细记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dm_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message_id INTEGER UNIQUE,
            FOREIGN KEY (user_id) REFERENCES dm_users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def record_dm_user(user: discord.User, message_content: str, message_id: int):
    """记录私信用户信息"""
    conn = sqlite3.connect('dm_users.db')
    cursor = conn.cursor()
    
    try:
        current_time = datetime.now()
        
        # 检查用户是否已存在
        cursor.execute('SELECT total_messages FROM dm_users WHERE user_id = ?', (user.id,))
        result = cursor.fetchone()
        
        if result:
            # 更新现有用户
            new_total = result[0] + 1
            cursor.execute('''
                UPDATE dm_users 
                SET username = ?, display_name = ?, last_message_time = ?, 
                    total_messages = ?, last_message_content = ?, avatar_url = ?
                WHERE user_id = ?
            ''', (
                user.name,
                user.display_name,
                current_time,
                new_total,
                message_content[:200],  # 限制长度
                str(user.display_avatar.url),
                user.id
            ))
        else:
            # 新增用户
            cursor.execute('''
                INSERT INTO dm_users 
                (user_id, username, display_name, first_message_time, last_message_time, 
                 total_messages, last_message_content, avatar_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id,
                user.name,
                user.display_name,
                current_time,
                current_time,
                1,
                message_content[:200],
                str(user.display_avatar.url)
            ))
        
        # 记录消息详情（可选）
        cursor.execute('''
            INSERT OR IGNORE INTO dm_messages (user_id, message_content, message_id)
            VALUES (?, ?, ?)
        ''', (user.id, message_content[:500], message_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"记录私信用户失败: {e}")
        return False
    finally:
        conn.close()

def get_dm_users_list(limit: int = 50, sort_by: str = "last_message") -> list:
    """获取私信用户列表"""
    conn = sqlite3.connect('dm_users.db')
    cursor = conn.cursor()
    
    # 根据排序方式构建查询
    order_by_map = {
        "last_message": "last_message_time DESC",
        "first_message": "first_message_time ASC",
        "most_messages": "total_messages DESC",
        "username": "username ASC"
    }
    
    order_by = order_by_map.get(sort_by, "last_message_time DESC")
    
    cursor.execute(f'''
        SELECT user_id, username, display_name, first_message_time, 
               last_message_time, total_messages, last_message_content, avatar_url
        FROM dm_users 
        ORDER BY {order_by}
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_dm_statistics() -> dict:
    """获取私信统计信息"""
    conn = sqlite3.connect('dm_users.db')
    cursor = conn.cursor()
    
    # 总用户数
    cursor.execute('SELECT COUNT(*) FROM dm_users')
    total_users = cursor.fetchone()[0]
    
    # 总消息数
    cursor.execute('SELECT SUM(total_messages) FROM dm_users')
    total_messages = cursor.fetchone()[0] or 0
    
    # 今天的新用户
    today = datetime.now().date()
    cursor.execute('SELECT COUNT(*) FROM dm_users WHERE DATE(first_message_time) = ?', (today,))
    today_new_users = cursor.fetchone()[0]
    
    # 今天的消息数
    cursor.execute('SELECT COUNT(*) FROM dm_messages WHERE DATE(timestamp) = ?', (today,))
    today_messages = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_messages': total_messages,
        'today_new_users': today_new_users,
        'today_messages': today_messages
    }

@bot.event
async def on_ready():
    """机器人启动事件"""
    print(f'📨 私信追踪机器人 {bot.user} 已启动！')
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

@bot.event
async def on_message(message):
    """监听所有消息，包括私信"""
    
    # 忽略机器人自己的消息
    if message.author.bot:
        return
    
    # 检查是否是私信
    if isinstance(message.channel, discord.DMChannel):
        # 记录私信用户
        success = record_dm_user(message.author, message.content, message.id)
        
        if success:
            print(f"📨 收到来自 {message.author.name} 的私信: {message.content[:50]}...")
        
        # 可选：自动回复私信
        try:
            await message.reply(
                "📨 收到你的私信！\n"
                "💡 如需帮助，请使用服务器中的命令或联系管理员。"
            )
        except:
            pass  # 如果回复失败，不影响记录功能
    
    # 处理其他命令
    await bot.process_commands(message)

@bot.tree.command(name="dm_list", description="查看所有私信用户列表（仅机器人所有者）")
@app_commands.describe(
    排序方式="选择排序方式",
    显示数量="显示用户数量（最多100）"
)
@app_commands.choices(排序方式=[
    app_commands.Choice(name="📅 最新私信", value="last_message"),
    app_commands.Choice(name="🕐 首次私信", value="first_message"),
    app_commands.Choice(name="💬 消息最多", value="most_messages"),
    app_commands.Choice(name="🔤 用户名", value="username"),
])
async def dm_list_command(interaction: discord.Interaction,
                         排序方式: Literal["last_message", "first_message", "most_messages", "username"] = "last_message",
                         显示数量: int = 20):
    """查看私信用户列表 - 仅机器人所有者可用"""
    
    # 检查是否是机器人所有者或应用程序所有者
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message(
            "❌ 此命令仅限机器人所有者使用！", 
            ephemeral=True
        )
        return
    
    # 限制显示数量
    if 显示数量 > 100:
        显示数量 = 100
    elif 显示数量 < 1:
        显示数量 = 20
    
    # 获取用户列表
    users = get_dm_users_list(显示数量, 排序方式)
    
    if not users:
        await interaction.response.send_message(
            "📨 还没有私信记录！", 
            ephemeral=True
        )
        return
    
    # 创建用户列表嵌入消息
    sort_names = {
        "last_message": "📅 最新私信",
        "first_message": "🕐 首次私信", 
        "most_messages": "💬 消息最多",
        "username": "🔤 用户名"
    }
    
    embed = discord.Embed(
        title="📨 私信用户列表",
        description=f"排序方式：{sort_names.get(排序方式, '最新私信')} | 显示前 {len(users)} 位",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    user_list_text = ""
    for i, (user_id, username, display_name, first_time, last_time, total_msg, last_content, avatar_url) in enumerate(users, 1):
        
        # 格式化时间
        last_time_dt = datetime.fromisoformat(last_time)
        last_time_str = last_time_dt.strftime("%m-%d %H:%M")
        
        # 截取最后消息内容
        preview = last_content[:30] + "..." if last_content and len(last_content) > 30 else last_content or "无"
        
        user_list_text += (
            f"**{i}.** `{username}`\n"
            f"　　💬 {total_msg} 条消息 | 📅 {last_time_str}\n"
            f"　　💭 {preview}\n\n"
        )
        
        # 避免消息过长
        if len(user_list_text) > 3500:
            user_list_text += f"... 还有 {len(users) - i} 位用户"
            break
    
    embed.description = user_list_text
    embed.set_footer(text="💡 仅机器人所有者可见此信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dm_stats", description="查看私信统计信息（仅机器人所有者）")
async def dm_stats_command(interaction: discord.Interaction):
    """查看私信统计 - 仅机器人所有者可用"""
    
    # 检查权限
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message(
            "❌ 此命令仅限机器人所有者使用！", 
            ephemeral=True
        )
        return
    
    # 获取统计数据
    stats = get_dm_statistics()
    
    # 创建统计嵌入消息
    embed = discord.Embed(
        title="📊 私信统计信息",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="👥 总用户数",
        value=f"**{stats['total_users']}** 位用户",
        inline=True
    )
    
    embed.add_field(
        name="💬 总消息数",
        value=f"**{stats['total_messages']}** 条消息",
        inline=True
    )
    
    embed.add_field(
        name="🆕 今日新用户",
        value=f"**{stats['today_new_users']}** 位",
        inline=True
    )
    
    embed.add_field(
        name="📅 今日消息数",
        value=f"**{stats['today_messages']}** 条",
        inline=True
    )
    
    if stats['total_users'] > 0:
        avg_messages = stats['total_messages'] / stats['total_users']
        embed.add_field(
            name="📈 平均消息数",
            value=f"**{avg_messages:.1f}** 条/用户",
            inline=True
        )
    
    embed.set_footer(text="💡 仅机器人所有者可见此信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dm_search", description="搜索特定用户的私信记录（仅机器人所有者）")
@app_commands.describe(关键词="搜索用户名或显示名")
async def dm_search_command(interaction: discord.Interaction, 关键词: str):
    """搜索私信用户 - 仅机器人所有者可用"""
    
    # 检查权限
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message(
            "❌ 此命令仅限机器人所有者使用！", 
            ephemeral=True
        )
        return
    
    conn = sqlite3.connect('dm_users.db')
    cursor = conn.cursor()
    
    # 搜索用户
    search_term = f"%{关键词}%"
    cursor.execute('''
        SELECT user_id, username, display_name, first_message_time, 
               last_message_time, total_messages, last_message_content
        FROM dm_users 
        WHERE username LIKE ? OR display_name LIKE ?
        ORDER BY last_message_time DESC
        LIMIT 10
    ''', (search_term, search_term))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        await interaction.response.send_message(
            f"🔍 没有找到包含 '{关键词}' 的用户！", 
            ephemeral=True
        )
        return
    
    # 创建搜索结果
    embed = discord.Embed(
        title=f"🔍 搜索结果：'{关键词}'",
        description=f"找到 {len(results)} 位用户",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    for user_id, username, display_name, first_time, last_time, total_msg, last_content in results:
        last_time_dt = datetime.fromisoformat(last_time)
        last_time_str = last_time_dt.strftime("%Y-%m-%d %H:%M")
        
        preview = last_content[:50] + "..." if last_content and len(last_content) > 50 else last_content or "无"
        
        embed.add_field(
            name=f"👤 {username}",
            value=(
                f"💬 {total_msg} 条消息\n"
                f"📅 最后消息：{last_time_str}\n"
                f"💭 {preview}"
            ),
            inline=False
        )
    
    embed.set_footer(text="💡 仅机器人所有者可见此信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dm_help", description="查看私信追踪机器人帮助")
async def dm_help_command(interaction: discord.Interaction):
    """帮助命令"""
    
    embed = discord.Embed(
        title="📨 私信追踪机器人帮助",
        description="自动记录和管理所有私信用户",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🤖 机器人功能",
        value=(
            "• 自动记录所有私信用户\n"
            "• 统计私信消息数量和时间\n"
            "• 提供用户列表和搜索功能\n"
            "• 自动回复私信消息"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👑 所有者命令",
        value=(
            "`/dm_list` - 查看私信用户列表\n"
            "`/dm_stats` - 查看私信统计信息\n"
            "`/dm_search` - 搜索特定用户\n"
            "`/dm_help` - 查看帮助信息"
        ),
        inline=False
    )
    
    embed.add_field(
        name="✨ 特色功能",
        value=(
            "🔒 **隐私保护** - 只有机器人所有者能查看\n"
            "📊 **多种排序** - 按时间、消息数等排序\n"
            "🔍 **搜索功能** - 快速找到特定用户\n"
            "📈 **统计报告** - 详细的数据统计"
        ),
        inline=False
    )
    
    embed.set_footer(text="💡 私信会被自动记录和回复")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """错误处理"""
    print(f'命令错误: {error}')

if __name__ == '__main__':
    try:
        print("📨 正在启动私信追踪机器人...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ 错误：无效的机器人令牌。请检查BOT_TOKEN设置。")
    except Exception as e:
        print(f"❌ 启动机器人时发生错误: {e}")
