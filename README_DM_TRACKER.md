# 📨 Discord 私信追踪机器人

一个功能强大的Discord私信管理系统，自动记录和统计所有私信用户，帮助机器人所有者管理私信交互。

## ✨ 功能特色

### 🎯 **核心功能**
- **自动记录** - 监听所有私信，自动记录用户信息
- **智能统计** - 消息数量、时间、用户活跃度统计
- **多维查询** - 支持多种排序和搜索方式
- **隐私保护** - 只有机器人所有者能查看数据
- **自动回复** - 自动回复私信消息

### 📊 **数据记录**
- 用户基本信息（用户名、头像等）
- 首次和最后私信时间
- 私信消息总数
- 最后一条消息内容预览
- 详细消息记录（可选）

## 🎛️ **命令功能**

### 👑 **机器人所有者专用命令**

#### `/dm_list` - 私信用户列表
```
/dm_list [排序方式] [显示数量]
```
**排序选项：**
- 📅 最新私信 - 按最后私信时间排序
- 🕐 首次私信 - 按首次私信时间排序  
- 💬 消息最多 - 按消息数量排序
- 🔤 用户名 - 按用户名字母排序

#### `/dm_stats` - 统计信息
显示详细的私信统计数据：
- 总用户数和消息数
- 今日新用户和消息数
- 平均消息数等

#### `/dm_search` - 搜索用户
```
/dm_search [关键词]
```
根据用户名或显示名搜索私信用户

#### `/dm_help` - 帮助信息
查看机器人使用帮助和功能说明

## 🔒 **隐私和安全**

### 🛡️ **权限控制**
- ✅ **严格权限** - 只有机器人所有者能查看数据
- ✅ **数据保护** - 所有查询结果仅发送方可见
- ✅ **本地存储** - 数据存储在本地SQLite数据库

### 📋 **数据记录范围**
- ✅ 用户基本信息（公开信息）
- ✅ 消息时间和数量
- ✅ 消息内容预览（限制长度）
- ❌ 不记录敏感个人信息

## 🚀 **部署指南**

### 1. 创建Discord机器人

1. 访问 [Discord开发者门户](https://discord.com/developers/applications)
2. 创建新应用，命名为"私信追踪机器人"
3. 创建Bot并复制TOKEN
4. **重要**：在Bot设置中启用以下权限：
   - ✅ **Message Content Intent** - 读取消息内容
   - ✅ **Direct Messages** - 接收私信

### 2. 设置机器人权限

邀请机器人时需要以下权限：
- ✅ **Send Messages** - 发送消息
- ✅ **Read Message History** - 读取消息历史
- ✅ **Use Slash Commands** - 使用斜杠命令
- ✅ **Embed Links** - 嵌入链接

### 3. 服务器部署

#### 上传文件到服务器：
```bash
# 将文件上传到服务器
scp dm_tracker_bot.py dm_requirements.txt linuxuser@你的服务器IP:~/

# 连接到服务器
ssh linuxuser@你的服务器IP

# 创建项目目录
mkdir dm-tracker-bot
cd dm-tracker-bot
mv ~/dm_tracker_bot.py ~/dm_requirements.txt ./
```

#### 安装依赖：
```bash
# 安装Python依赖
pip3 install -r dm_requirements.txt
```

#### 配置TOKEN：
```bash
# 编辑配置
nano dm_tracker_bot.py

# 找到这一行并替换TOKEN：
# BOT_TOKEN = os.getenv('DM_TRACKER_BOT_TOKEN', "你的私信追踪机器人TOKEN")
```

#### 运行机器人：
```bash
# 测试运行
python3 dm_tracker_bot.py

# 后台运行（推荐）
screen -S dm-tracker python3 dm_tracker_bot.py
# 按 Ctrl+A+D 退出screen而不停止程序
```

### 4. 设置系统服务（可选）

创建自动启动服务：
```bash
sudo nano /etc/systemd/system/dm-tracker.service
```

添加内容：
```ini
[Unit]
Description=Discord DM Tracker Bot
After=network.target

[Service]
Type=simple
User=linuxuser
WorkingDirectory=/home/linuxuser/dm-tracker-bot
Environment=DM_TRACKER_BOT_TOKEN=你的机器人TOKEN
ExecStart=/usr/bin/python3 /home/linuxuser/dm-tracker-bot/dm_tracker_bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable dm-tracker
sudo systemctl start dm-tracker
sudo systemctl status dm-tracker
```

## 📋 **使用示例**

### 查看私信用户列表（按最新消息排序）：
```
/dm_list 最新私信 20
```

### 查看私信统计：
```
/dm_stats
```

### 搜索特定用户：
```
/dm_search 张三
```

## 🗄️ **数据库结构**

### dm_users 表（用户信息）
- `user_id` - Discord用户ID
- `username` - 用户名
- `display_name` - 显示名
- `first_message_time` - 首次私信时间
- `last_message_time` - 最后私信时间
- `total_messages` - 消息总数
- `last_message_content` - 最后消息内容（预览）
- `avatar_url` - 头像URL

### dm_messages 表（消息记录）
- `user_id` - 用户ID
- `message_content` - 消息内容
- `timestamp` - 消息时间
- `message_id` - Discord消息ID

## 🔧 **管理和维护**

### 查看运行日志：
```bash
# 如果使用systemd服务
sudo journalctl -u dm-tracker -f

# 如果使用screen
screen -r dm-tracker
```

### 备份数据库：
```bash
# 备份私信数据
cp dm_users.db dm_users_backup_$(date +%Y%m%d).db
```

### 数据导出（可选）：
```bash
# 导出为CSV格式
sqlite3 dm_users.db -header -csv "SELECT * FROM dm_users;" > dm_users_export.csv
```

### 重启机器人：
```bash
# systemd服务
sudo systemctl restart dm-tracker

# screen运行
screen -r dm-tracker
# Ctrl+C停止，然后重新运行
python3 dm_tracker_bot.py
```

## ⚠️ **重要注意事项**

### 🚨 **Discord服务条款**
- 确保使用符合Discord服务条款
- 仅用于管理目的，不滥用用户数据
- 尊重用户隐私，不泄露私信内容

### 🔐 **安全建议**
- 定期备份数据库文件
- 保护好机器人TOKEN
- 限制服务器访问权限
- 定期检查数据库大小

### 📊 **性能优化**
- 定期清理过期消息记录
- 监控数据库大小
- 考虑设置消息记录数量限制

## 🎉 **功能亮点**

- **实时监控** - 自动捕获所有私信
- **智能分析** - 多维度数据统计
- **用户友好** - 简洁的斜杠命令界面
- **数据持久** - 可靠的SQLite数据库存储
- **隐私保护** - 严格的权限控制
- **易于管理** - 丰富的查询和搜索功能

让机器人帮你更好地管理私信交互！📨✨
