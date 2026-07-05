#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class ProxyListScraper:
    def __init__(self):
        self.url = "https://proxy-socks5.com/proxy_list"
    
    def scrape_proxy_list(self):
        """使用无头浏览器抓取动态渲染后的代理列表"""
        print(f"启动无头浏览器抓取: {self.url}")
        
        try:
            with sync_playwright() as p:
                # 启动隐形 Chromium 浏览器
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # 伪装真实用户的请求头
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                # 访问网页并等待网络空闲，确保基础 JS 文件已下载完毕
                print("正在加载网页并等待 JavaScript 解密...")
                page.goto(self.url, wait_until="networkidle", timeout=30000)
                
                # 额外强制等待 3 秒，留出足够的时间让网页完成从 X 到真实 IP 的动态渲染
                page.wait_for_timeout(3000)
                
                # 获取经过浏览器完整渲染后的 DOM 源码（此时机房的 X 已被替换为真 IP）
                html_content = page.content()
                browser.close()
                
            # 交给 BeautifulSoup 进行结构化提取
            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')
            
            if not table:
                print("未找到代理数据表格，可能触发了网站的真人验证防爬策略")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    protocol = cells[0].text.strip()
                    port = cells[2].text.strip()
                    location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    ip_cell = cells[1]
                    
                    # 即使有了浏览器加持，依然保留双保险：剔除残留的不可见干扰标签
                    for hidden_tag in ip_cell.find_all(['span', 'div', 'i', 'b', 'font']):
                        style = hidden_tag.get('style', '').lower()
                        class_list = ''.join(hidden_tag.get('class', [])).lower()
                        if 'none' in style or 'hidden' in style or 'hide' in class_list:
                            hidden_tag.decompose()
                            
                    ip = ip_cell.get_text(strip=True).replace(' ', '')
                    
                    # 深度清洗位置信息
                    location = location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                    location = ' '.join(location.split())
                    
                    if protocol and ip and port:
                        proxy = f"{protocol}://{ip}:{port} [{location}]"
                        proxies.append(proxy)
            
            print(f"成功抓取到 {len(proxies)} 个代理")
            return proxies
            
        except Exception as e:
            print(f"浏览器渲染抓取出现严重错误: {e}")
            return []

    def save_to_file(self, proxies, filename='proxy.txt'):
        """保存代理列表到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 代理列表更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n\n")
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            print(f"代理列表已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    scraper = ProxyListScraper()
    proxies = scraper.scrape_proxy_list()
    
    # 强制校验：如果没抓到数据，退出码置为 1，中断 Action 避免提交空文件
    if proxies:
        scraper.save_to_file(proxies)
        print("代理列表抓取完成！")
    else:
        print("错误：未能获取到代理数据")
        sys.exit(1)

if __name__ == "__main__":
    main()
