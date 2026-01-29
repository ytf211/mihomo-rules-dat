#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
import platform
import urllib.request
import json
import gzip
import shutil

RULEST_DIR = 'mihomo/rulest'
MRS_OUTPUT_DIR = f'{RULEST_DIR}/mrs'
MIHOMO_PATH = './mihomo-bin'

def detect_architecture():
    """检测当前系统架构"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # 转换架构名称
    arch_map = {
        'x86_64': 'amd64',
        'amd64': 'amd64',
        'aarch64': 'arm64',
        'arm64': 'arm64',
        'armv7l': 'armv7',
        'i386': '386',
        'i686': '386'
    }
    
    arch = arch_map.get(machine, machine)
    
    print(f"检测到系统: {system}, 架构: {arch}")
    return system, arch

def download_mihomo(system, arch):
    """下载适配当前架构的 mihomo"""
    print("=" * 60)
    print("步骤 3: 下载 mihomo")
    print("=" * 60)
    
    try:
        # 获取 release 信息
        release_url = "https://api.github.com/repos/chen08209/Clash.Meta/releases/tags/Prerelease-Alpha"
        print(f"正在获取 release 信息...")
        
        with urllib.request.urlopen(release_url) as response:
            release_data = json.loads(response.read())
        
        # 构建文件名模式
        if system == 'darwin':
            pattern = f"mihomo-darwin-{arch}-alpha"
        elif system == 'linux':
            pattern = f"mihomo-linux-{arch}-alpha"
        else:
            print(f"✗ 不支持的操作系统: {system}")
            return False
        
        # 查找匹配的下载链接
        download_url = None
        for asset in release_data.get('assets', []):
            name = asset['name']
            if (pattern in name and 
                name.endswith('.gz') and 
                'compatible' not in name and
                'go120' not in name and
                'go122' not in name and
                'go123' not in name):
                download_url = asset['browser_download_url']
                break
        
        if not download_url:
            print(f"✗ 未找到适配的 mihomo 版本: {pattern}")
            return False
        
        print(f"下载地址: {download_url}")
        print("正在下载...")
        
        # 下载文件
        urllib.request.urlretrieve(download_url, 'mihomo.gz')
        
        # 解压
        print("正在解压...")
        with gzip.open('mihomo.gz', 'rb') as f_in:
            with open(MIHOMO_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 设置执行权限
        os.chmod(MIHOMO_PATH, 0o755)
        
        # 清理压缩包
        os.remove('mihomo.gz')
        
        # 验证
        result = subprocess.run([MIHOMO_PATH, '-v'], capture_output=True, text=True)
        print(f"✓ mihomo 下载成功: {result.stdout.strip()}")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ 下载 mihomo 失败: {e}")
        return False

def check_mihomo():
    """检查 mihomo 是否存在"""
    print("=" * 60)
    print("步骤 2: 检查 mihomo")
    print("=" * 60)
    
    if os.path.exists(MIHOMO_PATH) and os.access(MIHOMO_PATH, os.X_OK):
        try:
            result = subprocess.run([MIHOMO_PATH, '-v'], capture_output=True, text=True)
            print(f"✓ 发现 mihomo: {result.stdout.strip()}")
            print()
            return True
        except:
            print("✗ mihomo 文件存在但无法执行")
            print()
            return False
    else:
        print("✗ 未找到 mihomo")
        print()
        return False

def find_all_yaml_files():
    """查找 rulest 目录下所有的 yaml 文件"""
    yaml_files = []
    for file in glob.glob(f'{RULEST_DIR}/**/*.yaml', recursive=True):
        # 排除 mrs 目录
        if '/mrs/' not in file:
            yaml_files.append(file)
    return yaml_files

def convert_yaml_to_mrs(yaml_file):
    """将单个 YAML 文件转换为 MRS 格式"""
    # 生成对应的 mrs 文件路径
    relative_path = os.path.relpath(yaml_file, RULEST_DIR)
    mrs_file = os.path.join(MRS_OUTPUT_DIR, relative_path.replace('.yaml', '.mrs'))
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(mrs_file), exist_ok=True)
    
    try:
        # 执行转换命令
        cmd = [MIHOMO_PATH, 'convert-ruleset', 'domain', 'yaml', yaml_file, mrs_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ {yaml_file} -> {mrs_file}")
            return True
        else:
            print(f"  ✗ {yaml_file} 转换失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ✗ {yaml_file} 转换出错: {e}")
        return False

def convert_all():
    """转换所有 YAML 文件为 MRS 格式"""
    print("=" * 60)
    print("步骤 4: 转换所有 YAML 文件为 MRS 格式")
    print("=" * 60)
    
    yaml_files = find_all_yaml_files()
    
    if not yaml_files:
        print("✗ 未找到任何 YAML 文件")
        return 1
    
    print(f"找到 {len(yaml_files)} 个 YAML 文件:")
    for f in yaml_files:
        print(f"  - {f}")
    print()
    
    success_count = 0
    for yaml_file in yaml_files:
        if convert_yaml_to_mrs(yaml_file):
            success_count += 1
    
    print()
    print(f"✓ 转换完成: {success_count}/{len(yaml_files)} 个文件成功")
    print(f"✓ MRS 文件保存在: {MRS_OUTPUT_DIR}")
    print()
    
    return 0 if success_count == len(yaml_files) else 1

def main():
    print("\n" + "=" * 60)
    print("Mihomo Rules Converter - YAML to MRS")
    print("=" * 60)
    print()
    
    # 检查 mihomo
    has_mihomo = check_mihomo()
    
    # 如果没有 mihomo，下载它
    if not has_mihomo:
        system, arch = detect_architecture()
        if not download_mihomo(system, arch):
            print("✗ 无法获取 mihomo，转换终止")
            return 1
    
    # 转换所有 YAML 文件
    return convert_all()

if __name__ == '__main__':
    exit(main())