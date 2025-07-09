# 爱尔兰签证结果查询与统计系统

这是一个自动化的爱尔兰签证结果查询与数据统计可视化项目，为 353bbs.com 论坛网友提供便捷的签证状态查询服务。

## 📋 项目概述

本项目能够：
- 🔍 **签证结果查询**：输入申请编号即可查询签证决策结果
- 📊 **数据可视化**：展示每周签证申请数量、拒签数量和拒签率趋势
- 🤖 **自动化更新**：定时从官方网站获取最新的签证决策数据
- 📱 **响应式设计**：支持桌面和移动设备访问

## 🏗️ 项目架构

```
visa_dashboard/
├── data/                    # 数据存储目录
│   ├── visas.db            # SQLite 数据库
│   └── visa_pdfs/          # PDF 文件存储
├── logs/                   # 日志文件目录
├── templates/              # HTML 模板
│   └── index.html         # 主页面模板
├── download_visas.py       # 数据下载脚本
├── parse_pdfs.py          # PDF 解析脚本
├── visa_dashboard.py      # Flask Web 应用
├── run_pipeline.sh        # 自动化任务脚本
├── requirements.txt       # Python 依赖
├── Dockerfile            # Docker 镜像配置
├── docker-compose.yml    # Docker Compose 配置
└── README.md            # 项目说明
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd visa_dashboard
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问应用**
打开浏览器访问：`http://localhost:5005`

### 方式二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **初始化数据**
```bash
# 下载 PDF 文件
python download_visas.py

# 解析 PDF 并存入数据库
python parse_pdfs.py
```

3. **启动 Web 服务**
```bash
python visa_dashboard.py
```

## 📁 核心组件说明

### 1. 数据获取模块 (`download_visas.py`)
- 从爱尔兰官方签证决策页面下载最新的 PDF 文件
- 自动检测新文件，避免重复下载
- 支持网络异常重试机制

### 2. 数据解析模块 (`parse_pdfs.py`)
- 使用 pdfplumber 解析 PDF 文件内容
- 提取申请编号、决策结果、日期范围等信息
- 存储到 SQLite 数据库中，防止重复处理

### 3. Web 应用模块 (`visa_dashboard.py`)
- Flask 框架构建的 Web 服务
- 提供查询 API 和数据统计 API
- 实时图表展示和申请编号查询功能

### 4. 自动化任务 (`run_pipeline.sh`)
- 周一至周五自动执行数据更新任务
- 智能跳过已完成的周任务，避免重复执行
- 完整的成功/失败状态管理

## 🔧 配置说明

### 环境变量
- `PDF_DIR`: PDF 文件存储目录（默认：`data/visa_pdfs`）
- `DB_NAME`: 数据库文件路径（默认：`data/visas.db`）

### 定时任务设置
在宿主机上设置 crontab：
```bash
# 周一至周五，凌晨2-8点每小时执行一次检查
0 2-8 * * 1-5 docker exec visa_dashboard_app /app/run_pipeline.sh >> /path/to/logs/cron.log 2>&1
```

## 📊 API 接口

### 获取统计数据
```
GET /api/data
```
返回签证申请的统计数据和图表数据。

### 查询申请结果
```
GET /api/search?app_number=申请编号
```
根据申请编号查询签证决策结果。

### 获取更新时间
```
GET /api/last_update
```
获取数据库最后更新时间。

## 🛠️ 技术栈

- **后端**: Python 3.9, Flask
- **数据库**: SQLite
- **前端**: HTML5, CSS3, JavaScript, Chart.js
- **PDF处理**: pdfplumber
- **数据分析**: pandas
- **容器化**: Docker, Docker Compose
- **任务调度**: cron, bash

## 📈 功能特性

- ✅ **实时数据同步**：每周自动获取最新签证决策数据
- ✅ **智能查询**：支持申请编号模糊匹配和精确查询
- ✅ **数据可视化**：交互式图表展示申请趋势和拒签率
- ✅ **响应式设计**：完美适配手机、平板、桌面设备
- ✅ **SEO 优化**：搜索引擎友好，支持社交媒体分享
- ✅ **容器化部署**：一键部署，易于维护和扩展

## 🔒 数据声明

本项目数据来源于爱尔兰官方公开的签证决策文件，仅供参考。实际签证决策请以官方通知为准。

## 📝 开发计划

- [ ] 添加数据导出功能
- [ ] 支持多语言界面
- [ ] 增加数据分析报告
- [ ] 添加邮件通知功能
- [ ] 性能监控和告警

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。请确保：
1. 代码风格符合 PEP 8 规范
2. 添加适当的注释和文档
3. 测试新功能的兼容性

## 📧 联系方式

- 项目维护：353bbs.com 爱尔兰第一中文论坛
- 问题反馈：通过 GitHub Issues 提交

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

**免责声明**：本工具仅供学习和参考使用，查询结果可能存在延迟或遗漏，请以官方渠道获取的信息为最终依据。