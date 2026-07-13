#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

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
                    # 1. 提取协议：只匹配 socks5, http 或 https，丢弃多余字符
                    protocol_match = re.search(r'(socks5|https|http)', cells[0].text, re.IGNORECASE)
                    protocol = protocol_match.group(1).lower() if protocol_match else ""
                    
                    # 2. 提取 IP：支持标准 IP 格式及带 X 的脱敏格式（如 23.254.X.240）
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.(?:\d{1,3}|X)\.\d{1,3})', cells[1].text)
                    ip = ip_match.group(1) if ip_match else ""
                    
                    # 3. 提取端口：只提取连续的数字
                    port_match = re.search(r'(\d{2,5})', cells[2].text)
                    port = port_match.group(1) if port_match else ""
                    
                    raw_location = cells[3].text.strip() if len(cells) > 3 else "未知"
                    
                    if protocol and ip and port:
                        # 基础清理多余文本和空白
                        raw_location = raw_location.replace('复制', '').replace('已复制', '').replace('已', '').strip()
                        raw_location = ' '.join(raw_location.split())
                        
                        # 4. 精准分离“入库时间”和“地理位置”
                        # 从原始字符串中提取类似 07-13 15:41 的时间
                        time_match = re.search(r'入库.*?(\d{2}-\d{2}\s+\d{2}:\d{2})', raw_location)
                        if time_match:
                            in_time = time_match.group(1)
                            # 将入库时间及其后面的所有字符从地理位置文本中抹除
                            location = re.sub(r'入库.*', '', raw_location).strip()
                        else:
                            in_time = "未知"
                            location = raw_location
                            
                        # 5. 组装代理链接并按参考图对齐
                        url_str = f"{protocol}://{ip}:{port}"
                        
                        # ljust(36) 让左侧的代理链接统一占据 36 个字符的宽度，不足的部分用空格补齐。
                        # 这完全模仿了 SCR-20260713-ospe.jpg 中整齐的垂直对齐效果。
                        proxy_line = f"{url_str.ljust(36)}入库时间：{in_time}  {location}"
                        
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
                # 完美还原头部固定信息格式
                f.write(f"# 代理列表更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n")
                f.write("# 实时抓取于免费公共代理池: https://proxy-socks5.com\n")
                f.write("# 最好用的代理资源\n\n")
                
                # 写入每一行代理
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            print(f"代理列表已保存到 {filename}")
            return True
            
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

def main():
    # 记得替换为你的有效 Cookie 字符串以获取未脱敏数据（家宽除外）
    my_cookie = "session=eyJwb3J0IjozMTI0OSwidXNlcm5hbWUiOiJtb29vb29zcyIsInV1aWQiOiI5MjA3YjgzMi1lNmFjLTQ1N2QtODkwZS1kN2FhMzQ0ZjU3ZDEifQ.alSdAQ.Oz1lKlfQgc2closhId5yGFquuVA"
    
    scraper = ProxyListScraper(cookie_string=my_cookie)
    proxies = scraper.scrape_proxy_list()
    
    if proxies:
        scraper.save_to_file(proxies)
    else:
        print("未能获取到代理数据")

if __name__ == "__main__":
    main()
