import discord
from discord.ext import commands
from config import BOT_TOKEN

# 创建机器人实例，设置命令前缀和意图
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """当机器人成功连接到Discord时触发"""
    print(f'{bot.user} 已经成功启动！')
    print(f'机器人ID: {bot.user.id}')
    print('-----')

@bot.event
async def on_reaction_add(reaction, user):
    """当有人给消息添加反应时触发"""
    # 确保不是机器人自己添加的反应
    if user.bot:
        return
    
    # 在添加反应的消息所在频道发送回复
    channel = reaction.message.channel
    await channel.send("收到啦~")
    
    # 在控制台打印日志
    print(f'{user.name} 在 #{channel.name} 添加了反应 {reaction.emoji}')

@bot.event
async def on_message(message):
    """当有消息发送时触发"""
    # 确保不是机器人自己发送的消息
    if message.author.bot:
        return
    
    # 检查消息中是否@了机器人
    if bot.user.mentioned_in(message):
        await message.channel.send("我在~")
        # 在控制台打印日志
        print(f'{message.author.name} 在 #{message.channel.name} @了机器人')
    
    # 重要：确保其他命令仍然能够工作
    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    """错误处理"""
    print(f'发生错误: {event}')

# 可选：添加一个简单的测试命令
@bot.command(name='hello')
async def hello(ctx):
    """测试命令：回复Hello"""
    await ctx.send(f'你好, {ctx.author.mention}!')

@bot.command(name='ping')
async def ping(ctx):
    """测试命令：显示延迟"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! 延迟: {latency}ms')

if __name__ == '__main__':
    try:
        print("正在启动机器人...")
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("错误：无效的机器人令牌。请检查config.py中的BOT_TOKEN设置。")
    except Exception as e:
        print(f"启动机器人时发生错误: {e}")