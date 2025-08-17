import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import json
import zipfile
import tempfile
from datetime import datetime
from typing import Optional
import asyncio

# 配置
BOT_TOKEN = os.getenv('DM_COMPLIANCE_BOT_TOKEN', "你的违规检测机器人TOKEN")

# 创建机器人实例
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 数据库初始化
def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect('compliance_reports.db')
    cursor = conn.cursor()
    
    # 创建违规报告表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            guild_id INTEGER NOT NULL,
            report_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            dm_users_count INTEGER,
            dm_users_data TEXT,
            violation_status TEXT DEFAULT 'pending',
            admin_notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_compliance_report(user_id: int, username: str, guild_id: int, dm_data: list):
    """保存违规检测报告"""
    conn = sqlite3.connect('compliance_reports.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO compliance_reports 
        (user_id, username, guild_id, dm_users_count, dm_users_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, guild_id, len(dm_data), json.dumps(dm_data, ensure_ascii=False)))
    
    conn.commit()
    conn.close()

def get_compliance_reports(guild_id: int, limit: int = 50):
    """获取违规检测报告"""
    conn = sqlite3.connect('compliance_reports.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, report_time, dm_users_count, violation_status
        FROM compliance_reports 
        WHERE guild_id = ?
        ORDER BY report_time DESC
        LIMIT ?
    ''', (guild_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results

def analyze_discord_data(file_content: bytes) -> list:
    """分析Discord数据包"""
    dm_users = []
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # 解析ZIP文件
        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            # 查找messages文件夹
            message_files = [f for f in zip_ref.namelist() if f.startswith('messages/') and f.endswith('.json')]
            
            for file_path in message_files:
                try:
                    with zip_ref.open(file_path) as f:
                        data = json.load(f)
                        
                        if 'messages' not in data or not data['messages']:
                            continue
                        
                        # 获取频道信息
                        channel_type = data.get('type', 0)
                        recipients = data.get('recipients', [])
                        
                        # 只处理私信频道 (type=1为DM, type=3为群聊)
                        if channel_type in [1, 3]:
                            if recipients:
                                for recipient in recipients:
                                    user_info = {
                                        'username': recipient.get('username', '未知'),
                                        'display_name': recipient.get('global_name') or recipient.get('username', '未知'),
                                        'user_id': recipient.get('id', '未知'),
                                        'channel_type': '群聊' if channel_type == 3 else '私信',
                                        'message_count': len(data['messages']),
                                        'last_message_time': data['messages'][0].get('timestamp', '') if data['messages'] else ''
                                    }
                                    dm_users.append(user_info)
                            else:
                                # 从文件名提取信息
                                filename = os.path.basename(file_path)
                                user_info = {
                                    'username': filename.replace('.json', ''),
                                    'display_name': filename.replace('.json', ''),
                                    'user_id': '从文件名提取',
                                    'channel_type': '群聊' if channel_type == 3 else '私信',
                                    'message_count': len(data['messages']),
                                    'last_message_time': data['messages'][0].get('timestamp', '') if data['messages'] else ''
                                }
                                dm_users.append(user_info)
                
                except Exception as e:
                    print(f"分析文件 {file_path} 失败: {e}")
                    continue
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"分析数据包失败: {e}")
    
    return dm_users

@bot.event
async def on_ready():
    """机器人启动事件"""
    print(f'🚨 违规检测机器人 {bot.user} 已启动！')
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

@bot.tree.command(name="submit_dm_report", description="提交私信合规报告（上传Discord数据包）")
async def submit_dm_report_command(interaction: discord.Interaction, 
                                  数据包: discord.Attachment):
    """提交私信合规报告"""
    
    # 检查文件类型
    if not 数据包.filename.endswith('.zip'):
        await interaction.response.send_message(
            "❌ 请上传ZIP格式的Discord数据包！\n\n"
            "📋 **获取方法：**\n"
            "1. Discord设置 → 隐私与安全\n"
            "2. 点击'申请我的数据'\n"
            "3. 等待邮件并下载ZIP文件\n"
            "4. 使用此命令上传ZIP文件",
            ephemeral=True
        )
        return
    
    # 检查文件大小（限制100MB）
    if 数据包.size > 100 * 1024 * 1024:
        await interaction.response.send_message(
            "❌ 文件过大！请确保数据包小于100MB。",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 下载并分析文件
        file_content = await 数据包.read()
        dm_users = analyze_discord_data(file_content)
        
        if not dm_users:
            await interaction.followup.send(
                "✅ **合规检测完成**\n\n"
                "📊 **结果：** 未发现私信记录\n"
                "🟢 **状态：** 符合服务器规则\n\n"
                "💡 此结果已记录并通知管理员。",
                ephemeral=True
            )
        else:
            # 保存报告到数据库
            save_compliance_report(
                interaction.user.id, 
                interaction.user.name, 
                interaction.guild.id, 
                dm_users
            )
            
            # 创建用户结果消息
            user_embed = discord.Embed(
                title="📊 私信合规检测结果",
                description=f"检测到 **{len(dm_users)}** 个私信/群聊记录",
                color=discord.Color.orange() if len(dm_users) > 0 else discord.Color.green(),
                timestamp=datetime.now()
            )
            
            user_embed.add_field(
                name="📋 检测结果",
                value=(
                    f"• 私信用户数: {len([u for u in dm_users if u['channel_type'] == '私信'])}\n"
                    f"• 群聊数量: {len([u for u in dm_users if u['channel_type'] == '群聊'])}\n"
                    f"• 总记录数: {len(dm_users)}"
                ),
                inline=False
            )
            
            user_embed.add_field(
                name="⚠️ 注意事项",
                value=(
                    "• 此结果已自动提交给管理员审核\n"
                    "• 管理员将根据服务器规则进行判断\n"
                    "• 如有疑问请联系服务器管理员"
                ),
                inline=False
            )
            
            user_embed.set_footer(text="合规检测系统")
            
            await interaction.followup.send(embed=user_embed, ephemeral=True)
        
        # 通知管理员
        await notify_admins(interaction, dm_users)
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ 处理数据包时发生错误：{e}\n\n"
            "💡 请确保上传的是正确的Discord数据包ZIP文件。",
            ephemeral=True
        )

async def notify_admins(interaction: discord.Interaction, dm_users: list):
    """通知管理员检测结果"""
    
    # 创建管理员通知消息
    admin_embed = discord.Embed(
        title="🚨 新的私信合规报告",
        description=f"用户 **{interaction.user.mention}** 提交了私信合规报告",
        color=discord.Color.red() if len(dm_users) > 0 else discord.Color.green(),
        timestamp=datetime.now()
    )
    
    admin_embed.add_field(
        name="👤 用户信息",
        value=(
            f"**用户名：** {interaction.user.name}\n"
            f"**显示名：** {interaction.user.display_name}\n"
            f"**用户ID：** {interaction.user.id}"
        ),
        inline=True
    )
    
    admin_embed.add_field(
        name="📊 检测结果",
        value=(
            f"**私信用户：** {len([u for u in dm_users if u['channel_type'] == '私信'])}\n"
            f"**群聊数量：** {len([u for u in dm_users if u['channel_type'] == '群聊'])}\n"
            f"**总记录：** {len(dm_users)}"
        ),
        inline=True
    )
    
    # 如果有违规记录，显示详细信息
    if dm_users:
        # 显示前5个私信用户
        dm_list = [u for u in dm_users if u['channel_type'] == '私信'][:5]
        if dm_list:
            dm_text = ""
            for user in dm_list:
                dm_text += f"• {user['username']} ({user['message_count']} 条消息)\n"
            
            if len([u for u in dm_users if u['channel_type'] == '私信']) > 5:
                dm_text += f"• ...还有 {len([u for u in dm_users if u['channel_type'] == '私信']) - 5} 个用户"
            
            admin_embed.add_field(
                name="📨 私信用户列表",
                value=dm_text,
                inline=False
            )
    
    admin_embed.set_footer(text="违规检测系统 | 使用 /compliance_details 查看详细信息")
    
    # 发送给所有管理员
    for member in interaction.guild.members:
        if member.guild_permissions.administrator and not member.bot:
            try:
                await member.send(embed=admin_embed)
            except:
                continue  # 如果无法发送私信，跳过

@bot.tree.command(name="compliance_details", description="查看用户的详细私信合规报告（仅管理员）")
@app_commands.describe(用户="要查看报告的用户")
async def compliance_details_command(interaction: discord.Interaction, 
                                   用户: discord.User):
    """查看详细合规报告 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 从数据库获取报告
        conn = sqlite3.connect('compliance_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT dm_users_data, report_time, dm_users_count
            FROM compliance_reports 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY report_time DESC
            LIMIT 1
        ''', (用户.id, interaction.guild.id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            await interaction.followup.send(
                f"❌ 未找到用户 **{用户.name}** 的合规报告！",
                ephemeral=True
            )
            return
        
        dm_users_data = json.loads(result[0])
        report_time = result[1]
        total_count = result[2]
        
        # 创建详细报告
        embed = discord.Embed(
            title=f"📋 {用户.name} 的详细私信报告",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(report_time)
        )
        
        embed.set_thumbnail(url=用户.display_avatar.url)
        
        # 统计信息
        dm_count = len([u for u in dm_users_data if u['channel_type'] == '私信'])
        group_count = len([u for u in dm_users_data if u['channel_type'] == '群聊'])
        
        embed.add_field(
            name="📊 统计概览",
            value=(
                f"**私信用户：** {dm_count}\n"
                f"**群聊数量：** {group_count}\n"
                f"**总记录数：** {total_count}\n"
                f"**报告时间：** {report_time[:10]}"
            ),
            inline=False
        )
        
        # 私信用户详细列表
        if dm_count > 0:
            dm_list_text = ""
            for i, user in enumerate([u for u in dm_users_data if u['channel_type'] == '私信'][:15], 1):
                last_time = user['last_message_time'][:10] if user['last_message_time'] else '未知'
                dm_list_text += f"{i}. **{user['username']}** - {user['message_count']} 条消息 ({last_time})\n"
            
            if dm_count > 15:
                dm_list_text += f"... 还有 {dm_count - 15} 个用户"
            
            embed.add_field(
                name="📨 私信用户列表",
                value=dm_list_text,
                inline=False
            )
        
        # 群聊列表
        if group_count > 0:
            group_list_text = ""
            for i, group in enumerate([u for u in dm_users_data if u['channel_type'] == '群聊'][:10], 1):
                group_list_text += f"{i}. **{group['username']}** - {group['message_count']} 条消息\n"
            
            if group_count > 10:
                group_list_text += f"... 还有 {group_count - 10} 个群聊"
            
            embed.add_field(
                name="👨‍👩‍👧‍👦 群聊列表",
                value=group_list_text,
                inline=False
            )
        
        embed.set_footer(text="管理员专用 | 违规检测系统")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ 获取报告详情时发生错误：{e}",
            ephemeral=True
        )

@bot.tree.command(name="compliance_list", description="查看所有用户的合规报告列表（仅管理员）")
@app_commands.describe(显示数量="显示报告数量（最多50）")
async def compliance_list_command(interaction: discord.Interaction, 
                                显示数量: int = 20):
    """查看合规报告列表 - 仅管理员"""
    
    # 检查权限
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 此命令仅限管理员使用！", 
            ephemeral=True
        )
        return
    
    # 限制显示数量
    if 显示数量 > 50:
        显示数量 = 50
    elif 显示数量 < 1:
        显示数量 = 20
    
    reports = get_compliance_reports(interaction.guild.id, 显示数量)
    
    if not reports:
        await interaction.response.send_message(
            "📊 还没有用户提交合规报告！",
            ephemeral=True
        )
        return
    
    # 创建报告列表
    embed = discord.Embed(
        title="📋 私信合规报告列表",
        description=f"显示最近 {len(reports)} 份报告",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    report_text = ""
    for i, (user_id, username, report_time, dm_count, status) in enumerate(reports, 1):
        status_emoji = "🟢" if dm_count == 0 else "🟡" if dm_count < 5 else "🔴"
        time_str = report_time[:10]
        
        report_text += f"{status_emoji} **{username}** - {dm_count} 个记录 ({time_str})\n"
        
        if len(report_text) > 3500:
            report_text += f"... 还有 {len(reports) - i} 份报告"
            break
    
    embed.description = report_text
    embed.set_footer(text="管理员专用 | 使用 /compliance_details 查看详细信息")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="compliance_help", description="查看违规检测机器人使用帮助")
