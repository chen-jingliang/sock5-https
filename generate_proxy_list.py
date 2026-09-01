#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        self.session = requests.Session()
        # 伪装现代浏览器标头，防止被反爬策略直接拒绝
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
                    
                    # 2. 提取 IP（仅提取无脱敏 X 的纯数字有效 IPv4）
                    ip_text = cells[1].text.strip()
                    if 'X' in ip_text or 'x' in ip_text:
                        continue  # 忽略脱敏加密的 IP
                        
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_text)
                    ip = ip_match.group(1) if ip_match else ""
                    
                    # 3. 提取端口
                    port_match = re.search(r'(\d{2,5})', cells[2].text)
                    port = port_match.group(1) if port_match else ""
                    
                    raw_location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    if protocol and ip and port:
                        raw_location = raw_location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                        raw_location = ' '.join(raw_location.split())
                        
                        # 4. 精准提取时间和地理位置
                        time_match = re.search(r'入库.*?(\d{2}-\d{2}\s+\d{2}:\d{2})', raw_location)
                        if time_match:
                            in_time = time_match.group(1)
                            location = re.sub(r'入库.*', '', raw_location).strip()
                        else:
                            in_time = "未知"
                            location = raw_location
                            
                        # 5. 格式化组装
                        url_str = f"{protocol}://{ip}:{port}"
                        proxy_line = f"{url_str.ljust(36)}入库时间：{in_time}  {location}"
                        proxies.append(proxy_line)
            
            print(f"成功抓取到 {len(proxies)} 个完整有效代理")
            return proxies
            
        except requests.RequestException as e:
            print(f"网络请求错误: {e}")
            return []
        except Exception as e:
            print(f"解析错误: {e}")
            return []
    
    def save_to_file(self, proxies, filename='proxy.txt'):
        """保存代理列表到文件（即使为空也生成头部，避免 Workflow 报文件不存在而中断）"""
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
        print("错误: 未找到 Cookie！请检查 GitHub Secrets 中的 PROXY_SITE_COOKIE 设置。")
        sys.exit(1)
        
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    # 无论是否抓到代理，都会生成 proxy.txt 文件，确保 GitHub Action 中的 `if [ -f proxy.txt ]` 检查正常通过
    scraper.save_to_file(proxies)

if __name__ == "__main__":
    main()
