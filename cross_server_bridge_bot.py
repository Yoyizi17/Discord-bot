import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import json
import aiohttp
from datetime import datetime
from typing import Optional, Dict, List
import asyncio

# 配置
BOT_TOKEN = os.getenv('BRIDGE_BOT_TOKEN', "你的跨服桥接机器人TOKEN")

# 创建机器人实例
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 数据库初始化
def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect('bridge_config.db')
    cursor = conn.cursor()
    
    # 创建桥接配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bridge_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bridge_name TEXT UNIQUE NOT NULL,
            source_guild_id INTEGER NOT NULL,
            source_channel_id INTEGER NOT NULL,
            target_guild_id INTEGER NOT NULL,
            target_channel_id INTEGER NOT NULL,
            webhook_url TEXT,
            is_enabled BOOLEAN DEFAULT TRUE,
            created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            admin_user_id INTEGER
        )
    ''')
    
    # 创建消息转发记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forwarded_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bridge_name TEXT NOT NULL,
            original_message_id INTEGER NOT NULL,
            forwarded_message_id INTEGER,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_bridge_configs() -> List[Dict]:
    """获取所有桥接配置"""
    conn = sqlite3.connect('bridge_config.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT bridge_name, source_guild_id, source_channel_id, 
               target_guild_id, target_channel_id, webhook_url, is_enabled
        FROM bridge_configs 
        WHERE is_enabled = TRUE
    ''')
    
    configs = []
    for row in cursor.fetchall():
        configs.append({
            'bridge_name': row[0],
            'source_guild_id': row[1],
            'source_channel_id': row[2],
            'target_guild_id': row[3],
            'target_channel_id': row[4],
            'webhook_url': row[5],
            'is_enabled': row[6]
        })
    
    conn.close()
    return configs