async def compliance_help_command(interaction: discord.Interaction):
    """帮助命令"""
    
    embed = discord.Embed(
        title="🚨 违规检测机器人使用指南",
        description="检测和监控Discord私信合规性",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    if interaction.user.guild_permissions.administrator:
        # 管理员看到的帮助
        embed.add_field(
            name="👑 管理员命令",
            value=(
                "`/compliance_list` - 查看所有合规报告\n"
                "`/compliance_details @用户` - 查看用户详细报告\n"
                "`/compliance_help` - 查看帮助"
            ),
            inline=False
        )
    
    embed.add_field(
        name="👥 用户命令",
        value="`/submit_dm_report` - 提交私信合规报告",
        inline=False
    )
    
    embed.add_field(
        name="📋 如何提交报告",
        value=(
            "1. **申请Discord数据：**\n"
            "   Discord设置 → 隐私与安全 → 申请我的数据\n\n"
            "2. **等待邮件通知：**\n"
            "   通常需要1-3天收到数据包\n\n"
            "3. **下载ZIP文件并上传：**\n"
            "   使用 `/submit_dm_report` 命令上传ZIP文件"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔒 隐私保护",
        value=(
            "• 上传的数据仅用于合规检测\n"
            "• 详细信息仅管理员可见\n"
            "• 系统不存储敏感消息内容\n"
            "• 仅记录用户列表和统计信息"
        ),
        inline=False
    )
    
    embed.set_footer(text="违规检测系统")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """错误处理"""
    print(f'命令错误: {error}')

if __name__ == '__main__':
    try:
        print("🚨 正在启动违规检测机器人...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ 错误：无效的机器人令牌。请检查BOT_TOKEN设置。")
    except Exception as e:
        print(f"❌ 启动机器人时发生错误: {e}")
