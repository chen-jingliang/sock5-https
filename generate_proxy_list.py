#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        self.session = requests.Session()
        # 补齐现代浏览器常用标头，避免触发防爬降级
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://proxy-socks5.com/',
            'Cookie': cookie_string
        })
    
    def scrape_proxy_list(self):
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
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    protocol_match = re.search(r'(socks5|https|http)', cells[0].text, re.IGNORECASE)
                    protocol = protocol_match.group(1).lower() if protocol_match else ""
                    
                    # 匹配完整纯数字 IP（如果包含 X 则直接忽略，确保输出有效节点）
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', cells[1].text)
                    ip = ip_match.group(1) if ip_match else ""
                    
                    # 如果带 X 则跳过，防止写入无效格式
                    if not ip or 'X' in cells[1].text:
                        continue
                    
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
            
            print(f"成功抓取到 {len(proxies)} 个未加密代理")
            return proxies
            
        except Exception as e:
            print(f"抓取错误: {e}")
            return []

    def save_to_file(self, proxies, filename='proxy.txt'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 代理列表更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n")
                f.write("# 实时抓取于免费公共代理池: https://proxy-socks5.com\n\n")
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            return True
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    my_cookie = os.environ.get("PROXY_SITE_COOKIE")
    if not my_cookie:
        print("错误: 未找到 Cookie！")
        return
        
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    if proxies:
        scraper.save_to_file(proxies)
    else:
        print("未能获取到有效未加密代理，建议更新 PROXY_SITE_COOKIE")

if __name__ == "__main__":
    main()