def save_bridge_config(bridge_name: str, source_guild_id: int, source_channel_id: int,
                      target_guild_id: int, target_channel_id: int, webhook_url: str, admin_user_id: int):
    """保存桥接配置"""
    conn = sqlite3.connect('bridge_config.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO bridge_configs 
        (bridge_name, source_guild_id, source_channel_id, target_guild_id, 
         target_channel_id, webhook_url, admin_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (bridge_name, source_guild_id, source_channel_id, target_guild_id, 
          target_channel_id, webhook_url, admin_user_id))
    
    conn.commit()
    conn.close()

def log_forwarded_message(bridge_name: str, original_msg_id: int, forwarded_msg_id: int,
                         author_id: int, author_name: str, content: str):
    """记录转发的消息"""
    conn = sqlite3.connect('bridge_config.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO forwarded_messages 
        (bridge_name, original_message_id, forwarded_message_id, author_id, author_name, content)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (bridge_name, original_msg_id, forwarded_msg_id, author_id, author_name, content[:500]))
    
    conn.commit()
    conn.close()

async def create_webhook_if_needed(channel: discord.TextChannel, webhook_name: str = "跨服桥接") -> str:
    """为频道创建webhook"""
    try:
        # 检查是否已有webhook
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == webhook_name:
                return webhook.url
        
        # 创建新webhook
        webhook = await channel.create_webhook(name=webhook_name)
        return webhook.url
    except Exception as e:
        print(f"创建webhook失败: {e}")
        return None

async def send_webhook_message(webhook_url: str, content: str, username: str, avatar_url: str, embeds: List = None):
    """通过webhook发送消息"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                'content': content,
                'username': username,
                'avatar_url': avatar_url
            }
            
            if embeds:
                payload['embeds'] = embeds
            
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get('id')
                else:
                    print(f"Webhook发送失败: {response.status}")
                    return None
    except Exception as e:
        print(f"发送webhook消息失败: {e}")
        return None

@bot.event
async def on_ready():
    """机器人启动事件"""
    print(f'🌉 跨服桥接机器人 {bot.user} 已启动！')
    print(f'机器人ID: {bot.user.id}')
    print(f'已连接到 {len(bot.guilds)} 个服务器')
    print('-----')
    
    # 初始化数据库
    init_database()
    
    # 同步斜杠命令
    try:
        synced = await bot.tree.sync()
        print(f"同步了 {len(synced)} 个斜杠命令")
    except Exception as e:
        print(f"同步命令失败: {e}")
    
    # 加载桥接配置
    configs = get_bridge_configs()
    print(f"加载了 {len(configs)} 个桥接配置")

@bot.event
async def on_message(message):
    """消息监听事件"""
    # 忽略机器人消息和系统消息
    if message.author.bot or message.type != discord.MessageType.default:
        return
    
    # 获取桥接配置
    configs = get_bridge_configs()
    
    for config in configs:
        # 检查是否是源频道的消息
        if (message.guild.id == config['source_guild_id'] and 
            message.channel.id == config['source_channel_id']):
            
            await forward_message(message, config)
    
    # 处理其他命令
    await bot.process_commands(message)

async def forward_message(message: discord.Message, config: Dict):
    """转发消息到目标频道"""
    try:
        # 获取目标频道
        target_guild = bot.get_guild(config['target_guild_id'])
        if not target_guild:
            print(f"无法找到目标服务器: {config['target_guild_id']}")
            return
        
        target_channel = target_guild.get_channel(config['target_channel_id'])
        if not target_channel:
            print(f"无法找到目标频道: {config['target_channel_id']}")
            return
        
        # 准备用户信息
        author = message.author
        username = f"{author.display_name}"
        avatar_url = str(author.display_avatar.url)
        
        # 准备消息内容
        content = message.content
        
        # 处理附件
        embeds = []
        if message.attachments:
            for attachment in message.attachments:
                embed = discord.Embed()
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    embed.set_image(url=attachment.url)
                else:
                    embed.add_field(
                        name="📎 附件", 
                        value=f"[{attachment.filename}]({attachment.url})",
                        inline=False
                    )
                embeds.append(embed.to_dict())
        
        # 处理嵌入消息
        if message.embeds:
            for embed in message.embeds:
                embeds.append(embed.to_dict())
        
        # 添加来源信息
        source_info = f"\n\n*📍 来自: {message.guild.name} #{message.channel.name}*"
        if content:
            content += source_info
        else:
            content = source_info
        
        # 获取或创建webhook
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            webhook_url = await create_webhook_if_needed(target_channel)
            if webhook_url:
                # 更新配置中的webhook URL
                conn = sqlite3.connect('bridge_config.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE bridge_configs 
                    SET webhook_url = ? 
                    WHERE bridge_name = ?
                ''', (webhook_url, config['bridge_name']))
                conn.commit()
                conn.close()
        
        if not webhook_url:
            print(f"无法创建webhook for {config['bridge_name']}")
            return
        
        # 发送消息
        forwarded_msg_id = await send_webhook_message(
            webhook_url, content, username, avatar_url, embeds
        )
        
        if forwarded_msg_id:
            # 记录转发消息
            log_forwarded_message(
                config['bridge_name'], 
                message.id, 
                forwarded_msg_id,
                author.id, 
                author.name, 
                message.content
            )
            
            print(f"✅ 消息已转发: {config['bridge_name']} | {author.name}: {content[:50]}...")
        
    except Exception as e:
        print(f"转发消息失败: {e}")

@bot.tree.command(name="bridge_add", description="添加跨服桥接配置（仅管理员）")
@app_commands.describe(
    桥接名称="桥接配置的名称",
    源服务器id="源服务器ID",
    源频道id="源频道ID", 
    目标服务器id="目标服务器ID",
    目标频道id="目标频道ID"
)
async def bridge_add_command(interaction: discord.Interaction,
                           桥接名称: str,
                           源服务器id: str,
                           源频道id: str,
                           目标服务器id: str,
                           目标频道id: str):
    """添加桥接配置 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    try:
        # 验证ID格式
        source_guild_id = int(源服务器id)
        source_channel_id = int(源频道id)
        target_guild_id = int(目标服务器id)
        target_channel_id = int(目标频道id)
        
        # 验证服务器和频道是否存在
        source_guild = bot.get_guild(source_guild_id)
        target_guild = bot.get_guild(target_guild_id)
        
        if not source_guild:
            await interaction.response.send_message(
                f"❌ 无法找到源服务器 ID: {源服务器id}",
                ephemeral=True
            )
            return
            
        if not target_guild:
            await interaction.response.send_message(
                f"❌ 无法找到目标服务器 ID: {目标服务器id}",
                ephemeral=True
            )
            return
        
        source_channel = source_guild.get_channel(source_channel_id)
        target_channel = target_guild.get_channel(target_channel_id)
        
        if not source_channel:
            await interaction.response.send_message(
                f"❌ 无法找到源频道 ID: {源频道id}",
                ephemeral=True
            )
            return
            
        if not target_channel:
            await interaction.response.send_message(
                f"❌ 无法找到目标频道 ID: {目标频道id}",
                ephemeral=True
            )
            return
        
        # 创建webhook
        webhook_url = await create_webhook_if_needed(target_channel, f"桥接-{桥接名称}")
        
        if not webhook_url:
            await interaction.response.send_message(
                f"❌ 无法为目标频道创建webhook！请检查机器人权限。",
                ephemeral=True
            )
            return
        
        # 保存配置
        save_bridge_config(
            桥接名称, source_guild_id, source_channel_id,
            target_guild_id, target_channel_id, webhook_url, interaction.user.id
        )
        
        # 创建成功消息
        embed = discord.Embed(
            title="✅ 桥接配置已添加",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 配置信息",
            value=(
                f"**桥接名称：** {桥接名称}\n"
                f"**源频道：** {source_guild.name} #{source_channel.name}\n"
                f"**目标频道：** {target_guild.name} #{target_channel.name}"
            ),
            inline=False
        )
        
        embed.set_footer(text="桥接已激活，消息将自动转发")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except ValueError:
        await interaction.response.send_message(
            "❌ 无效的ID格式！请确保输入的是数字ID。",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 添加桥接配置失败：{e}",
            ephemeral=True
        )

@bot.tree.command(name="bridge_list", description="查看所有桥接配置（仅管理员）")
async def bridge_list_command(interaction: discord.Interaction):
    """查看桥接列表 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    configs = get_bridge_configs()
    
    if not configs:
        await interaction.response.send_message(
            "📋 还没有配置任何桥接！",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🌉 跨服桥接配置列表",
        description=f"当前活跃的桥接数量: {len(configs)}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for config in configs:
        source_guild = bot.get_guild(config['source_guild_id'])
        target_guild = bot.get_guild(config['target_guild_id'])
        source_channel = source_guild.get_channel(config['source_channel_id']) if source_guild else None
        target_channel = target_guild.get_channel(config['target_channel_id']) if target_guild else None
        
        source_name = f"{source_guild.name} #{source_channel.name}" if source_guild and source_channel else "未知"
        target_name = f"{target_guild.name} #{target_channel.name}" if target_guild and target_channel else "未知"
        
        status = "🟢 活跃" if config['is_enabled'] else "🔴 禁用"
        
        embed.add_field(
            name=f"🌉 {config['bridge_name']}",
            value=(
                f"**源频道：** {source_name}\n"
                f"**目标频道：** {target_name}\n"
                f"**状态：** {status}"
            ),
            inline=False
        )
    
    embed.set_footer(text="使用 /bridge_remove 删除桥接")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bridge_remove", description="删除桥接配置（仅管理员）")
@app_commands.describe(桥接名称="要删除的桥接配置名称")
async def bridge_remove_command(interaction: discord.Interaction, 桥接名称: str):
    """删除桥接配置 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    try:
        conn = sqlite3.connect('bridge_config.db')
        cursor = conn.cursor()
        
        # 检查桥接是否存在
        cursor.execute('SELECT * FROM bridge_configs WHERE bridge_name = ?', (桥接名称,))
        if not cursor.fetchone():
            await interaction.response.send_message(
                f"❌ 找不到名为 '{桥接名称}' 的桥接配置！",
                ephemeral=True
            )
            conn.close()
            return
        
        # 删除配置
        cursor.execute('DELETE FROM bridge_configs WHERE bridge_name = ?', (桥接名称,))
        conn.commit()
        conn.close()
        
        await interaction.response.send_message(
            f"✅ 桥接配置 '{桥接名称}' 已删除！",
            ephemeral=True
        )
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 删除桥接配置失败：{e}",
            ephemeral=True
        )

