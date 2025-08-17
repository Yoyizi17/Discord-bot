# 🚨 Discord私信违规检测机器人

专为服务器管理员设计的违规监控工具，通过分析用户主动提交的Discord数据包来检测私信违规行为。

## 🎯 使用场景

- **服务器禁止私聊政策** - 监控成员是否违规私聊
- **合规性检查** - 定期检查成员的私信活动
- **透明管理** - 让成员主动提交合规报告
- **违规记录** - 完整记录和统计违规情况

## ✨ 功能特色

### 👥 **用户功能**
- **主动提交报告** - 上传Discord数据包进行合规检测
- **即时结果** - 立即显示检测结果和状态
- **隐私保护** - 只分析必要的联系人信息

### 👑 **管理员功能**
- **实时通知** - 新报告自动私信通知所有管理员
- **详细查看** - 查看任何用户的完整私信列表
- **批量管理** - 查看所有用户的合规报告列表
- **数据统计** - 私信数量、群聊数量等统计信息

### 🔒 **隐私与安全**
- **用户主动** - 成员自愿上传数据包
- **管理员专用** - 详细信息仅管理员可见
- **数据最小化** - 只存储必要的统计信息
- **本地存储** - 所有数据保存在机器人服务器

## 🎛️ 命令功能

### 👥 **用户命令**

#### `/submit_dm_report` - 提交合规报告
用户上传Discord数据包ZIP文件进行合规检测。

**使用方法：**
1. 申请Discord数据导出（设置 → 隐私与安全 → 申请我的数据）
2. 等待1-3天收到邮件
3. 下载ZIP文件
4. 使用此命令上传文件

### 👑 **管理员专用命令**

#### `/compliance_list [显示数量]` - 查看报告列表
显示所有用户提交的合规报告概览。

**显示信息：**
- 用户名和提交时间
- 私信记录数量
- 违规状态指示（🟢🟡🔴）

#### `/compliance_details @用户` - 查看详细报告
查看特定用户的完整私信合规报告。

**详细信息：**
- 私信用户完整列表
- 每个联系人的消息数量
- 群聊信息
- 最后活动时间

#### `/compliance_help` - 查看帮助
显示使用指南和命令说明。

## 🚀 部署指南

### 1. 创建Discord机器人

1. 访问 [Discord开发者门户](https://discord.com/developers/applications)
2. 创建新应用，命名为"违规检测机器人"
3. 创建Bot并复制TOKEN
4. 设置必要权限：
   - ✅ **Send Messages** - 发送消息
   - ✅ **Use Slash Commands** - 使用斜杠命令
   - ✅ **Read Message History** - 读取消息历史
   - ✅ **Send Messages in Threads** - 在线程中发送消息

### 2. 服务器部署

```bash
# 上传文件到服务器
scp dm_compliance_bot.py linuxuser@你的服务器IP:~/

# 连接到服务器
ssh linuxuser@你的服务器IP

# 创建项目目录
mkdir compliance-bot
cd compliance-bot
mv ~/dm_compliance_bot.py ./

# 安装依赖
pip3 install discord.py

# 配置TOKEN
nano dm_compliance_bot.py
# 替换 "你的违规检测机器人TOKEN" 为实际TOKEN

# 运行机器人
python3 dm_compliance_bot.py

# 后台运行（推荐）
screen -S compliance-bot python3 dm_compliance_bot.py
# 按 Ctrl+A+D 退出screen而不停止程序
```

### 3. 邀请机器人到服务器

使用OAuth2 URL Generator生成邀请链接：
- **Scopes**: `bot`, `applications.commands`
- **Bot Permissions**: Send Messages, Use Slash Commands, Read Message History

## 📋 使用流程

### 📝 **标准检查流程**

1. **发布检查通知**
   ```
   @everyone 请所有成员在24小时内提交私信合规报告
   使用 /submit_dm_report 命令上传你的Discord数据包
   ```

2. **成员提交报告**
   - 成员申请Discord数据导出
   - 下载ZIP文件并使用命令上传
   - 机器人自动分析并显示结果

3. **管理员审核**
   - 自动收到私信通知
   - 使用 `/compliance_list` 查看概览
   - 使用 `/compliance_details` 查看详情

4. **处理违规**
   - 根据检测结果采取行动
   - 记录保存在数据库中

### 🔍 **检测结果说明**

#### 状态指示：
- 🟢 **合规** - 0个私信记录
- 🟡 **轻微** - 1-4个私信记录  
- 🔴 **违规** - 5个以上私信记录

#### 检测内容：
- **私信用户列表** - 所有一对一私信的用户
- **群聊列表** - 参与的群组对话
- **消息统计** - 每个对话的消息数量
- **时间信息** - 最后活动时间

## 🗄️ 数据存储

### compliance_reports 表
- `user_id` - 用户Discord ID
- `username` - 用户名
- `guild_id` - 服务器ID
- `report_time` - 报告提交时间
- `dm_users_count` - 私信用户数量
- `dm_users_data` - 详细私信数据（JSON格式）
- `violation_status` - 违规状态
- `admin_notes` - 管理员备注

## 📊 管理建议

### 🎯 **制定明确政策**
```
服务器规则：
- 禁止成员之间私信交流
- 所有讨论必须在公开频道进行
- 每月需要提交一次合规报告
- 违规将根据严重程度处理
```

### 📅 **定期检查计划**
- **每周检查** - 新成员加入后7天内提交
- **每月检查** - 所有成员月度合规报告
- **随机检查** - 不定期抽查活跃成员

### ⚖️ **违规处理建议**
- **首次轻微违规** - 警告教育
- **重复违规** - 临时禁言
- **严重违规** - 踢出服务器
- **记录保存** - 所有检查结果存档

## 🔧 高级配置

### 自动化检查（可选）
可以配合定时任务定期提醒成员提交报告：

```python
# 添加到机器人的定时任务
@tasks.loop(hours=168)  # 每周运行
async def weekly_compliance_reminder():
    # 提醒所有成员提交报告
    pass
```

### 数据导出
```bash
# 导出合规报告数据
sqlite3 compliance_reports.db -header -csv "SELECT * FROM compliance_reports;" > compliance_export.csv
```

### 备份数据库
```bash
# 定期备份
cp compliance_reports.db compliance_backup_$(date +%Y%m%d).db
```

## ⚠️ 重要说明

### 法律和道德考量
- 确保符合当地隐私法律
- 明确告知成员检查目的
- 尊重用户隐私权
- 仅用于合规监控目的

### 技术限制
- 依赖用户主动提交数据包
- Discord数据导出需要1-3天处理时间
- 无法检测最新的私信活动

### 最佳实践
- 提前通知检查计划
- 提供清晰的操作指南
- 公平公正处理所有成员
- 保护举报者隐私

## 🎉 使用效果

通过这个机器人，你可以：

- ✅ **有效监控** - 实时了解成员私信情况
- ✅ **透明管理** - 所有检查过程公开透明
- ✅ **数据支撑** - 基于客观数据做出管理决策
- ✅ **违规威慑** - 定期检查形成有效威慑
- ✅ **合规文化** - 培养服务器合规意识

这是一个强大而实用的服务器管理工具，帮助你维护健康的社区环境！🚨✨
