# 🗳️ Discord 匿名投票机器人

一个功能强大的Discord匿名投票系统，让服务器成员可以匿名给其他人投票，同时保护隐私。

## ✨ 功能特性

### 🎯 **核心功能**
- **匿名投票** - 成员可以给其他人投好票/坏票
- **完全隐私** - 投票记录对普通成员完全隐藏
- **管理员统计** - 只有管理员能查看投票数据和统计
- **数据持久化** - 使用SQLite数据库安全存储所有投票记录

### 🔧 **斜杠命令**

#### 普通用户命令：
- `/vote @用户 票型` - 给指定用户投票（好票/坏票）
- `/my_votes` - 查看自己的投票历史（仅自己可见）

#### 管理员专用命令：
- `/stats @用户` - 查看指定用户的投票统计
- `/leaderboard` - 查看服务器投票排行榜

## 🔒 **隐私保护**

- ✅ **投票完全匿名** - 没人知道是谁投的票
- ✅ **统计数据加密** - 只有管理员能访问
- ✅ **个人投票隐私** - 只能看到自己的投票历史
- ✅ **权限严格控制** - 管理员命令有权限验证

## 🚀 **部署指南**

### 1. 创建新的Discord应用
1. 访问 [Discord开发者门户](https://discord.com/developers/applications)
2. 创建新应用，命名为"投票机器人"或类似名称
3. 转到"Bot"部分，创建机器人并复制TOKEN

### 2. 设置机器人权限
邀请机器人时需要以下权限：
- ✅ **Send Messages** - 发送消息
- ✅ **Use Slash Commands** - 使用斜杠命令
- ✅ **Read Message History** - 读取消息历史
- ✅ **Embed Links** - 嵌入链接（用于美化消息）

### 3. 服务器部署

#### 上传文件到服务器：
```bash
# 将文件上传到服务器
scp vote_bot.py vote_requirements.txt linuxuser@你的服务器IP:~/

# 连接到服务器
ssh linuxuser@你的服务器IP

# 创建项目目录
mkdir vote-bot
cd vote-bot
mv ~/vote_bot.py ~/vote_requirements.txt ./
```

#### 安装依赖：
```bash
# 安装Python依赖
pip3 install -r vote_requirements.txt
```

#### 配置TOKEN：
```bash
# 编辑配置
nano vote_bot.py

# 找到这一行并替换TOKEN：
# BOT_TOKEN = os.getenv('VOTE_BOT_TOKEN', "你的投票机器人TOKEN")
```

#### 运行机器人：
```bash
# 测试运行
python3 vote_bot.py

# 后台运行（推荐）
screen -S vote-bot python3 vote_bot.py
# 按 Ctrl+A+D 退出screen而不停止程序
```

### 4. 设置系统服务（可选）

创建自动启动服务：
```bash
sudo nano /etc/systemd/system/vote-bot.service
```

添加内容：
```ini
[Unit]
Description=Discord Vote Bot
After=network.target

[Service]
Type=simple
User=linuxuser
WorkingDirectory=/home/linuxuser/vote-bot
Environment=VOTE_BOT_TOKEN=你的机器人TOKEN
ExecStart=/usr/bin/python3 /home/linuxuser/vote-bot/vote_bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable vote-bot
sudo systemctl start vote-bot
sudo systemctl status vote-bot
```

## 📊 **使用示例**

### 普通用户投票：
```
/vote @张三 好票    # 给张三投好票
/vote @李四 坏票    # 给李四投坏票
/my_votes          # 查看自己的投票历史
```

### 管理员查看统计：
```
/stats @张三       # 查看张三的投票统计
/leaderboard      # 查看排行榜
```

## 🗄️ **数据库结构**

SQLite数据库 `votes.db` 包含：
- **votes表**：存储所有投票记录
  - `voter_id`: 投票者ID
  - `target_id`: 被投票者ID  
  - `vote_type`: 票型（好票/坏票）
  - `guild_id`: 服务器ID
  - `timestamp`: 投票时间

## 🔧 **管理和维护**

### 查看日志：
```bash
# 如果使用systemd服务
sudo journalctl -u vote-bot -f

# 如果使用screen
screen -r vote-bot
```

### 备份数据库：
```bash
# 备份投票数据
cp votes.db votes_backup_$(date +%Y%m%d).db
```

### 重启机器人：
```bash
# systemd服务
sudo systemctl restart vote-bot

# screen运行
screen -r vote-bot
# Ctrl+C停止，然后重新运行
python3 vote_bot.py
```

## ⚠️ **注意事项**

- 🔐 **保护TOKEN** - 永远不要分享机器人TOKEN
- 🗄️ **定期备份** - 建议定期备份votes.db数据库
- 👥 **权限管理** - 确保只有可信用户有管理员权限
- 🔄 **更新机器人** - 定期检查并更新Discord.py版本

## 🎉 **功能亮点**

- **用户友好** - 简单的斜杠命令界面
- **数据安全** - SQLite数据库可靠存储
- **权限分离** - 普通用户和管理员功能分离
- **匿名保护** - 投票者身份完全保密
- **实时统计** - 即时的投票数据和排行榜

享受你的Discord投票系统吧！🎊
