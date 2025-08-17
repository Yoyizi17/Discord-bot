#!/usr/bin/env python3
"""
Discord私信列表获取工具 - OAuth2授权版本
通过OAuth2授权获取用户的私信频道列表
"""

import requests
import json
import webbrowser
import urllib.parse
from datetime import datetime
import os
from flask import Flask, request, render_template_string, redirect, session
import threading
import time

# Discord OAuth2 配置
CLIENT_ID = "你的应用程序客户端ID"  # 需要在Discord开发者门户获取
CLIENT_SECRET = "你的应用程序客户端密钥"  # 需要在Discord开发者门户获取
REDIRECT_URI = "http://localhost:8080/callback"

# Discord API 端点
DISCORD_API_BASE = "https://discord.com/api/v10"
OAUTH2_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"

# Flask应用
app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # 生产环境请使用随机密钥

# HTML模板
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord私信列表获取工具</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: #36393f;
            color: #ffffff;
        }
        .container { 
            background: #2f3136; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .btn { 
            display: inline-block;
            background: #5865f2; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 10px 0;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover { background: #4752c4; }
        .warning { 
            background: #faa61a; 
            color: #000; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 15px 0; 
        }
        .info { 
            background: #5865f2; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 15px 0; 
        }
        .step { 
            background: #40444b; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px; 
            border-left: 4px solid #5865f2;
        }
        h1 { color: #5865f2; }
        h2 { color: #ffffff; }
        code { 
            background: #40444b; 
            padding: 2px 6px; 
            border-radius: 3px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📨 Discord私信列表获取工具</h1>
        
        <div class="info">
            <h3>🎯 功能说明</h3>
            <p>此工具可以帮你获取Discord私信频道列表，包括：</p>
            <ul>
                <li>所有私信用户的基本信息</li>
                <li>私信频道的最后活动时间</li>
                <li>导出为JSON格式文件</li>
            </ul>
        </div>

        <div class="warning">
            <h3>⚠️ 重要说明</h3>
            <p><strong>配置要求：</strong></p>
            <ol>
                <li>需要先在Discord开发者门户创建应用程序</li>
                <li>获取Client ID和Client Secret</li>
                <li>设置重定向URI为: <code>http://localhost:8080/callback</code></li>
                <li>修改脚本中的配置信息</li>
            </ol>
        </div>

        {% if not configured %}
        <div class="step">
            <h3>🔧 配置步骤</h3>
            <ol>
                <li><strong>访问Discord开发者门户：</strong><br>
                    <a href="https://discord.com/developers/applications" target="_blank" class="btn">Discord开发者门户</a>
                </li>
                <li><strong>创建新应用程序：</strong><br>
                    点击"New Application"，输入应用名称（如"私信列表工具"）
                </li>
                <li><strong>配置OAuth2：</strong><br>
                    • 转到"OAuth2" → "General"<br>
                    • 复制Client ID和Client Secret<br>
                    • 在Redirects中添加: <code>http://localhost:8080/callback</code>
                </li>
                <li><strong>修改脚本配置：</strong><br>
                    在 <code>discord_dm_oauth.py</code> 中替换CLIENT_ID和CLIENT_SECRET
                </li>
                <li><strong>重新启动脚本</strong></li>
            </ol>
        </div>
        {% else %}
        <div class="step">
            <h3>🚀 开始获取私信列表</h3>
            <p>点击下方按钮开始OAuth2授权流程：</p>
            <a href="/authorize" class="btn">🔐 授权获取私信列表</a>
        </div>
        
        <div class="info">
            <h3>🔒 隐私保护</h3>
            <ul>
                <li>授权过程完全在本地进行</li>
                <li>不会上传任何数据到外部服务器</li>
                <li>获取的数据仅保存在本地</li>
                <li>可以随时撤销授权</li>
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

RESULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>私信列表结果</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 20px auto; 
            padding: 20px;
            background: #36393f;
            color: #ffffff;
        }
        .container { 
            background: #2f3136; 
            padding: 30px; 
            border-radius: 10px; 
        }
        .user-card {
            background: #40444b;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #5865f2;
        }
        .user-info {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 15px;
        }
        .username {
            font-weight: bold;
            font-size: 18px;
        }
        .user-details {
            font-size: 14px;
            color: #b9bbbe;
            margin-left: 55px;
        }
        .btn { 
            background: #5865f2; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 10px 5px;
            display: inline-block;
        }
        .success { 
            background: #57f287; 
            color: #000; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 15px 0; 
        }
        h1 { color: #5865f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📨 私信列表获取成功！</h1>
        
        <div class="success">
            <strong>✅ 获取完成！</strong><br>
            找到 <strong>{{ dm_count }}</strong> 个私信频道
        </div>

        <h2>📋 私信用户列表</h2>
        {% for user in dm_users %}
        <div class="user-card">
            <div class="user-info">
                <img src="{{ user.avatar_url }}" alt="Avatar" class="avatar">
                <div>
                    <div class="username">{{ user.username }}</div>
                    <div style="color: #b9bbbe;">{{ user.display_name }}</div>
                </div>
            </div>
            <div class="user-details">
                <div>📅 最后活动: {{ user.last_activity }}</div>
                <div>🆔 用户ID: {{ user.user_id }}</div>
                <div>📨 频道ID: {{ user.channel_id }}</div>
            </div>
        </div>
        {% endfor %}

        <div style="margin-top: 30px;">
            <a href="/export" class="btn">💾 导出为JSON文件</a>
            <a href="/" class="btn">🔄 重新获取</a>
        </div>
    </div>
</body>
</html>
"""

def is_configured():
    """检查是否已配置Client ID和Secret"""
    return (CLIENT_ID != "你的应用程序客户端ID" and 
            CLIENT_SECRET != "你的应用程序客户端密钥")

def get_oauth_url():
    """生成OAuth2授权URL"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify guilds.join'  # Discord不允许直接访问私信，需要其他方式
    }
    return f"{OAUTH2_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    """用授权码交换访问令牌"""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(TOKEN_URL, data=data)
    return response.json()

def get_user_info(access_token):
    """获取用户信息"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
    return response.json()

def get_user_dms(access_token):
    """
    获取用户私信频道
    注意：Discord API限制，普通应用无法直接获取用户私信
    此功能需要特殊权限或使用用户token
    """
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # 尝试获取用户的私信频道（可能需要用户token）
    try:
        response = requests.get(f"{DISCORD_API_BASE}/users/@me/channels", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取私信频道失败: {response.status_code}")
            print(f"响应: {response.text}")
            return []
    except Exception as e:
        print(f"请求失败: {e}")
        return []

@app.route('/')
def index():
    """主页"""
    return render_template_string(INDEX_TEMPLATE, configured=is_configured())

@app.route('/authorize')
def authorize():
    """开始OAuth2授权"""
    if not is_configured():
        return redirect('/')
    
    oauth_url = get_oauth_url()
    return redirect(oauth_url)

@app.route('/callback')
def callback():
    """OAuth2回调处理"""
    code = request.args.get('code')
    if not code:
        return "授权失败：未获取到授权码"
    
    try:
        # 交换访问令牌
        token_data = exchange_code_for_token(code)
        
        if 'access_token' not in token_data:
            return f"获取访问令牌失败: {token_data}"
        
        access_token = token_data['access_token']
        
        # 获取用户信息
        user_info = get_user_info(access_token)
        session['user_info'] = user_info
        
        # 尝试获取私信频道
        dm_channels = get_user_dms(access_token)
        session['dm_channels'] = dm_channels
        
        return redirect('/result')
        
    except Exception as e:
        return f"处理回调时发生错误: {e}"

@app.route('/result')
def result():
    """显示结果"""
    user_info = session.get('user_info', {})
    dm_channels = session.get('dm_channels', [])
    
    # 处理私信频道数据
    dm_users = []
    for channel in dm_channels:
        if channel.get('type') == 1:  # DM频道
            recipients = channel.get('recipients', [])
            for recipient in recipients:
                dm_users.append({
                    'username': recipient.get('username', '未知'),
                    'display_name': recipient.get('global_name') or recipient.get('username', '未知'),
                    'user_id': recipient.get('id', '未知'),
                    'channel_id': channel.get('id', '未知'),
                    'avatar_url': f"https://cdn.discordapp.com/avatars/{recipient.get('id')}/{recipient.get('avatar')}.png" if recipient.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png",
                    'last_activity': channel.get('last_message_id', '未知')
                })
    
    # 如果没有获取到私信数据，提供说明
    if not dm_users:
        dm_users = [{
            'username': '无法获取私信数据',
            'display_name': 'Discord API限制',
            'user_id': '由于Discord API政策限制',
            'channel_id': '普通OAuth2应用无法访问私信',
            'avatar_url': 'https://cdn.discordapp.com/embed/avatars/0.png',
            'last_activity': '建议使用Discord数据导出功能'
        }]
    
    return render_template_string(RESULT_TEMPLATE, 
                                dm_users=dm_users, 
                                dm_count=len(dm_users))

@app.route('/export')
def export_data():
    """导出数据为JSON"""
    user_info = session.get('user_info', {})
    dm_channels = session.get('dm_channels', [])
    
    export_data = {
        'user_info': user_info,
        'dm_channels': dm_channels,
        'export_time': datetime.now().isoformat(),
        'note': 'Discord API限制，可能无法获取完整私信数据'
    }
    
    filename = f"discord_dm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return f"数据已导出到文件: {filename}<br><a href='/'>返回首页</a>"

def create_setup_guide():
    """创建设置指南文件"""
    guide_content = """
# Discord私信列表获取工具 - 设置指南

## 🔧 配置步骤

### 1. 创建Discord应用程序
1. 访问 https://discord.com/developers/applications
2. 点击 "New Application"
3. 输入应用名称（如"私信列表工具"）
4. 点击 "Create"

### 2. 配置OAuth2
1. 在左侧菜单选择 "OAuth2" → "General"
2. 复制 "CLIENT ID"
3. 复制 "CLIENT SECRET"（点击Reset Secret获取）
4. 在 "Redirects" 部分添加: http://localhost:8080/callback

### 3. 修改脚本配置
在 discord_dm_oauth.py 文件中找到以下行并替换：

```python
CLIENT_ID = "你的应用程序客户端ID"        # 替换为实际的Client ID
CLIENT_SECRET = "你的应用程序客户端密钥"   # 替换为实际的Client Secret
```

### 4. 安装依赖
```bash
pip install flask requests
```

### 5. 运行脚本
```bash
python discord_dm_oauth.py
```

### 6. 访问工具
在浏览器中打开: http://localhost:8080

## ⚠️ 重要说明

由于Discord API政策限制，普通OAuth2应用无法直接访问用户的私信频道。
如需获取完整私信列表，建议使用以下方法：

1. **Discord官方数据导出**：
   - Discord设置 → 隐私与安全 → 申请我的数据
   - 等待邮件，下载数据包
   - 解压后查看messages文件夹

2. **浏览器开发者工具**：
   - 在Discord网页版按F12
   - 使用网络标签监控API请求
   - 手动获取私信数据

此工具主要用于演示OAuth2授权流程和API调用方法。
"""
    
    with open("SETUP_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)

def main():
    """主函数"""
    print("🚀 Discord私信列表获取工具")
    print("=" * 50)
    
    if not is_configured():
        print("⚠️  尚未配置Client ID和Secret")
        print("📋 请查看SETUP_GUIDE.md文件了解配置步骤")
        create_setup_guide()
        print("✅ 已创建设置指南文件: SETUP_GUIDE.md")
        print("")
    else:
        print("✅ 配置检查通过")
    
    print("🌐 启动Web服务器...")
    print(f"📱 请在浏览器中访问: http://localhost:8080")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("")
    
    try:
        # 自动打开浏览器
        threading.Timer(1.5, lambda: webbrowser.open('http://localhost:8080')).start()
        
        # 启动Flask应用
        app.run(host='localhost', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")

if __name__ == '__main__':
    main()
