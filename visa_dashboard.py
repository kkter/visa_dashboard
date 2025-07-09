import sqlite3
import pandas as pd
import json
import re
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import threading
import time
import os # <-- 1. 增加 os 模块导入

# 数据库配置
DB_NAME = "data/visas.db"
TABLE_NAME = "visa_decisions"

app = Flask(__name__)

def format_date_range_chinese(start_date, end_date):
    """将日期范围格式化为中文显示"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 月份映射
        month_map = {
            1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月',
            7: '7月', 8: '8月', 9: '9月', 10: '10月', 11: '11月', 12: '12月'
        }
        
        start_month_cn = month_map[start.month]
        end_month_cn = month_map[end.month]
        
        if start.month == end.month:
            return f"{start_month_cn}{start.day}日-{end.day}日"
        else:
            return f"{start_month_cn}{start.day}日-{end_month_cn}{end.day}日"
    except:
        return f"{start_date} 至 {end_date}"

def get_date_range():
    """获取数据的日期范围"""
    try:
        conn = sqlite3.connect(DB_NAME)
        query = f"SELECT MIN(date_range_start) as min_date, MAX(date_range_end) as max_date FROM {TABLE_NAME}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty or df['min_date'].isna().any():
            return "暂无数据", "暂无数据"
        
        min_date = df['min_date'].iloc[0]
        max_date = df['max_date'].iloc[0]
        
        if min_date and max_date:
            start_str = datetime.strptime(min_date, '%Y-%m-%d').strftime('%Y年%m月%d日')
            end_str = datetime.strptime(max_date, '%Y-%m-%d').strftime('%Y年%m月%d日')
            return start_str, end_str
        else:
            return "数据解析中", "数据解析中"
            
    except Exception as e:
        print(f"获取日期范围时发生错误: {e}")
        return "未知", "未知"

def get_visa_data():
    """从数据库获取签证数据"""
    try:
        conn = sqlite3.connect(DB_NAME)
        query = f"SELECT application_number, decision, source_file, date_range_start, date_range_end FROM {TABLE_NAME}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 获取日期范围
        start_date, end_date = get_date_range()
        
        if df.empty:
            return {
                'labels': [],
                'total_applications': [],
                'refused_count': [],
                'refusal_rate': [],
                'summary': {
                    'total_apps': 0,
                    'total_refused': 0,
                    'avg_refusal_rate': 0,
                    'start_date': start_date,
                    'end_date': end_date
                    # 移除这里的 last_updated，因为它将由新的API提供
                    # 'last_updated': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                }
            }
        
        # 使用数据库中的日期范围创建周期标签
        df['week'] = df.apply(lambda row: format_date_range_chinese(row['date_range_start'], row['date_range_end']), axis=1)
        
        # 按周统计
        weekly_stats = df.groupby(['week', 'decision']).size().unstack(fill_value=0)
        
        # 计算总申请数和拒签率
        weekly_stats['total_applications'] = weekly_stats.sum(axis=1)
        weekly_stats['refused_count'] = weekly_stats.get('Refused', 0)
        weekly_stats['approved_count'] = weekly_stats.get('Approved', 0)
        weekly_stats['refusal_rate'] = (weekly_stats['refused_count'] / weekly_stats['total_applications'] * 100).round(2)
        
        # 按日期排序 - 使用原始数据的date_range_start进行排序
        df_for_sort = df[['week', 'date_range_start']].drop_duplicates().sort_values('date_range_start')
        sorted_weeks = df_for_sort['week'].tolist()
        weekly_stats = weekly_stats.reindex(sorted_weeks)
        
        # 准备返回数据
        data = {
            'labels': weekly_stats.index.tolist(),
            'total_applications': weekly_stats['total_applications'].tolist(),
            'refused_count': weekly_stats['refused_count'].tolist(),
            'refusal_rate': weekly_stats['refusal_rate'].tolist(),
            'summary': {
                'total_apps': int(weekly_stats['total_applications'].sum()),
                'total_refused': int(weekly_stats['refused_count'].sum()),
                'avg_refusal_rate': round(weekly_stats['refusal_rate'].mean(), 1),
                'start_date': start_date,
                'end_date': end_date
                # 移除这里的 last_updated，因为它将由新的API提供
                # 'last_updated': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
            }
        }
        
        return data
        
    except Exception as e:
        print(f"获取数据时发生错误: {e}")
        start_date, end_date = get_date_range()
        return {
            'labels': [],
            'total_applications': [],
            'refused_count': [],
            'refusal_rate': [],
            'summary': {
                'total_apps': 0,
                'total_refused': 0,
                'avg_refusal_rate': 0,
                'start_date': start_date,
                'end_date': end_date
                # 移除这里的 last_updated
                # 'last_updated': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
            }
        }

@app.route('/')
def dashboard():
    """主页面"""
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    """API接口：获取最新数据"""
    data = get_visa_data()
    return jsonify(data)

# --- 2. 新增一个API接口，专门用于获取数据库文件更新时间 ---
@app.route('/api/last_update')
def get_last_update_time():
    """获取数据库文件的最后修改时间"""
    try:
        mtime = os.path.getmtime(DB_NAME)
        last_update_dt = datetime.fromtimestamp(mtime)
        last_update_str = last_update_dt.strftime('%Y年%m月%d日 %H:%M:%S')
        return jsonify({'last_update_time': last_update_str})
    except Exception as e:
        print(f"获取最后更新时间失败: {e}") # 在服务器端打印错误日志
        return jsonify({'last_update_time': '无法获取'})

@app.route('/api/search')
def api_search():
    """API接口：查询申请号"""
    app_number = request.args.get('app_number', '').strip()
    
    if not app_number:
        return jsonify({
            'success': False,
            'message': '请输入申请号'
        })
    
    if not app_number.isdigit():
        return jsonify({
            'success': False,
            'message': '申请号应为数字'
        })
    
    try:
        conn = sqlite3.connect(DB_NAME)
        query = f"""
        SELECT application_number, decision, source_file, date_range_start, date_range_end, processed_date 
        FROM {TABLE_NAME} 
        WHERE application_number = ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (int(app_number),))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({
                'success': False,
                'message': f'未找到申请号 {app_number} 的记录'
            })
        
        # 处理结果（可能有多条记录，因为同一个申请号可能在不同文件中出现）
        formatted_results = []
        for row in results:
            app_num, decision, source_file, date_start, date_end, processed_date = row
            week_info = format_date_range_chinese(date_start, date_end)
            formatted_results.append({
                'application_number': app_num,
                'decision': decision,
                'week': week_info,
                'source_file': source_file,
                'processed_date': processed_date
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询时发生错误: {str(e)}'
        })

