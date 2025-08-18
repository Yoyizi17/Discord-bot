# 🚀 Discord机器人服务器部署完整指南

## 📋 准备工作

### 1. 获取服务器信息
购买萤光云服务器后，你会收到：
- **服务器IP地址**: 例如 `8.8.8.8`
- **用户名**: 通常是 `root` 或 `ubuntu`
- **密码**: 在控制面板查看

### 2. 准备Discord机器人TOKEN
- **投票机器人TOKEN**: 从Discord开发者门户获取
- **跨服桥接机器人TOKEN**: 从Discord开发者门户获取

---

## 🔧 服务器部署命令流程

### 第一步：连接服务器
```bash
# 使用SSH连接服务器（替换IP地址）
ssh root@你的服务器IP地址

# 如果是ubuntu用户
ssh ubuntu@你的服务器IP地址
```

### 第二步：更新系统
```bash
# 更新软件包列表
apt update

# 升级系统软件包
apt upgrade -y
```

### 第三步：安装必要软件
```bash
# 安装Python3和pip
apt install python3 python3-pip git screen nano curl wget -y

# 验证安装
python3 --version
pip3 --version
```

### 第四步：创建机器人目录
```bash
# 创建工作目录
mkdir -p /root/discord-bots
cd /root/discord-bots

# 创建子目录
mkdir vote-bot bridge-bot
```

### 第五步：下载投票机器人
```bash
# 进入投票机器人目录
cd /root/discord-bots/vote-bot

# 下载投票机器人代码
wget https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_bot_v2.py
wget https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_requirements.txt

# 安装依赖
pip3 install -r vote_requirements.txt
```

### 第六步：下载跨服桥接机器人
```bash
# 进入跨服桥接机器人目录
cd /root/discord-bots/bridge-bot

# 下载跨服桥接机器人代码
wget https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/cross_server_bridge_bot.py

# 安装依赖
pip3 install discord.py aiohttp
```

### 第七步：配置投票机器人TOKEN
```bash
cd /root/discord-bots/vote-bot

# 编辑投票机器人代码
nano vote_bot_v2.py

# 在nano编辑器中：
# 1. 找到这一行：BOT_TOKEN = os.getenv('VOTE_BOT_TOKEN', "你的投票机器人令牌放在这里")
# 2. 将 "你的投票机器人令牌放在这里" 替换为你的实际TOKEN
# 3. 按 Ctrl+X，然后按 Y，再按 Enter 保存

# 或者使用环境变量（推荐）
echo 'export VOTE_BOT_TOKEN="你的投票机器人TOKEN"' >> ~/.bashrc
source ~/.bashrc
```

### 第八步：配置跨服桥接机器人TOKEN
```bash
cd /root/discord-bots/bridge-bot

# 编辑跨服桥接机器人代码
nano cross_server_bridge_bot.py

# 在nano编辑器中：
# 1. 找到这一行：BOT_TOKEN = os.getenv('BRIDGE_BOT_TOKEN', "你的跨服桥接机器人TOKEN")
# 2. 将 "你的跨服桥接机器人TOKEN" 替换为你的实际TOKEN
# 3. 按 Ctrl+X，然后按 Y，再按 Enter 保存

# 或者使用环境变量（推荐）
echo 'export BRIDGE_BOT_TOKEN="你的跨服桥接机器人TOKEN"' >> ~/.bashrc
source ~/.bashrc
```

### 第九步：启动投票机器人
```bash
cd /root/discord-bots/vote-bot

# 在screen中启动投票机器人
screen -S vote-bot python3 vote_bot_v2.py

# 按 Ctrl+A+D 退出screen（机器人继续在后台运行）
```

### 第十步：启动跨服桥接机器人
```bash
cd /root/discord-bots/bridge-bot

# 在screen中启动跨服桥接机器人
screen -S bridge-bot python3 cross_server_bridge_bot.py

# 按 Ctrl+A+D 退出screen（机器人继续在后台运行）
```

---

## 🔍 验证和管理

### 检查机器人运行状态
```bash
# 查看所有screen会话
screen -ls

# 重新连接到投票机器人
screen -r vote-bot

# 重新连接到跨服桥接机器人  
screen -r bridge-bot

# 退出screen会话
# 按 Ctrl+A+D
```

### 查看机器人日志
```bash
# 连接到投票机器人查看日志
screen -r vote-bot

# 连接到跨服桥接机器人查看日志
screen -r bridge-bot
```

### 停止机器人
```bash
# 停止投票机器人
screen -S vote-bot -X quit

# 停止跨服桥接机器人
screen -S bridge-bot -X quit
```

