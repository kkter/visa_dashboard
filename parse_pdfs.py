import os
import sqlite3
import pdfplumber
import re
from datetime import datetime

# 定义常量
PDF_DIR = "data/visa_pdfs"
DB_NAME = "data/visas.db"
TABLE_NAME = "visa_decisions"

def setup_database():
    """初始化数据库和表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 删除旧表，重新创建
    cursor.execute(f'DROP TABLE IF EXISTS {TABLE_NAME}')
    
    # 创建简单的表结构
    cursor.execute(f'''
    CREATE TABLE {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_number INTEGER NOT NULL,
        decision TEXT NOT NULL,
        source_file TEXT NOT NULL,
        date_range_start DATE,
        date_range_end DATE,
        processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引防止重复
    cursor.execute(f'''
    CREATE UNIQUE INDEX idx_app_source ON {TABLE_NAME} (application_number, source_file)
    ''')
    
    conn.commit()
    return conn

def parse_date_range_from_filename(filename):
    """从文件名中解析日期范围"""
    try:
        name_without_ext = filename.replace('.pdf', '')
        
        patterns = [
            r'(\d{1,2})_([A-Za-z]+)_to_(\d{1,2})_([A-Za-z]+)_(\d{4})',
            r'(\d{1,2})_to_(\d{1,2})_([A-Za-z]+)_(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name_without_ext)
            if match:
                groups = match.groups()
                
                try:
                    if len(groups) == 5:
                        start_day, start_month, end_day, end_month, year = groups
                        start_date_str = f"{start_day} {start_month} {year}"
                        end_date_str = f"{end_day} {end_month} {year}"
                    elif len(groups) == 4:
                        start_day, end_day, month, year = groups
                        start_date_str = f"{start_day} {month} {year}"
                        end_date_str = f"{end_day} {month} {year}"
                    
                    start_date = datetime.strptime(start_date_str, "%d %B %Y").date()
                    end_date = datetime.strptime(end_date_str, "%d %B %Y").date()
                    
                    return start_date, end_date
                        
                except ValueError:
                    continue
        
        return None, None
        
    except Exception:
        return None, None

def sort_files_by_date(pdf_files):
    """按文件中的日期范围排序PDF文件"""
    files_with_dates = []
    
    for filename in pdf_files:
        start_date, end_date = parse_date_range_from_filename(filename)
        if start_date and end_date:
            files_with_dates.append((filename, start_date))
        else:
            files_with_dates.append((filename, datetime.max.date()))
    
    # 按开始日期排序
    files_with_dates.sort(key=lambda x: x[1])
    return [item[0] for item in files_with_dates]

def parse_and_store_pdfs(conn):
    """解析所有PDF文件并将数据存入数据库"""
    cursor = conn.cursor()
    
    if not os.path.exists(PDF_DIR):
        print(f"错误: 目录 '{PDF_DIR}' 不存在。")
        return

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("未找到PDF文件。")
        return
    
    # 按日期排序文件
    sorted_files = sort_files_by_date(pdf_files)
    print(f"找到 {len(sorted_files)} 个 PDF 文件待处理。")

    total_new_records = 0
    
    for filename in sorted_files:
        file_path = os.path.join(PDF_DIR, filename)
        print(f"\n--- 正在处理文件: {filename} ---")
        
        # 解析文件名中的日期范围
        start_date, end_date = parse_date_range_from_filename(filename)
        if start_date and end_date:
            print(f"  日期范围: {start_date} 到 {end_date}")
        
        file_records = 0
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"  处理第 {page_num} 页...")
                    tables = page.extract_tables()
                    
                    for table in tables:
                        for row in filter(None, table):
                            # 跳过表头
                            if any(header in str(row) for header in ['Application Number', 'Decision']):
                                continue
                            
                            # 验证行数据
                            if len(row) >= 2 and row[0] and str(row[0]).strip().isdigit():
                                app_number = int(str(row[0]).strip())
                                decision = str(row[1]).strip() if row[1] else "N/A"
                                
                                try:
                                    cursor.execute(
                                        f"""INSERT OR IGNORE INTO {TABLE_NAME} 
                                        (application_number, decision, source_file, date_range_start, date_range_end) 
                                        VALUES (?, ?, ?, ?, ?)""",
                                        (app_number, decision, filename, start_date, end_date)
                                    )
                                    
                                    if cursor.rowcount > 0:
                                        file_records += 1
                                        total_new_records += 1
                                        print(f"    新记录: {app_number} - {decision}")
                                    
                                except sqlite3.Error as db_error:
                                    print(f"    数据库错误: {db_error}")
                
            conn.commit()
            print(f"  文件处理完成，新增 {file_records} 条记录")
            
        except Exception as e:
            print(f"处理文件 {filename} 时发生错误: {e}")

    print(f"\n处理完成! 总共添加了 {total_new_records} 条新记录到数据库")

def print_database_summary(conn):
    """打印数据库摘要信息"""
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        total_records = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT decision, COUNT(*) FROM {TABLE_NAME} GROUP BY decision")
        decision_stats = cursor.fetchall()
        
        print(f"\n=== 数据库摘要 ===")
        print(f"总记录数: {total_records}")
        print(f"决定统计:")
        for decision, count in decision_stats:
            print(f"  {decision}: {count}")
        
    except Exception as e:
        print(f"获取数据库摘要时发生错误: {e}")

if __name__ == "__main__":
    print("开始处理PDF文件...")
    db_connection = setup_database()
    parse_and_store_pdfs(db_connection)
    print_database_summary(db_connection)
    db_connection.close()
    print("数据库连接已关闭。")