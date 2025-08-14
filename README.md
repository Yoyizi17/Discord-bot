# Discord 反应机器人

这是一个简单的Discord机器人，当用户给任何消息添加反应（emoji）时，机器人会自动回复"收到啦~"。

## 功能特点

- 💫 监听所有消息的反应添加事件
- 🤖 当有人添加反应时自动回复"收到啦~"
- 🛡️ 忽略机器人自己的反应，避免无限循环
- 📝 包含简单的测试命令（!hello 和 !ping）

## 安装步骤

### 1. 安装依赖

在命令提示符或PowerShell中运行：

```cmd
pip install -r requirements.txt
```

### 2. 创建Discord机器人

1. 访问 [Discord开发者门户](https://discord.com/developers/applications)
2. 点击"New Application"创建新应用
3. 给应用起个名字
4. 转到左侧的"Bot"部分
5. 点击"Add Bot"
6. 在"Token"部分点击"Copy"复制令牌

### 3. 配置机器人

1. 打开 `config.py` 文件
2. 将复制的令牌粘贴到 `BOT_TOKEN` 变量中：
   ```python
   BOT_TOKEN = "你复制的令牌粘贴在这里"
   ```

### 4. 邀请机器人到服务器

1. 在Discord开发者门户中，转到"OAuth2" > "URL Generator"
2. 在"Scopes"中勾选"bot"
3. 在"Bot Permissions"中勾选以下权限：
   - Send Messages（发送消息）
   - Read Message History（读取消息历史）
   - Add Reactions（添加反应）
4. 复制生成的URL并在浏览器中打开
5. 选择要邀请机器人的服务器

### 5. 运行机器人

在命令提示符或PowerShell中运行：

```cmd
python main.py
```

如果看到"[机器人名称] 已经成功启动！"的消息，说明机器人已经在线。

## 使用方法

1. 在Discord服务器的任何频道中发送一条消息
2. 给这条消息添加任意反应（emoji）
3. 机器人会自动回复"收到啦~"

## 测试命令

- `!hello` - 机器人会回复问候
- `!ping` - 显示机器人的延迟

## 注意事项

- ⚠️ **重要**：不要将包含真实token的config.py文件分享给他人或上传到公共代码仓库
- 🔒 机器人需要"读取消息历史"和"发送消息"权限才能正常工作
- 🚫 机器人不会对自己添加的反应做出响应，避免无限循环

## 故障排除

### 机器人无法启动
- 检查token是否正确复制到config.py中
- 确保已安装discord.py库：`pip install discord.py`

### 机器人不响应反应
- 确认机器人有"读取消息历史"权限
- 确认机器人有"发送消息"权限
- 检查机器人是否在线（在Discord中应显示为在线状态）

### 权限错误
- 确保机器人角色拥有足够的权限
- 检查频道特定的权限设置

## 自定义

你可以修改 `main.py` 中的以下内容：
- 将 `"收到啦~"` 改为其他回复内容
- 添加更多的命令和功能
- 修改机器人的行为逻辑

享受你的Discord机器人吧！🎉
