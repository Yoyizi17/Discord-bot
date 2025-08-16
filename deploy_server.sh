#!/bin/bash

echo "🚀 Discord机器人一键部署脚本"

# 更新系统
echo "📦 更新系统包..."
apt update && apt upgrade -y

# 安装Python和Git
echo "🐍 安装Python 3.11..."
apt install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-pip git screen

# 克隆项目
echo "📥 下载机器人代码..."
cd /home
git clone https://github.com/Yoyizi17/Discord-bot.git discord-bot
cd discord-bot

# 安装依赖
echo "📚 安装依赖包..."
python3.11 -m pip install -r requirements.txt

# 创建配置文件
echo "⚙️ 配置机器人..."
echo "export BOT_TOKEN='你的机器人TOKEN'" > .env

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd /home/discord-bot
source .env
python3.11 main.py
EOF

chmod +x start.sh

# 创建系统服务（自动启动）
cat > /etc/systemd/system/discord-bot.service << 'EOF'
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/discord-bot
Environment=BOT_TOKEN=你的机器人TOKEN
ExecStart=/usr/bin/python3.11 /home/discord-bot/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 部署完成！"
echo ""
echo "📝 接下来需要手动操作："
echo "1. 编辑配置: nano /etc/systemd/system/discord-bot.service"
echo "2. 替换 '你的机器人TOKEN' 为实际TOKEN"
echo "3. 启动服务: systemctl enable discord-bot && systemctl start discord-bot"
echo "4. 查看状态: systemctl status discord-bot"
echo "5. 查看日志: journalctl -u discord-bot -f"
