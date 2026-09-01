#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://proxy-socks5.com/',
            'Cookie': cookie_string
        })
    
    def scrape_proxy_list(self):
        """抓取代理列表"""
        try:
            print(f"正在抓取代理列表: {self.url}")
            response = self.session.get(self.url, timeout=30)
            response.encoding = 'utf-8'
            
            # 1. 页面级拦截：检测是否有英文的 Token 过期或无效提示
            page_text_lower = response.text.lower()
            if "expired" in page_text_lower or "invalid" in page_text_lower or "unauthorized" in page_text_lower:
                print("Token expired. (Detected expiration keywords in page)")
                return []
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                print("未找到代理数据表格，页面结构可能改变，或 Cookie 权限不足。")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    protocol_match = re.search(r'(socks5|https|http)', cells[0].text, re.IGNORECASE)
                    protocol = protocol_match.group(1).lower() if protocol_match else ""
                    
                    # 兼容提取包含 X 或 x 的脱敏 IP
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.(?:\d{1,3}|[Xx]+)\.\d{1,3})', cells[1].text)
                    ip = ip_match.group(1) if ip_match else ""
                    
                    port_match = re.search(r'(\d{2,5})', cells[2].text)
                    port = port_match.group(1) if port_match else ""
                    
                    raw_location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    if protocol and ip and port:
                        raw_location = raw_location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                        raw_location = ' '.join(raw_location.split())
                        
                        time_match = re.search(r'入库.*?(\d{2}-\d{2}\s+\d{2}:\d{2})', raw_location)
                        if time_match:
                            in_time = time_match.group(1)
                            location = re.sub(r'入库.*', '', raw_location).strip()
                        else:
                            in_time = "未知"
                            location = raw_location
                            
                        url_str = f"{protocol}://{ip}:{port}"
                        proxy_line = f"{url_str.ljust(36)}入库时间：{in_time}  {location}"
                        
                        proxies.append(proxy_line)
            
            # 2. 数据级拦截：智能判定是否 100% 都是带 X 的脱敏 IP
            if proxies:
                x_count = sum(1 for p in proxies if 'X' in p or 'x' in p)
                
                # 如果所有提取到的节点全都带有 X，说明账号已被降级为访客权限
                if x_count == len(proxies):
                    print("Token expired. (All proxy IPs are masked with 'X').")
                    return []
            
            print(f"成功抓取到 {len(proxies)} 个代理（其中包含 {x_count if proxies else 0} 个带 X 节点）")
            return proxies
            
        except requests.RequestException as e:
            print(f"网络请求错误: {e}")
            return []
        except Exception as e:
            print(f"抓取错误: {e}")
            return []
    
    def save_to_file(self, proxies, filename='proxy.txt'):
        """保存代理列表到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 获取 UTC 时间并强制加上 8 小时，转换为北京时间
                beijing_time = datetime.utcnow() + timedelta(hours=8)
                f.write(f"# 代理列表更新时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n")                
                f.write(f"# 总计: {len(proxies)} 个代理\n")
                
                # 如果列表为空，在文件中直观标注 Token 状态，方便查阅
                if not proxies:
                    f.write("# Token expired or no valid proxies found.\n")
                    f.write("# Please update PROXY_SITE_COOKIE in GitHub Secrets.\n")
                
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            print(f"代理列表已保存到 {filename}")
            return True
            
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    my_cookie = os.environ.get("PROXY_SITE_COOKIE")
    
    if not my_cookie:
        print("Error: Cookie not found! Please check PROXY_SITE_COOKIE in GitHub Secrets.")
        sys.exit(1)
        
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    # 无论抓取结果如何，都强制生成文件，保障 GitHub Actions 顺利通过 [ -f proxy.txt ] 检测
    scraper.save_to_file(proxies)

if __name__ == "__main__":
    main()
