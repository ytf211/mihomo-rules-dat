#!/usr/bin/env python3
import requests
import os
from datetime import datetime

# 规则源配置
SOURCES = [
    {
        'url': 'https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/master/SMAdHosts',
        'name': 'SM-Ad-FuckU-hosts'
    }
]

OUTPUT_FILE = 'mihomo/rulest/app_ad.yaml'

def download_hosts(url):
    """下载 hosts 文件"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return None

def parse_hosts(content):
    """解析 hosts 文件，提取域名"""
    domains = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ['0.0.0.0', '127.0.0.1']:
            domains.append(parts[1])
    return domains

def convert_to_yaml(domains, output_file):
    """转换为 YAML 格式"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    unique_domains = sorted(set(domains))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("payload:\n")
        f.write(f"  # 内容：Custom Block List\n")
        f.write(f"  # 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  # 数量：{len(unique_domains)}条\n")
        
        for domain in unique_domains:
            f.write(f"  - DOMAIN-SUFFIX,{domain}\n")
    
    return len(unique_domains)

def main():
    print("=" * 60)
    print("步骤 1: 开始处理广告拦截规则（hosts -> YAML）")
    print("=" * 60)
    
    all_domains = []
    
    for source in SOURCES:
        content = download_hosts(source['url'])
        if content:
            domains = parse_hosts(content)
            all_domains.extend(domains)
            print(f"✓ 从 {source['name']} 获取 {len(domains)} 条记录")
    
    if not all_domains:
        print("✗ 错误：未获取到任何规则")
        return 1
    
    count = convert_to_yaml(all_domains, OUTPUT_FILE)
    print(f"✓ 成功转换 {count} 条唯一记录")
    print(f"✓ 输出文件：{OUTPUT_FILE}")
    print()
    
    return 0

if __name__ == '__main__':
    exit(main())