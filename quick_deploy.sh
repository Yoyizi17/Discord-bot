#!/bin/bash

# 🚀 Discord机器人快速部署脚本
# 作者：Yoyizi17
# 用途：在新服务器上快速部署投票机器人和跨服桥接机器人

echo "🚀 Discord机器人快速部署开始..."
echo "================================"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root用户运行此脚本"
    echo "   sudo bash quick_deploy.sh"
    exit 1
fi

# 更新系统
echo "📦 更新系统软件包..."
apt update -y
apt upgrade -y

# 安装必要软件
echo "⚙️ 安装必要软件..."
apt install python3 python3-pip git screen nano curl wget -y

# 验证安装
echo "✅ 验证安装..."
python3 --version
pip3 --version

# 创建机器人目录
echo "📁 创建工作目录..."
mkdir -p /root/discord-bots/{vote-bot,bridge-bot}

# 下载投票机器人
echo "📥 下载投票机器人..."
cd /root/discord-bots/vote-bot
wget -q -O vote_bot_v2.py https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_bot_v2.py
wget -q -O vote_requirements.txt https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 投票机器人代码下载成功"
else
    echo "❌ 投票机器人代码下载失败"
    exit 1
fi

# 安装投票机器人依赖
echo "📦 安装投票机器人依赖..."
pip3 install -r vote_requirements.txt

# 下载跨服桥接机器人
echo "📥 下载跨服桥接机器人..."
cd /root/discord-bots/bridge-bot
wget -q -O cross_server_bridge_bot.py https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/cross_server_bridge_bot.py

if [ $? -eq 0 ]; then
    echo "✅ 跨服桥接机器人代码下载成功"
else
    echo "❌ 跨服桥接机器人代码下载失败"
    exit 1
fi

# 安装跨服桥接机器人依赖
echo "📦 安装跨服桥接机器人依赖..."
pip3 install discord.py aiohttp

# 创建启动脚本
echo "🔧 创建启动脚本..."

# 投票机器人启动脚本
cat > /root/discord-bots/start_vote_bot.sh << 'EOF'
#!/bin/bash
cd /root/discord-bots/vote-bot
screen -S vote-bot python3 vote_bot_v2.py
EOF

# 跨服桥接机器人启动脚本
cat > /root/discord-bots/start_bridge_bot.sh << 'EOF'
#!/bin/bash
cd /root/discord-bots/bridge-bot
screen -S bridge-bot python3 cross_server_bridge_bot.py
EOF

# 监控脚本
cat > /root/discord-bots/monitor_bots.sh << 'EOF'
#!/bin/bash
echo "📊 Discord机器人运行状态："
echo "================================"

if screen -list | grep -q "vote-bot"; then
    echo "✅ 投票机器人: 运行中"
else
    echo "❌ 投票机器人: 未运行"
    echo "   启动命令: bash /root/discord-bots/start_vote_bot.sh"
fi

if screen -list | grep -q "bridge-bot"; then
    echo "✅ 跨服桥接机器人: 运行中"  
else
    echo "❌ 跨服桥接机器人: 未运行"
    echo "   启动命令: bash /root/discord-bots/start_bridge_bot.sh"
fi

echo "================================"
echo "📝 所有Screen会话："
screen -ls
EOF

# 停止脚本
cat > /root/discord-bots/stop_bots.sh << 'EOF'
#!/bin/bash
echo "🛑 停止所有Discord机器人..."

if screen -list | grep -q "vote-bot"; then
    screen -S vote-bot -X quit
    echo "✅ 投票机器人已停止"
else
    echo "⚠️ 投票机器人未在运行"
fi

if screen -list | grep -q "bridge-bot"; then
    screen -S bridge-bot -X quit
    echo "✅ 跨服桥接机器人已停止"
else
    echo "⚠️ 跨服桥接机器人未在运行"
fi

echo "🎯 所有机器人已停止"
EOF

# 重启脚本
cat > /root/discord-bots/restart_bots.sh << 'EOF'
#!/bin/bash
echo "🔄 重启所有Discord机器人..."

# 停止机器人
bash /root/discord-bots/stop_bots.sh

sleep 2

# 启动机器人
echo "🚀 启动投票机器人..."
bash /root/discord-bots/start_vote_bot.sh

sleep 2

echo "🚀 启动跨服桥接机器人..."
bash /root/discord-bots/start_bridge_bot.sh

sleep 2

# 检查状态
bash /root/discord-bots/monitor_bots.sh
EOF

# 设置执行权限
chmod +x /root/discord-bots/*.sh

# 创建TOKEN配置提示文件
cat > /root/discord-bots/README.txt << 'EOF'
🎯 Discord机器人部署完成！

接下来需要配置TOKEN：

1. 配置投票机器人TOKEN：
   nano /root/discord-bots/vote-bot/vote_bot_v2.py
   找到: BOT_TOKEN = os.getenv('VOTE_BOT_TOKEN', "你的投票机器人令牌放在这里")
   替换: "你的投票机器人令牌放在这里" -> 你的实际TOKEN

2. 配置跨服桥接机器人TOKEN：
   nano /root/discord-bots/bridge-bot/cross_server_bridge_bot.py
   找到: BOT_TOKEN = os.getenv('BRIDGE_BOT_TOKEN', "你的跨服桥接机器人TOKEN")
   替换: "你的跨服桥接机器人TOKEN" -> 你的实际TOKEN

3. 启动机器人：
   bash /root/discord-bots/start_vote_bot.sh
   bash /root/discord-bots/start_bridge_bot.sh

4. 监控机器人：
   bash /root/discord-bots/monitor_bots.sh

5. 停止机器人：
   bash /root/discord-bots/stop_bots.sh

6. 重启机器人：
   bash /root/discord-bots/restart_bots.sh

重要提醒：
- 按 Ctrl+A+D 退出screen会话（机器人继续运行）
- screen -r vote-bot 重新连接投票机器人
- screen -r bridge-bot 重新连接跨服桥接机器人

祝你使用愉快！🎉
EOF

echo ""
echo "🎉 Discord机器人部署完成！"
echo "================================"
echo "📁 安装位置: /root/discord-bots/"
echo "📝 使用说明: cat /root/discord-bots/README.txt"
echo ""
echo "⏭️ 下一步："
echo "1. 配置机器人TOKEN"
echo "2. 启动机器人"
echo "3. 在Discord中测试功能"
echo ""
echo "🔧 常用命令："
echo "   bash /root/discord-bots/monitor_bots.sh  # 查看状态"
echo "   bash /root/discord-bots/start_vote_bot.sh    # 启动投票机器人"  
echo "   bash /root/discord-bots/start_bridge_bot.sh  # 启动跨服机器人"
echo "   bash /root/discord-bots/stop_bots.sh         # 停止所有机器人"
echo ""
echo "📖 详细说明: cat /root/discord-bots/README.txt"
echo "================================"

# 显示目录结构
echo "📁 目录结构："
tree /root/discord-bots/ 2>/dev/null || find /root/discord-bots/ -type f -exec echo "   {}" \;
