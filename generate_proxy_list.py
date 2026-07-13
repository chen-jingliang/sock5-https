#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re  # 新增：用于正则提取时间

class ProxyListScraper:
    def __init__(self, cookie_string=""):
        self.url = "https://proxy-socks5.com/proxy_list"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36',
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
                print("未找到代理数据表格")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # 提取纯文本，避免变量重复拼接
                    protocol = cells[0].text.strip().lower()
                    ip = cells[1].text.strip()
                    port = cells[2].text.strip()
                    raw_location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    if protocol and ip and port:
                        # 基础清理多余文本和空白
                        raw_location = raw_location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                        raw_location = ' '.join(raw_location.split())
                        
                        # 1. 使用正则将“入库时间”从 location 中剥离出来
                        time_match = re.search(r'入库(?:时间)?[:：]?\s*(\d{2}-\d{2}\s+\d{2}:\d{2})', raw_location)
                        if time_match:
                            in_time = time_match.group(1)
                            # 截取时间匹配之前的部分作为纯地理位置
                            location = raw_location[:time_match.start()].strip()
                        else:
                            in_time = "未知"
                            location = raw_location
                            
                        # 2. 格式化拼接与排版对齐
                        url_str = f"{protocol}://{ip}:{port}"
                        
                        # ljust(32) 表示将左侧 URL 填充至 32 个字符宽度，不足的用空格补齐，从而实现上下对齐
                        # 后面使用 \t 制表符进一步排版机房位置信息
                        proxy_line = f"{url_str.ljust(32)}入库时间：{in_time}\t{location}"
                        
                        proxies.append(proxy_line)
            
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
                # 按原作者格式写入文件头部
                f.write(f"# 代理列表更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n")
                f.write("# 实时抓取于免费公共代理池: https://proxy-socks5.com\n")
                f.write("# 最好用的代理资源\n\n")
                
                # 写入代理正文
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            print(f"代理列表已保存到 {filename}")
            return True
            
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    # 如果你需要登录后的数据，依然将你的 Cookie 填在下方
    my_cookie = "session=eyJwb3J0IjozMTI0OSwidXNlcm5hbWUiOiJtb29vb29zcyIsInV1aWQiOiI5MjA3YjgzMi1lNmFjLTQ1N2QtODkwZS1kN2FhMzQ0ZjU3ZDEifQ.alSdAQ.Oz1lKlfQgc2closhId5yGFquuVA"
    
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    if proxies:
        scraper.save_to_file(proxies)
    else:
        print("未能获取到代理数据")

if __name__ == "__main__":
    main()