### 重启机器人
```bash
# 停止后重新启动投票机器人
cd /root/discord-bots/vote-bot
screen -S vote-bot python3 vote_bot_v2.py

# 停止后重新启动跨服桥接机器人
cd /root/discord-bots/bridge-bot
screen -S bridge-bot python3 cross_server_bridge_bot.py
```

---

## 🎯 快速部署脚本

### 一键部署脚本（可选）
```bash
# 创建自动部署脚本
cat > /root/deploy_bots.sh << 'EOF'
#!/bin/bash
echo "🚀 开始部署Discord机器人..."

# 更新系统
apt update && apt upgrade -y

# 安装必要软件
apt install python3 python3-pip git screen nano curl wget -y

# 创建目录
mkdir -p /root/discord-bots/{vote-bot,bridge-bot}

# 下载投票机器人
cd /root/discord-bots/vote-bot
wget -O vote_bot_v2.py https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_bot_v2.py
wget -O vote_requirements.txt https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/vote_requirements.txt
pip3 install -r vote_requirements.txt

# 下载跨服桥接机器人
cd /root/discord-bots/bridge-bot
wget -O cross_server_bridge_bot.py https://raw.githubusercontent.com/Yoyizi17/Discord-bot/main/cross_server_bridge_bot.py
pip3 install discord.py aiohttp

echo "✅ 机器人代码下载完成！"
echo "📝 请手动配置TOKEN后启动机器人："
echo "   1. nano /root/discord-bots/vote-bot/vote_bot_v2.py"
echo "   2. nano /root/discord-bots/bridge-bot/cross_server_bridge_bot.py"
echo "   3. screen -S vote-bot python3 /root/discord-bots/vote-bot/vote_bot_v2.py"
echo "   4. screen -S bridge-bot python3 /root/discord-bots/bridge-bot/cross_server_bridge_bot.py"
EOF

# 运行部署脚本
chmod +x /root/deploy_bots.sh
bash /root/deploy_bots.sh
```

---

## 📱 Discord配置

### 投票机器人配置
1. **邀请投票机器人到服务器**
   - 权限：发送消息、使用斜杠命令、管理消息
2. **测试命令**：
   ```
   /vote @用户名 好评
   /stats @用户名
   /leaderboard
   ```

### 跨服桥接机器人配置  
1. **邀请跨服桥接机器人到所有相关服务器**
   - 权限：发送消息、读取消息历史、管理Webhook、使用斜杠命令
2. **配置桥接**：
   ```
   /bridge_add 
   桥接名称: 主服-分服
   源服务器ID: [服务器1的ID]
   源频道ID: [频道1的ID]  
   目标服务器ID: [服务器2的ID]
   目标频道ID: [频道2的ID]
   ```

---

## ⚠️ 注意事项

### 安全设置
```bash
# 修改SSH端口（可选，提高安全性）
nano /etc/ssh/sshd_config
# 找到 #Port 22，改为 Port 2222
systemctl restart sshd

# 配置防火墙（可选）
ufw enable
ufw allow 2222/tcp  # 如果修改了SSH端口
```

### 备份设置
```bash
# 创建定时备份脚本
cat > /root/backup_bots.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /root/bot_backup_$DATE.tar.gz /root/discord-bots/
# 保留最近7天的备份
find /root/ -name "bot_backup_*.tar.gz" -mtime +7 -delete
EOF

chmod +x /root/backup_bots.sh

# 添加到定时任务（每天凌晨2点备份）
echo "0 2 * * * /root/backup_bots.sh" | crontab -
```

### 监控脚本
```bash
# 创建机器人监控脚本
cat > /root/monitor_bots.sh << 'EOF'
#!/bin/bash
echo "📊 Discord机器人运行状态："
echo "================================"

if screen -list | grep -q "vote-bot"; then
    echo "✅ 投票机器人: 运行中"
else
    echo "❌ 投票机器人: 未运行"
fi

if screen -list | grep -q "bridge-bot"; then
    echo "✅ 跨服桥接机器人: 运行中"
else
    echo "❌ 跨服桥接机器人: 未运行"
fi

echo "================================"
echo "📝 Screen会话列表："
screen -ls
EOF

chmod +x /root/monitor_bots.sh

# 使用方法
# bash /root/monitor_bots.sh
```

---

## 🎉 部署完成

按照这个流程，你的两个机器人就能在新服务器上稳定运行了！

如果遇到问题，可以：
1. 检查screen会话状态
2. 查看机器人控制台输出
3. 确认TOKEN配置正确
4. 验证Discord机器人权限

祝你部署顺利！🚀