def create_template():
    """创建HTML模板"""
    template_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- 1. SEO 优化：添加核心 Meta 标签 -->
    <title>爱尔兰签证结果查询与每周数据统计 - 353bbs.com 论坛工具</title>
    <meta name="description" content="一个为 353bbs 论坛网友提供的爱尔兰签证结果在线查询工具。输入申请编号即可查询最新签证状态，并查看每周签证申请数量、拒签数量和拒签率的统计图表。">
    <meta name="keywords" content="爱尔兰签证, 签证查询, 签证结果, 353bbs, 签证统计, 拒签率, Visa Decision">
    <meta name="author" content="353bbs.com">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script defer src="https://umami.520353.xyz/demo.js" data-website-id="ddcdb9ee-21d1-4974-8bbd-7a694858fb60"></script>
    
    

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'SF Pro Display', 'Segoe UI', system-ui, sans-serif;
            /* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
            background: linear-gradient(135deg, #1b6f54 0%, #2c9678 50%, #4ed1a0 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            animation: fadeInDown 0.8s ease;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }

        .search-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 25px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: fadeInUp 0.8s ease 0.1s both;
        }

        .search-title {
            font-size: 2rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
        }

        .search-form {
            display: flex;
            gap: 15px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }

        .search-input {
            padding: 12px 20px;
            border: 2px solid #e1e8ed;
            border-radius: 25px;
            font-size: 1rem;
            width: 300px;
            transition: all 0.3s ease;
            outline: none;
        }

        .search-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .search-btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #2c9678, #1b6f54);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 100px;
        }

        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(44, 150, 120, 0.3);
        }

        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .search-result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 15px;
            display: none;
        }

        .search-result.success {
            background: rgba(46, 204, 113, 0.1);
            border: 1px solid rgba(46, 204, 113, 0.3);
        }

        .search-result.error {
            background: rgba(231, 76, 60, 0.1);
            border: 1px solid rgba(231, 76, 60, 0.3);
        }

        .result-item {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }

        .result-item:last-child {
            margin-bottom: 0;
        }

        .result-decision {
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 15px;
        }

        .result-decision.approved {
            color: #2ecc71;
        }

        .result-decision.refused {
            color: #e74c3c;
        }

        .result-app-number {
            font-size: 1.2rem;
            color: #666;
            font-weight: 600;
        }

        .result-disclaimer {
            background: rgba(52, 152, 219, 0.1);
            border: 1px solid rgba(52, 152, 219, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9rem;
            color: #2980b9;
            text-align: center;
            line-height: 1.5;
        }

        .data-info {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: fadeInUp 0.8s ease 0.15s both;
            text-align: center;
        }

        .data-info h2 {
            color: #2c3e50;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 25px;
        }

        .date-range {
            font-size: 1.5rem;
            color: #2c9678;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .disclaimer {
            font-size: 0.95rem;
            color: #7f8c8d;
            line-height: 1.6;
            margin-top: 10px;
        }

        .stats-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 0px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: fadeInUp 0.8s ease 0.2s both;
        }

        .stats-title {
            text-align: center;
            color: #2c3e50;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 30px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            transition: all 0.4s cubic-bezier(0.23, 1, 0.320, 1);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .stat-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }

        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
            opacity: 0.8;
        }

        .material-icons.md-18 { font-size: 18px; }
        .material-icons.md-24 { font-size: 24px; }
        .material-icons.md-36 { font-size: 36px; }
        .material-icons.md-48 { font-size: 48px; }

        .stat-number {
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--color-1), var(--color-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            color: #666;
            font-size: 1.1rem;
            font-weight: 500;
        }

        .stat-card:nth-child(1) { --color-1: #3498db; --color-2: #2980b9; }
        .stat-card:nth-child(2) { --color-1: #e74c3c; --color-2: #c0392b; }
        .stat-card:nth-child(3) { --color-1: #f39c12; --color-2: #e67e22; }

        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 25px;
            padding: 35px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: fadeInUp 0.8s ease 0.4s both;
            position: relative;
            overflow: hidden;
        }

        .chart-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 25px;
            text-align: center;
        }

        .chart-wrapper {
            position: relative;
            height: 500px;
            background: rgba(255, 255, 255, 1);
            border-radius: 15px;
            padding: 20px;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
            animation: fadeIn 1s ease 0.6s both;
        }

        .footer p {
            margin: 5px 0;
        }

        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            color: #666;
            flex-direction: column;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translate3d(0, -100px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translate3d(0, 100px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.2rem;
            }
            
            .stat-number {
                font-size: 2.2rem;
            }

            .chart-wrapper {
                height: 400px;
            }

            body {
                padding: 15px;
            }

            .search-form {
                flex-direction: column;
            }

            .search-input {
                width: 100%;
            }

            .stats-title {
                font-size: 1.8rem;
            }

            .data-info h2 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>爱尔兰签证结果查询与统计</h1>
            <!-- 1. 移除此处的描述性段落 -->
        </div>

        <!-- 数据信息说明 -->
        <div class="data-info">
            <h2>数据范围</h2>
            <div class="date-range" id="dataRange">加载中...</div>
            <div class="disclaimer">
                ⚠️ <strong>重要声明：</strong>本页面数据仅供参考，所有签证申请结果以官方发布信息为准。查询结果可能存在延迟或遗漏，请以官方渠道获取的信息为最终依据。
            </div>
        </div>
        
        <!-- 查询功能 -->
        <div class="search-section">
            <div class="search-title">🔍 签证结果查询</div>
            <div class="search-form">
                <!-- 3. SEO 优化：为输入框添加更明确的 aria-label -->
                <input type="text" id="searchInput" class="search-input" placeholder="请输入申请编号 (例如: 7162****)" maxlength="15" aria-label="爱尔兰签证申请编号输入框">
                <button id="searchBtn" class="search-btn">查询</button>
            </div>
            <div id="searchResult" class="search-result"></div>
        </div>

        <!-- 统计数据部分 -->
        <div class="stats-section">
            <div class="stats-title">签证结果统计</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <!--div class="stat-icon">📈</div-->
                    <div class="stat-number" id="totalApps">-</div>
                    <div class="stat-label">总申请数</div>
                </div>
                <div class="stat-card">
                    <!--div class="stat-icon">❌</div-->
                    <div class="stat-number" id="totalRefused">-</div>
                    <div class="stat-label">拒签数量</div>
                </div>
                <div class="stat-card">
                    <!--div class="stat-icon">📊</div-->
                    <div class="stat-number" id="avgRefusalRate">-</div>
                    <div class="stat-label">拒签率</div>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">申请数量与拒签率</div>
            <div class="chart-wrapper">
                <div class="loading" id="loadingChart">
                    <div class="spinner"></div>
                    <p>正在加载图表数据...</p>
                </div>
                <canvas id="trendChart" style="display: none;"></canvas>
            </div>
        </div>
        
        <div class="footer">
            <p id="lastUpdated">数据最后更新: 加载中...</p>
            <br>
            <!-- 2. 在页脚添加版权信息 -->
            <p>&copy; 2025 <a href="https://353bbs.com" target="_blank" style="color: white; text-decoration: underline;">爱尔兰第一中文论坛</a>. All Rights Reserved.</p>


        </div>
    </div>
    
    <script>
        let chart = null;
        let updateInterval = null;

        // --- 3. 新增一个函数，用于获取并更新页脚的时间 ---
        function fetchLastUpdateTime() {
            fetch('/api/last_update')
                .then(response => response.json())
                .then(data => {
                    const timeElement = document.getElementById('lastUpdated');
                    if (data && data.last_update_time) {
                        timeElement.textContent = `数据最后更新: ${data.last_update_time}`;
                    } else {
                        timeElement.textContent = '数据最后更新: 未知';
                    }
                })
                .catch(error => {
                    console.error('获取最后更新时间失败:', error);
                    document.getElementById('lastUpdated').textContent = '数据最后更新: 获取失败';
                });
        }

        // 更新统计数据
        function updateStats(data) {
            document.getElementById('totalApps').textContent = data.summary.total_apps.toLocaleString();
            document.getElementById('totalRefused').textContent = data.summary.total_refused.toLocaleString();
            document.getElementById('avgRefusalRate').textContent = data.summary.avg_refusal_rate + '%';
            // 移除从这里更新时间，因为它现在由 fetchLastUpdateTime 负责
            // document.getElementById('lastUpdated').textContent = `数据最后更新: ${data.summary.last_updated}`;
            
            // 更新数据范围
            document.getElementById('dataRange').textContent = `${data.summary.start_date} 至 ${data.summary.end_date}`;
        }

        // 查询申请号
        async function searchApplication() {
            const appNumber = document.getElementById('searchInput').value.trim();
            const resultDiv = document.getElementById('searchResult');
            const searchBtn = document.getElementById('searchBtn');
            
            if (!appNumber) {
                showSearchResult(false, '请输入申请编号');
                return;
            }
            
            searchBtn.disabled = true;
            searchBtn.textContent = '查询中...';
            
            try {
                const response = await fetch(`/api/search?app_number=${appNumber}`);
                const data = await response.json();
                
                if (data.success) {
                    let resultHtml = '';
                    
                    data.results.forEach((result, index) => {
                        const decisionClass = result.decision.toLowerCase() === 'approved' ? 'approved' : 'refused';
                        const decisionText = result.decision === 'Approved' ? '✅ 申请获批' : '❌ 申请被拒';
                        
                        resultHtml += `
                            <div class="result-item">
                                <div class="result-decision ${decisionClass}">
                                    ${decisionText}
                                </div>
                                <div class="result-app-number">
                                    申请编号: ${result.application_number}
                                </div>
                            </div>
                        `;
                    });

                    // 添加声明
                    resultHtml += `
                        <div class="result-disclaimer">
                            📌 <strong>查询结果声明：</strong>此查询结果基于公开数据整理，仅供参考。实际签证决策请以官方通知为准，如有疑问请联系相关签证中心或领事馆确认。
                        </div>
                    `;
                    
                    resultDiv.innerHTML = resultHtml;
                    resultDiv.className = 'search-result success';
                } else {
                    showSearchResult(false, data.message);
                }
                
            } catch (error) {
                showSearchResult(false, '查询时发生网络错误，请稍后重试');
            }
            
            searchBtn.disabled = false;
            searchBtn.textContent = '查询';
            resultDiv.style.display = 'block';
        }

        function showSearchResult(success, message) {
            const resultDiv = document.getElementById('searchResult');
            resultDiv.innerHTML = `<p style="margin: 0; color: ${success ? '#2ecc71' : '#e74c3c'}; text-align: center; padding: 20px;">${message}</p>`;
            resultDiv.className = `search-result ${success ? 'success' : 'error'}`;
            resultDiv.style.display = 'block';
        }

        // 创建/更新图表
        function updateChart(data) {
            const ctx = document.getElementById('trendChart').getContext('2d');
            
            const chartData = {
                labels: data.labels,
                datasets: [
                    {
                        label: '总申请数',
                        type: 'bar',
                        data: data.total_applications,
                        backgroundColor: 'rgba(52, 152, 219, 0.8)',
                        borderColor: 'rgba(52, 152, 219, 1)',
                        borderWidth: 2,
                        borderRadius: 8,
                        yAxisID: 'y'
                    },
                    {
                        label: '拒签数',
                        type: 'bar',
                        data: data.refused_count,
                        backgroundColor: 'rgba(231, 76, 60, 0.8)',
                        borderColor: 'rgba(231, 76, 60, 1)',
                        borderWidth: 2,
                        borderRadius: 8,
                        yAxisID: 'y'
                    },
                    {
                        label: '拒签率',
                        type: 'line',
                        data: data.refusal_rate,
                        borderColor: 'rgba(243, 156, 18, 1)',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        borderWidth: 4,
                        pointRadius: 8,
                        pointHoverRadius: 12,
                        pointBackgroundColor: 'rgba(243, 156, 18, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            };

            const config = {
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                pointStyle: 'circle',
                                font: {
                                    size: 14,
                                    weight: '600'
                                },
                                padding: 25
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: 'rgba(255, 255, 255, 0.2)',
                            borderWidth: 1,
                            cornerRadius: 12,
                            displayColors: true,
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.dataset.label === '拒签率') {
                                        label += context.parsed.y + '%';
                                    } else {
                                        label += context.parsed.y + ' 人';
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: {
                                    size: 12,
                                    weight: '500'
                                },
                                color: '#666'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: '申请人数',
                                font: {
                                    size: 14,
                                    weight: '600'
                                },
                                color: '#2c3e50'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                }
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: '拒签率 (%)',
                                font: {
                                    size: 14,
                                    weight: '600'
                                },
                                color: '#2c3e50'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                },
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            };

            if (chart) {
                chart.destroy();
            }
            
            chart = new Chart(ctx, config);
            
            // 隐藏加载动画，显示图表
            document.getElementById('loadingChart').style.display = 'none';
            document.getElementById('trendChart').style.display = 'block';
        }

        // 获取数据
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                updateStats(data);
                updateChart(data);
                
            } catch (error) {
                console.error('获取数据失败:', error);
            }
        }

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            fetchData();
            fetchLastUpdateTime(); // <-- 4. 页面加载时调用新函数
            
            // 5. 将刷新间隔从30秒改为1小时 (3600000毫秒)
            updateInterval = setInterval(fetchData, 3600000);
            
            // 页面可见性变化时的处理
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    clearInterval(updateInterval);
                } else {
                    fetchData();
                    updateInterval = setInterval(fetchData, 3600000); // <-- 同样修改这里的间隔
                }
            });

            // 查询功能事件绑定
            document.getElementById('searchBtn').addEventListener('click', searchApplication);
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchApplication();
                }
            });
        });

        // 页面加载动画
        window.addEventListener('load', function() {
            document.querySelectorAll('.stat-card').forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.8s cubic-bezier(0.23, 1, 0.320, 1)';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 150);
            });
        });
    </script>
</body>
</html>'''
    
    # 创建templates目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    # 保存模板文件
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(template_content)

def main():
    """主函数，仅用于直接运行时提供友好提示和启动开发服务器"""
    print("🚀 正在启动签证数据看板服务...")
    
    # 测试数据库连接
    try:
        data = get_visa_data()
        print(f"✅ 数据库连接成功，当前有 {data['summary']['total_apps']} 条申请记录")
        print(f"📅 数据范围: {data['summary']['start_date']} 至 {data['summary']['end_date']}")
    except Exception as e:
        print(f"❌ 数据库连接或数据处理失败: {e}")
        # 在开发模式下，即使失败也尝试启动服务以便调试
    
    print("\n🌐 启动Web服务器 (开发模式)...")
    print(f"📊 访问地址: http://localhost:5005")
    print("🔄 数据刷新已调整为1小时")
    print("⏹️  按 Ctrl+C 停止服务")
    
    # 启动Flask应用。这部分代码在Gunicorn下不会被执行。
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    # 仅在直接运行此脚本时创建模板文件
    print("📝 正在生成/更新HTML模板文件...")
    create_template()
    main()