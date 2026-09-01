#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        self.session = requests.Session()
        # 优化 1：更新为现代浏览器请求头，降低被拦截概率
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
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                print("未找到代理数据表格，请检查 Cookie 是否过期或页面结构是否改变")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # 1. 提取协议
                    protocol_match = re.search(r'(socks5|https|http)', cells[0].text, re.IGNORECASE)
                    protocol = protocol_match.group(1).lower() if protocol_match else ""
                    
                    # 优化 2：严格过滤带 X 的脱敏 IP
                    ip_text = cells[1].text.strip()
                    if 'X' in ip_text or 'x' in ip_text:
                        continue
                    
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_text)
                    ip = ip_match.group(1) if ip_match else ""
                    
                    # 3. 提取端口
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
            
            print(f"成功抓取到 {len(proxies)} 个未脱敏代理")
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
                f.write(f"# 代理列表更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n")
                f.write("# 实时抓取于免费公共代理池: https://proxy-socks5.com\n")
                f.write("# 最好用的代理资源\n\n")
                
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
        print("错误: 未找到 Cookie！请检查是否在 GitHub Secrets 或环境变量中设置了 PROXY_SITE_COOKIE。")
        # 优化 3：抛出系统错误码，让 Action 捕获失败状态
        sys.exit(1)
        
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    # 优化 4：移除 if proxies 判断。即使为空，也强制生成 proxy.txt
    # 防止 GitHub Actions 后续步骤因找不到文件而报 exit 1 导致整个流程卡死
    scraper.save_to_file(proxies)
    
    if not proxies:
        print("警告: 抓取结果为空，可能 Token 已失效或全是脱敏 IP。已生成带头部的空文件以维持 Action 运行。")

if __name__ == "__main__":
    main()
