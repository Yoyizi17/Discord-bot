# Discord机器人配置文件
import os

# 从环境变量获取Discord机器人令牌
# 本地开发时使用默认值，部署时使用环境变量

BOT_TOKEN = os.getenv('BOT_TOKEN', "你的机器人令牌放在这里")

# 部署到Back4App说明：
# 1. 在Back4App控制台的Settings -> Config Vars中添加：
#    BOT_TOKEN = 你的实际机器人令牌
# 2. 这样可以避免在代码中暴露敏感信息
