#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        
        # 1. 初始化 Session 对象，跨请求保持连接状态
        self.session = requests.Session()
        
        # 2. 设置通用请求头，并将你的登录 Cookie 加入其中
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36',
            'Cookie': cookie_string
        })
    
    def scrape_proxy_list(self):
        """抓取代理列表"""
        try:
            print(f"正在以登录状态抓取代理列表: {self.url}")
            
            # 3. 使用 session 发送请求，此时会自动携带 Cookie
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
                    protocol = cells[0].text.strip()
                    ip = cells[1].text.strip()
                    port = cells[2].text.strip()
                    location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    location = location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                    location = ' '.join(location.split())
                    
                    if protocol and ip and port:
                        # 如果是家宽（即便是登录状态也带X），你可以选择跳过或保留
                        # if 'X' in ip:
                        #     continue
                        
                        proxy = f"{protocol}://{ip}:{port} [{location}]"
                        proxies.append(proxy)
            
            print(f"成功抓取到 {len(proxies)} 个代理")
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
                f.write(f"# 总计: {len(proxies)} 个代理\n\n")
                
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            print(f"代理列表已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    # 替换为你刚才在浏览器开发者工具中抓取到的真实 Cookie 字符串
    my_cookie = "session=eyJwb3J0IjozMTI0OSwidXNlcm5hbWUiOiJtb29vb29zcyIsInV1aWQiOiI5MjA3YjgzMi1lNmFjLTQ1N2QtODkwZS1kN2FhMzQ0ZjU3ZDEifQ.alSdAQ.Oz1lKlfQgc2closhId5yGFquuVA"
    
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    if proxies:
        scraper.save_to_file(proxies)
    else:
        print("未能获取到代理数据")

if __name__ == "__main__":
    main()