@bot.tree.command(name="bridge_stats", description="查看桥接统计信息（仅管理员）")
async def bridge_stats_command(interaction: discord.Interaction):
    """查看桥接统计 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    try:
        conn = sqlite3.connect('bridge_config.db')
        cursor = conn.cursor()
        
        # 获取统计数据
        cursor.execute('SELECT COUNT(*) FROM bridge_configs WHERE is_enabled = TRUE')
        active_bridges = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM forwarded_messages')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM forwarded_messages WHERE DATE(timestamp) = DATE("now")')
        today_messages = cursor.fetchone()[0]
        
        # 获取最活跃的桥接
        cursor.execute('''
            SELECT bridge_name, COUNT(*) as message_count
            FROM forwarded_messages 
            GROUP BY bridge_name 
            ORDER BY message_count DESC 
            LIMIT 5
        ''')
        top_bridges = cursor.fetchall()
        
        conn.close()
        
        # 创建统计信息
        embed = discord.Embed(
            title="📊 跨服桥接统计",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🌉 桥接状态",
            value=f"**活跃桥接：** {active_bridges} 个",
            inline=True
        )
        
        embed.add_field(
            name="💬 消息统计",
            value=(
                f"**总转发数：** {total_messages:,} 条\n"
                f"**今日转发：** {today_messages} 条"
            ),
            inline=True
        )
        
        if top_bridges:
            top_text = ""
            for i, (bridge_name, count) in enumerate(top_bridges, 1):
                top_text += f"{i}. {bridge_name}: {count:,} 条\n"
            
            embed.add_field(
                name="🏆 最活跃桥接",
                value=top_text,
                inline=False
            )
        
        embed.set_footer(text="跨服桥接系统")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 获取统计信息失败：{e}",
            ephemeral=True
        )

@bot.tree.command(name="bridge_help", description="查看跨服桥接机器人帮助")
async def bridge_help_command(interaction: discord.Interaction):
    """帮助命令"""
    
    embed = discord.Embed(
        title="🌉 跨服桥接机器人使用指南",
        description="实现服务器间的消息转发和跨服沟通",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="👑 管理员命令",
        value=(
            "`/bridge_add` - 添加新的桥接配置\n"
            "`/bridge_list` - 查看所有桥接配置\n"
            "`/bridge_remove` - 删除桥接配置\n"
            "`/bridge_stats` - 查看转发统计\n"
            "`/bridge_help` - 查看帮助"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔧 功能特点",
        value=(
            "• **真实用户外观** - 显示原用户头像和昵称\n"
            "• **完整消息支持** - 转发文本、图片、附件\n"
            "• **来源标识** - 显示消息来源服务器和频道\n"
            "• **实时转发** - 消息即时同步\n"
            "• **多桥接支持** - 可配置多个转发规则"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📋 配置步骤",
        value=(
            "1. **获取频道ID** - 右键频道→复制链接→提取ID\n"
            "2. **添加桥接** - 使用 `/bridge_add` 命令\n"
            "3. **测试功能** - 在源频道发送测试消息\n"
            "4. **查看状态** - 使用 `/bridge_list` 检查配置"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚠️ 权限要求",
        value=(
            "机器人需要在两个服务器都有以下权限：\n"
            "• 读取消息历史\n"
            "• 发送消息\n"
            "• 管理Webhook\n"
            "• 嵌入链接"
        ),
        inline=False
    )
    
    embed.set_footer(text="跨服桥接系统 | 连接不同社区")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """错误处理"""
    print(f'命令错误: {error}')

if __name__ == '__main__':
    try:
        print("🌉 正在启动跨服桥接机器人...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ 错误：无效的机器人令牌。请检查BOT_TOKEN设置。")
    except Exception as e:
        print(f"❌ 启动机器人时发生错误: {e}")
