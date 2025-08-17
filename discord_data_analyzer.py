#!/usr/bin/env python3
"""
Discord数据分析工具
分析Discord官方数据导出包，提取私信用户列表和统计信息
"""

import json
import os
import zipfile
import csv
from datetime import datetime
from collections import defaultdict, Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

class DiscordDataAnalyzer:
    def __init__(self):
        self.data_path = None
        self.messages_data = {}
        self.dm_users = []
        self.statistics = {}
        
    def select_data_package(self):
        """选择Discord数据包"""
        print("📦 请选择Discord数据包...")
        print("💡 支持格式: .zip文件 或 解压后的文件夹")
        
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 先尝试选择ZIP文件
        zip_file = filedialog.askopenfilename(
            title="选择Discord数据包ZIP文件",
            filetypes=[("ZIP文件", "*.zip"), ("所有文件", "*.*")]
        )
        
        if zip_file:
            self.data_path = zip_file
            return True
            
        # 如果没选ZIP，选择文件夹
        folder = filedialog.askdirectory(
            title="选择解压后的Discord数据文件夹"
        )
        
        if folder:
            self.data_path = folder
            return True
            
        return False
    
    def extract_and_analyze(self):
        """提取并分析数据"""
        if not self.data_path:
            print("❌ 未选择数据包")
            return False
            
        print(f"📂 分析数据包: {self.data_path}")
        
        try:
            if self.data_path.endswith('.zip'):
                return self.analyze_zip_package()
            else:
                return self.analyze_folder_package()
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return False
    
    def analyze_zip_package(self):
        """分析ZIP数据包"""
        with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
            # 查找messages文件夹
            message_files = [f for f in zip_ref.namelist() if f.startswith('messages/') and f.endswith('.json')]
            
            if not message_files:
                print("❌ 在数据包中未找到messages文件夹")
                return False
            
            print(f"📨 找到 {len(message_files)} 个消息文件")
            
            # 分析每个消息文件
            for file_path in message_files:
                try:
                    with zip_ref.open(file_path) as f:
                        data = json.load(f)
                        self.analyze_message_file(file_path, data)
                except Exception as e:
                    print(f"⚠️  读取文件 {file_path} 失败: {e}")
            
            return True
    
    def analyze_folder_package(self):
        """分析文件夹数据包"""
        messages_folder = os.path.join(self.data_path, 'messages')
        
        if not os.path.exists(messages_folder):
            print("❌ 未找到messages文件夹")
            return False
        
        # 获取所有JSON文件
        json_files = []
        for root, dirs, files in os.walk(messages_folder):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print("❌ 在messages文件夹中未找到JSON文件")
            return False
        
        print(f"📨 找到 {len(json_files)} 个消息文件")
        
        # 分析每个消息文件
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.analyze_message_file(file_path, data)
            except Exception as e:
                print(f"⚠️  读取文件 {file_path} 失败: {e}")
        
        return True
    
    def analyze_message_file(self, file_path, data):
        """分析单个消息文件"""
        if 'messages' not in data:
            return
        
        messages = data['messages']
        if not messages:
            return
        
        # 获取频道信息
        channel_info = {
            'id': data.get('id', '未知'),
            'type': data.get('type', 0),
            'name': data.get('name', ''),
            'recipients': data.get('recipients', [])
        }
        
        # 判断是否为私信频道 (type=1为DM, type=3为群聊)
        if channel_info['type'] in [1, 3]:
            self.process_dm_channel(file_path, channel_info, messages)
    
    def process_dm_channel(self, file_path, channel_info, messages):
        """处理私信频道"""
        recipients = channel_info.get('recipients', [])
        
        # 获取对话用户信息
        if channel_info['type'] == 1:  # 私信
            if recipients:
                user_info = recipients[0]
            else:
                # 从文件名提取用户信息
                filename = os.path.basename(file_path)
                user_info = {'username': filename.replace('.json', ''), 'id': 'unknown'}
        else:  # 群聊
            user_info = {
                'username': channel_info.get('name', '群聊'),
                'id': channel_info['id'],
                'is_group': True
            }
        
        # 统计消息
        message_count = len(messages)
        if message_count == 0:
            return
        
        # 获取时间范围
        timestamps = [msg.get('timestamp', '') for msg in messages if msg.get('timestamp')]
        first_message = min(timestamps) if timestamps else ''
        last_message = max(timestamps) if timestamps else ''
        
        # 统计消息发送者
        author_stats = Counter()
        for msg in messages:
            author = msg.get('author', {})
            author_name = author.get('username', '未知')
            author_stats[author_name] += 1
        
        # 添加到用户列表
        dm_user = {
            'username': user_info.get('username', '未知'),
            'display_name': user_info.get('global_name') or user_info.get('username', '未知'),
            'user_id': user_info.get('id', '未知'),
            'channel_id': channel_info['id'],
            'channel_type': '群聊' if channel_info['type'] == 3 else '私信',
            'message_count': message_count,
            'first_message': first_message,
            'last_message': last_message,
            'author_stats': dict(author_stats),
            'file_path': file_path
        }
        
        self.dm_users.append(dm_user)
        print(f"✅ 处理: {dm_user['username']} ({message_count} 条消息)")
    
    def generate_statistics(self):
        """生成统计信息"""
        if not self.dm_users:
            return
        
        total_users = len(self.dm_users)
        total_messages = sum(user['message_count'] for user in self.dm_users)
        
        # 按消息数量排序
        top_users = sorted(self.dm_users, key=lambda x: x['message_count'], reverse=True)[:10]
        
        # 按时间统计
        dm_users_only = [u for u in self.dm_users if u['channel_type'] == '私信']
        group_chats = [u for u in self.dm_users if u['channel_type'] == '群聊']
        
        self.statistics = {
            'total_users': total_users,
            'total_messages': total_messages,
            'dm_users_count': len(dm_users_only),
            'group_chats_count': len(group_chats),
            'top_users': top_users,
            'avg_messages': total_messages / total_users if total_users > 0 else 0
        }
    
    def print_results(self):
        """打印分析结果"""
        print("\n" + "="*60)
        print("📊 Discord私信分析结果")
        print("="*60)
        
        if not self.dm_users:
            print("❌ 未找到私信数据")
            return
        
        stats = self.statistics
        print(f"👥 总用户数: {stats['total_users']}")
        print(f"💬 总消息数: {stats['total_messages']:,}")
        print(f"📨 私信用户: {stats['dm_users_count']}")
        print(f"👨‍👩‍👧‍👦 群聊数量: {stats['group_chats_count']}")
        print(f"📈 平均消息数: {stats['avg_messages']:.1f} 条/用户")
        
        print(f"\n🏆 消息最多的用户 (前10名):")
        for i, user in enumerate(stats['top_users'], 1):
            print(f"{i:2d}. {user['username']:20} - {user['message_count']:,} 条消息")
        
        print(f"\n📋 完整用户列表:")
        for i, user in enumerate(self.dm_users, 1):
            last_date = user['last_message'][:10] if user['last_message'] else '未知'
            print(f"{i:3d}. {user['username']:25} | {user['message_count']:6,} 条 | {user['channel_type']} | {last_date}")
    
    def export_to_csv(self, filename=None):
        """导出为CSV文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discord_dm_users_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                '序号', '用户名', '显示名', '用户ID', '频道ID', '类型', 
                '消息数量', '首次消息时间', '最后消息时间', '文件路径'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for i, user in enumerate(self.dm_users, 1):
                writer.writerow({
                    '序号': i,
                    '用户名': user['username'],
                    '显示名': user['display_name'],
                    '用户ID': user['user_id'],
                    '频道ID': user['channel_id'],
                    '类型': user['channel_type'],
                    '消息数量': user['message_count'],
                    '首次消息时间': user['first_message'],
                    '最后消息时间': user['last_message'],
                    '文件路径': user['file_path']
                })
        
        print(f"✅ 数据已导出到: {filename}")
    
    def export_to_json(self, filename=None):
        """导出为JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discord_dm_analysis_{timestamp}.json"
        
        export_data = {
            'analysis_time': datetime.now().isoformat(),
            'statistics': self.statistics,
            'dm_users': self.dm_users
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 完整数据已导出到: {filename}")
    
    def create_html_report(self, filename=None):
        """创建HTML报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discord_dm_report_{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord私信分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #5865f2; text-align: center; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #5865f2; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #5865f2; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #5865f2; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .channel-type {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
        .dm {{ background: #57f287; color: #000; }}
        .group {{ background: #faa61a; color: #000; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📨 Discord私信分析报告</h1>
        <p style="text-align: center; color: #666;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{self.statistics['total_users']}</div>
                <div>总用户数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.statistics['total_messages']:,}</div>
                <div>总消息数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.statistics['dm_users_count']}</div>
                <div>私信用户</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.statistics['group_chats_count']}</div>
                <div>群聊数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.statistics['avg_messages']:.1f}</div>
                <div>平均消息数</div>
            </div>
        </div>
        
        <h2>📋 完整用户列表</h2>
        <table>
            <thead>
                <tr>
                    <th>序号</th>
                    <th>用户名</th>
                    <th>显示名</th>
                    <th>类型</th>
                    <th>消息数量</th>
                    <th>最后消息时间</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, user in enumerate(self.dm_users, 1):
            channel_type_class = "dm" if user['channel_type'] == '私信' else "group"
            last_date = user['last_message'][:10] if user['last_message'] else '未知'
            
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{user['username']}</td>
                    <td>{user['display_name']}</td>
                    <td><span class="channel-type {channel_type_class}">{user['channel_type']}</span></td>
                    <td>{user['message_count']:,}</td>
                    <td>{last_date}</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <p>💡 此报告由Discord数据分析工具生成</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML报告已生成: {filename}")
        
        # 自动打开报告
        try:
            webbrowser.open(f'file://{os.path.abspath(filename)}')
        except:
            pass

def main():
    """主函数"""
    print("🎯 Discord数据分析工具")
    print("="*50)
    print("📋 此工具可以分析Discord官方数据导出包")
    print("💡 获取数据导出包的方法:")
    print("   1. Discord设置 → 隐私与安全")
    print("   2. 点击'申请我的数据'")
    print("   3. 等待邮件通知并下载ZIP文件")
    print("")
    
    analyzer = DiscordDataAnalyzer()
    
    # 选择数据包
    if not analyzer.select_data_package():
        print("❌ 未选择数据包，程序退出")
        return
    
    # 分析数据
    print("\n🔍 开始分析数据...")
    if not analyzer.extract_and_analyze():
        print("❌ 数据分析失败")
        return
    
    # 生成统计
    analyzer.generate_statistics()
    
    # 显示结果
    analyzer.print_results()
    
    # 导出数据
    print(f"\n💾 导出数据...")
    analyzer.export_to_csv()
    analyzer.export_to_json()
    analyzer.create_html_report()
    
    print(f"\n✅ 分析完成！")
    print(f"📊 已生成CSV、JSON和HTML报告文件")
    
    input("\n按回车键退出...")

if __name__ == '__main__':
    main()
