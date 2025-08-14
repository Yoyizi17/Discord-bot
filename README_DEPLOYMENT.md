# Discord机器人 - Back4App部署指南

## 🚀 准备部署文件

已为Back4App部署准备了以下文件：
- ✅ `Procfile` - 告诉Back4App如何启动应用
- ✅ `runtime.txt` - 指定Python版本
- ✅ `requirements.txt` - 项目依赖
- ✅ `config.py` - 支持环境变量的配置
- ✅ `.gitignore` - 忽略不必要的文件

## 📋 部署步骤

### 1. 注册并设置Back4App

1. 访问 [Back4App](https://www.back4app.com/)
2. 注册账号并登录
3. 点击 **"Create a new app"**
4. 选择 **"Container as a Service"**
5. 给应用起个名字（如：discord-bot）

### 2. 连接GitHub仓库

1. 将你的代码推送到GitHub：
   ```bash
   git init
   git add .
   git commit -m "Discord bot for Back4App"
   git branch -M main
   git remote add origin https://github.com/你的用户名/你的仓库名.git
   git push -u origin main
   ```

2. 在Back4App中连接GitHub：
   - 选择 **"Connect with GitHub"**
   - 授权Back4App访问你的GitHub
   - 选择包含机器人代码的仓库

### 3. 配置环境变量

1. 在Back4App控制台中，进入你的应用
2. 点击 **"Settings"** → **"Config Vars"**
3. 添加环境变量：
   ```
   Key: BOT_TOKEN
   Value: 你的Discord机器人令牌
   ```

### 4. 部署应用

1. 在应用控制台点击 **"Deploy"**
2. 选择要部署的分支（通常是main）
3. 点击 **"Deploy"** 开始部署

### 5. 启动Worker

1. 部署完成后，进入 **"Resources"** 标签
2. 确保 **worker** 进程已启用
3. 如果显示为关闭状态，点击切换开关启用

## 🔍 检查部署状态

### 查看日志
1. 在Back4App控制台点击 **"Logs"**
2. 应该看到类似输出：
   ```
   [机器人名称] 已经成功启动！
   机器人ID: [ID号码]
   -----
   ```

### 测试机器人
1. 在Discord服务器中给任意消息添加反应
2. 机器人应该回复"收到啦~"
3. @机器人，应该回复"我在~"

## 🛠️ 故障排除

### 机器人未启动
- 检查 **Resources** 中worker是否启用
- 查看 **Logs** 是否有错误信息
- 确认 **Config Vars** 中BOT_TOKEN设置正确

### 权限错误
- 确保机器人在Discord服务器中有正确权限：
  - Send Messages
  - Read Message History  
  - Add Reactions

### 连接错误
- Back4App服务器网络通常比本地更稳定
- 如果仍有问题，检查Discord开发者门户中的机器人设置

## 💡 优势

✅ **免费部署** - Back4App提供免费套餐  
✅ **24/7运行** - 机器人持续在线  
✅ **自动重启** - 应用崩溃后自动重启  
✅ **日志监控** - 方便调试和监控  
✅ **环境变量** - 安全存储敏感信息  

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看Back4App的部署日志
2. 检查Discord开发者门户设置
3. 确认机器人权限配置正确

祝你部署成功！🎉
