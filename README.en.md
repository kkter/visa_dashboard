# Irish Visa Decision Query & Statistics System

An automated Irish visa decision query and data visualization project providing convenient visa status lookup services for 353bbs.com forum members.

## 📋 Project Overview

This project provides:
- 🔍 **Visa Decision Query**: Search visa decision results by application number
- 📊 **Data Visualization**: Display weekly visa application trends, refusal numbers and refusal rates
- 🤖 **Automated Updates**: Automatically fetch latest visa decision data from official sources
- 📱 **Responsive Design**: Supports both desktop and mobile device access

## 🏗️ Project Architecture

```
visa_dashboard/
├── data/                    # Data storage directory
│   ├── visas.db            # SQLite database
│   └── visa_pdfs/          # PDF files storage
├── logs/                   # Log files directory
├── templates/              # HTML templates
│   └── index.html         # Main page template
├── download_visas.py       # Data download script
├── parse_pdfs.py          # PDF parsing script
├── visa_dashboard.py      # Flask web application
├── run_pipeline.sh        # Automation task script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image configuration
├── docker-compose.yml    # Docker Compose configuration
└── README.md            # Project documentation
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
```bash
git clone git@github.com:kkter/visa_dashboard.git
cd visa_dashboard
```

2. **Start the service**
```bash
docker-compose up -d
```

3. **Access the application**
Open your browser and visit: `http://localhost:5005`

### Option 2: Local Development

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Initialize data**
```bash
# Download PDF files
python download_visas.py

# Parse PDFs and store in database
python parse_pdfs.py
```

3. **Start web service**
```bash
python visa_dashboard.py
```

## 📁 Core Components

### 1. Data Acquisition Module (`download_visas.py`)
- Downloads latest PDF files from Irish official visa decision pages
- Automatically detects new files to avoid duplicate downloads
- Supports network exception retry mechanism

### 2. Data Parsing Module (`parse_pdfs.py`)
- Uses pdfplumber to parse PDF file content
- Extracts application numbers, decision results, date ranges and other information
- Stores data in SQLite database with duplicate prevention

### 3. Web Application Module (`visa_dashboard.py`)
- Flask framework-based web service
- Provides query API and data statistics API
- Real-time chart display and application number search functionality

### 4. Automation Task (`run_pipeline.sh`)
- Automatically executes data update tasks Monday through Friday
- Intelligently skips completed weekly tasks to avoid duplication
- Complete success/failure status management

## 🔧 Configuration

### Environment Variables
- `PDF_DIR`: PDF file storage directory (default: `data/visa_pdfs`)
- `DB_NAME`: Database file path (default: `data/visas.db`)

### Scheduled Task Setup
Set up crontab on the host machine:
```bash
# Monday-Friday, execute check every hour from 2-8 AM
0 2-8 * * 1-5 docker exec visa_dashboard_app /app/run_pipeline.sh >> /path/to/logs/cron.log 2>&1
```

## 📊 API Endpoints

### Get Statistics Data
```
GET /api/data
```
Returns statistical data and chart data for visa applications.

### Query Application Results
```
GET /api/search?app_number=application_number
```
Query visa decision results by application number.

### Get Last Update Time
```
GET /api/last_update
```
Get the last database update timestamp.

## 🛠️ Technology Stack

- **Backend**: Python 3.9, Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **PDF Processing**: pdfplumber
- **Data Analysis**: pandas
- **Containerization**: Docker, Docker Compose
- **Task Scheduling**: cron, bash

## 📈 Features

- ✅ **Real-time Data Sync**: Automatically fetch latest visa decision data weekly
- ✅ **Smart Query**: Support fuzzy matching and exact search by application number
- ✅ **Data Visualization**: Interactive charts showing application trends and refusal rates
- ✅ **Responsive Design**: Perfect adaptation for mobile, tablet, and desktop devices
- ✅ **SEO Optimized**: Search engine friendly with social media sharing support
- ✅ **Containerized Deployment**: One-click deployment, easy maintenance and scaling

## 🔒 Data Disclaimer

The data in this project comes from publicly available Irish official visa decision documents and is for reference only. Please refer to official notifications for actual visa decisions.

## 📝 Development Roadmap

- [ ] Add data export functionality
- [ ] Support multi-language interface
- [ ] Enhance data analysis reports
- [ ] Add email notification features
- [ ] Performance monitoring and alerting

## 🤝 Contributing

We welcome Issues and Pull Requests to improve the project. Please ensure:
1. Code style follows PEP 8 standards
2. Add appropriate comments and documentation
3. Test compatibility of new features

## 📧 Contact

- Project Maintainer: 353bbs.com - Ireland's First Chinese Forum
- Issue Reports: Submit via GitHub Issues

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🔍 How It Works

### Data Collection Process
1. **Automated Download**: The system monitors the official Irish visa decision page for new PDF publications
2. **Intelligent Processing**: Only processes new files to maintain efficiency
3. **Data Extraction**: Parses PDF content to extract structured visa decision data
4. **Database Storage**: Stores processed data in SQLite with proper indexing for fast queries

### Query System
- **Fast Search**: Optimized database queries for instant application number lookup
- **Flexible Matching**: Supports both exact and partial application number searches
- **Real-time Results**: Immediate response with decision status and relevant dates

### Visualization Dashboard
- **Interactive Charts**: Built with Chart.js for responsive data visualization
- **Trend Analysis**: Weekly statistics showing application volumes and approval rates
- **Mobile Optimized**: Touch-friendly interface for mobile devices

## 🚨 Important Notes

1. **Data Accuracy**: While we strive for accuracy, this tool is for reference only
2. **Update Frequency**: Data is typically updated weekly following official publications
3. **System Requirements**: Requires Docker for easiest deployment
4. **Network Dependencies**: Requires internet access for data updates

## 🎯 Use Cases

- **Applicants**: Check your visa decision status quickly
- **Immigration Consultants**: Monitor processing trends and statistics
- **Community Members**: Stay informed about visa processing patterns
- **Researchers**: Analyze Irish visa approval trends over time

---

**Disclaimer**: This tool is for educational and reference purposes only. Query results may have delays or omissions. Please rely on official channels for final decision information.