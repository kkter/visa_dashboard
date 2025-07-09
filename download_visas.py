# filepath: /Users/kkter/KKTer/Learn_File/Programing/Project/VisaResults/download_visas.py
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 目标网页 URL
URL = "https://www.ireland.ie/en/china/beijing/services/visas/visa-decisions/"

# PDF 文件将要保存的目录
DOWNLOAD_DIR = "data/visa_pdfs"

def download_visa_pdfs():
    """
    从爱尔兰签证决策页面下载新的 PDF 文件。
    """
    print(f"正在访问: {URL}")
    
    try:
        # 创建用于保存 PDF 的目录
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
            print(f"已创建目录: {DOWNLOAD_DIR}")

        # 设置浏览器头信息
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }

        # 发送 HTTP 请求获取网页内容
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()  # 如果请求失败则抛出异常

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找包含链接的 div
        summary_div = soup.find('div', class_='rich_text__summary')
        
        if not summary_div:
            print("错误: 未在页面上找到 'rich_text__summary' 部分。")
            return

        # 查找所有 PDF 链接
        pdf_links = summary_div.find_all('a', href=lambda href: href and href.endswith('.pdf'))
        
        if not pdf_links:
            print("未找到任何 PDF 链接。")
            return

        print(f"找到 {len(pdf_links)} 个 PDF 链接。")
        new_files_downloaded = 0

        # 遍历所有链接并下载文件
        for link in pdf_links:
            # 构造完整的 PDF URL
            pdf_relative_url = link.get('href')
            pdf_url = urljoin(URL, pdf_relative_url)
            
            # 从 URL 中获取文件名
            pdf_filename = os.path.basename(pdf_relative_url)
            file_path = os.path.join(DOWNLOAD_DIR, pdf_filename)

            # 如果文件不存在，则下载它
            if not os.path.exists(file_path):
                print(f"正在下载新文件: {pdf_filename}...")
                pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
                pdf_response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"已保存到 {file_path}")
                new_files_downloaded += 1
            else:
                print(f"文件已存在，跳过: {pdf_filename}")

        if new_files_downloaded == 0:
            print("\n没有需要下载的新文件。")
        else:
            print(f"\n下载完成。共下载了 {new_files_downloaded} 个新文件。")

    except requests.exceptions.RequestException as e:
        print(f"访问网页时出错: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    download_visa_pdfs()