#!/usr/bin/env python3
"""
Whisper Client CLI - 命令行工具，用于与 Whisper Server 交互

用法:
    python client_cli.py --ip <ip> --port <port> upload <file_path> [language]
    python client_cli.py --ip <ip> --port <port> files
    python client_cli.py --ip <ip> --port <port> delete <filename>
    python client_cli.py --ip <ip> --port <port> delete-all
    python client_cli.py --ip <ip> --port <port> idle
    python client_cli.py --ip <ip> --port <port> transcribe <filename> [language]
    python client_cli.py --ip <ip> --port <port> result
    python client_cli.py --ip <ip> --port <port> result-file <filename>
    python client_cli.py --ip <ip> --port <port> download <filename>
    python client_cli.py --ip <ip> --port <port> delete-transcription <transcription_dir>
    python client_cli.py --ip <ip> --port <port> delete-all-transcriptions
    python client_cli.py --ip <ip> --port <port> cleanup-zips
"""

import argparse
import sys
import os
import json
import requests
from pathlib import Path
from typing import Optional


def get_base_url(ip: str, port: int) -> str:
    """获取服务器基础URL"""
    return f"http://{ip}:{port}"


def upload_file(ip: str, port: int, file_path: str, language: str = "Chinese") -> bool:
    """上传音视频文件并发起转录"""
    base_url = get_base_url(ip, port)
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return False
    
    filename = os.path.basename(file_path)
    
    # 1. 上传文件
    print(f"上传文件: {filename}...")
    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(f"{base_url}/upload", files=files, timeout=600)
    
    if response.status_code != 200:
        result = response.json()
        print(f"上传失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"上传成功: {result.get('filename')}")
    
    # 2. 发起转录
    print(f"发起转录任务 (语言: {language})...")
    whisper_data = {
        "filename": filename,
        "language": language
    }
    response = requests.post(f"{base_url}/whisper", json=whisper_data)
    
    if response.status_code != 200:
        result = response.json()
        print(f"转录启动失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"转录已启动, 目录: {result.get('transcription_dir')}")
    return True


def list_files(ip: str, port: int) -> bool:
    """获取服务器上的文件列表"""
    base_url = get_base_url(ip, port)
    
    print("获取文件列表...")
    response = requests.get(f"{base_url}/files")
    
    if response.status_code != 200:
        result = response.json()
        print(f"获取失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    files = result.get("files", [])
    
    if not files:
        print("服务器上没有文件")
        return True
    
    print(f"\n文件列表 (共 {len(files)} 个):")
    print("-" * 80)
    for f in files:
        print(f"  {f['name']:<40} SHA256: {f['sha256']}")
    print("-" * 80)
    
    return True


def delete_file(ip: str, port: int, filename: str) -> bool:
    """删除服务器上的指定文件"""
    base_url = get_base_url(ip, port)
    
    print(f"删除文件: {filename}...")
    response = requests.delete(f"{base_url}/files/{filename}")
    
    if response.status_code == 404:
        print("文件不存在")
        return False
    
    if response.status_code != 200:
        result = response.json()
        print(f"删除失败: {result.get('error', '未知错误')}")
        return False
    
    print("删除成功")
    return True


def delete_all_files(ip: str, port: int) -> bool:
    """删除服务器上的所有文件"""
    base_url = get_base_url(ip, port)
    
    print("清空所有上传文件...")
    response = requests.delete(f"{base_url}/files")
    
    if response.status_code != 200:
        result = response.json()
        print(f"删除失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"删除成功, 共删除 {result.get('deleted', 0)} 个文件")
    return True


def check_idle(ip: str, port: int) -> bool:
    """检查GPU空闲状态"""
    base_url = get_base_url(ip, port)
    
    print("检查GPU状态...")
    response = requests.get(f"{base_url}/idle")
    
    if response.status_code != 200:
        result = response.json()
        print(f"检查失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    if result.get("idle"):
        print("GPU状态: 空闲")
    else:
        print(f"GPU状态: 占用中 (处理: {result.get('processing', 'unknown')})")
    
    return True


def start_transcription(ip: str, port: int, filename: str, language: str = "Chinese") -> bool:
    """发起转录任务"""
    base_url = get_base_url(ip, port)
    
    print(f"发起转录任务: {filename} (语言: {language})...")
    whisper_data = {
        "filename": filename,
        "language": language
    }
    response = requests.post(f"{base_url}/whisper", json=whisper_data)
    
    if response.status_code == 404:
        print("文件不存在，请先上传")
        return False
    
    if response.status_code == 409:
        result = response.json()
        print(f"转录失败: {result.get('error', '未知错误')}")
        return False
    
    if response.status_code != 200:
        result = response.json()
        print(f"转录失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"转录已启动")
    print(f"  转录目录: {result.get('transcription_dir')}")
    print(f"  消息: {result.get('message')}")
    return True


def get_all_results(ip: str, port: int) -> bool:
    """获取所有转录任务状态"""
    base_url = get_base_url(ip, port)
    
    print("获取所有转录任务状态...")
    response = requests.get(f"{base_url}/result")
    
    if response.status_code != 200:
        result = response.json()
        print(f"获取失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    results = result.get("results", {})
    
    if not results:
        print("没有转录任务")
        return True
    
    print(f"\n转录任务状态 (共 {len(results)} 个):")
    print("-" * 80)
    for name, data in results.items():
        status = data.get("result", "unknown")
        if status == "success":
            print(f"  {name:<40} 状态: 成功")
        elif status == "failed":
            error = data.get("error", "")
            print(f"  {name:<40} 状态: 失败 - {error}")
        elif status == "timeout":
            print(f"  {name:<40} 状态: 超时")
        elif status == "processing":
            print(f"  {name:<40} 状态: 处理中")
        else:
            print(f"  {name:<40} 状态: {status}")
    print("-" * 80)
    
    return True


def get_transcription_result(ip: str, port: int, filename: str) -> bool:
    """获取指定文件的转录结果"""
    base_url = get_base_url(ip, port)
    
    print(f"获取转录结果: {filename}...")
    response = requests.get(f"{base_url}/result/{filename}")
    
    if response.status_code == 404:
        print("转录结果不存在")
        return False
    
    if response.status_code != 200:
        result = response.json()
        print(f"获取失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"\n转录结果信息:")
    print(f"  文件名: {result.get('filename')}")
    print(f"  转录目录: {result.get('transcription_dir')}")
    print(f"  结果文件:")
    for f in result.get("files", []):
        print(f"    - {f}")
    
    return True


def download_transcription(ip: str, port: int, filename: str, output_dir: Optional[str] = None) -> bool:
    """下载转录结果ZIP包"""
    base_url = get_base_url(ip, port)
    
    transcription_dir = filename.replace(".", "_")
    output_path = f"{transcription_dir}.zip"
    
    if output_dir:
        output_path = os.path.join(output_dir, output_path)
    
    print(f"下载转录结果: {filename}...")
    response = requests.get(f"{base_url}/download/{filename}", stream=True)
    
    if response.status_code == 404:
        print("转录结果不存在")
        return False
    
    if response.status_code != 200:
        result = response.json()
        print(f"下载失败: {result.get('error', '未知错误')}")
        return False
    
    # 保存文件
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"下载完成: {output_path}")
    return True


def delete_transcription(ip: str, port: int, transcription_dir: str) -> bool:
    """删除指定的转录目录"""
    base_url = get_base_url(ip, port)
    
    print(f"删除转录目录: {transcription_dir}...")
    response = requests.delete(f"{base_url}/transcriptions/{transcription_dir}")
    
    if response.status_code == 404:
        print("转录目录不存在")
        return False
    
    if response.status_code != 200:
        result = response.json()
        print(f"删除失败: {result.get('error', '未知错误')}")
        return False
    
    print("删除成功")
    return True


def delete_all_transcriptions(ip: str, port: int) -> bool:
    """清空所有转录目录"""
    base_url = get_base_url(ip, port)
    
    print("清空所有转录目录...")
    response = requests.delete(f"{base_url}/transcriptions")
    
    if response.status_code != 200:
        result = response.json()
        print(f"删除失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"删除成功, 共删除 {result.get('deleted', 0)} 个转录目录")
    return True


def cleanup_zips(ip: str, port: int) -> bool:
    """清理残留的ZIP文件"""
    base_url = get_base_url(ip, port)
    
    print("清理残留ZIP文件...")
    response = requests.delete(f"{base_url}/zips")
    
    if response.status_code != 200:
        result = response.json()
        print(f"清理失败: {result.get('error', '未知错误')}")
        return False
    
    result = response.json()
    print(f"清理成功, 共删除 {result.get('deleted', 0)} 个ZIP文件")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Whisper Client CLI - 与 Whisper Server 交互的命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  上传并转录文件:
    python client_cli.py --ip 192.168.1.100 --port 8000 upload /path/to/video.mp4 Chinese

  查看服务器文件:
    python client_cli.py --ip 192.168.1.100 --port 8000 files

  检查GPU状态:
    python client_cli.py --ip 192.168.1.100 --port 8000 idle

  获取所有转录结果:
    python client_cli.py --ip 192.168.1.100 --port 8000 result

  下载转录结果:
    python client_cli.py --ip 192.168.1.100 --port 8000 download video.mp4
        """
    )
    
    parser.add_argument("--ip", required=True, help="服务器IP地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # upload 命令
    upload_parser = subparsers.add_parser("upload", help="上传文件并转录")
    upload_parser.add_argument("file_path", help="本地文件路径")
    upload_parser.add_argument("language", nargs="?", default="Chinese", help="语言 (默认: Chinese)")
    
    # files 命令
    subparsers.add_parser("files", help="获取文件列表")
    
    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除指定文件")
    delete_parser.add_argument("filename", help="要删除的文件名")
    
    # delete-all 命令
    subparsers.add_parser("delete-all", help="删除所有上传文件")
    
    # idle 命令
    subparsers.add_parser("idle", help="检查GPU空闲状态")
    
    # transcribe 命令
    transcribe_parser = subparsers.add_parser("transcribe", help="发起转录任务")
    transcribe_parser.add_argument("filename", help="服务器上的文件名")
    transcribe_parser.add_argument("language", nargs="?", default="Chinese", help="语言 (默认: Chinese)")
    
    # result 命令
    subparsers.add_parser("result", help="获取所有转录任务状态")
    
    # result-file 命令
    result_file_parser = subparsers.add_parser("result-file", help="获取指定文件的转录结果")
    result_file_parser.add_argument("filename", help="文件名")
    
    # download 命令
    download_parser = subparsers.add_parser("download", help="下载转录结果ZIP包")
    download_parser.add_argument("filename", help="文件名")
    download_parser.add_argument("--output", "-o", help="输出目录")
    
    # delete-transcription 命令
    delete_trans_parser = subparsers.add_parser("delete-transcription", help="删除指定转录目录")
    delete_trans_parser.add_argument("transcription_dir", help="转录目录名")
    
    # delete-all-transcriptions 命令
    subparsers.add_parser("delete-all-transcriptions", help="删除所有转录目录")
    
    # cleanup-zips 命令
    subparsers.add_parser("cleanup-zips", help="清理残留ZIP文件")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    success = False
    
    if args.command == "upload":
        success = upload_file(args.ip, args.port, args.file_path, args.language)
    elif args.command == "files":
        success = list_files(args.ip, args.port)
    elif args.command == "delete":
        success = delete_file(args.ip, args.port, args.filename)
    elif args.command == "delete-all":
        success = delete_all_files(args.ip, args.port)
    elif args.command == "idle":
        success = check_idle(args.ip, args.port)
    elif args.command == "transcribe":
        success = start_transcription(args.ip, args.port, args.filename, args.language)
    elif args.command == "result":
        success = get_all_results(args.ip, args.port)
    elif args.command == "result-file":
        success = get_transcription_result(args.ip, args.port, args.filename)
    elif args.command == "download":
        success = download_transcription(args.ip, args.port, args.filename, args.output)
    elif args.command == "delete-transcription":
        success = delete_transcription(args.ip, args.port, args.transcription_dir)
    elif args.command == "delete-all-transcriptions":
        success = delete_all_transcriptions(args.ip, args.port)
    elif args.command == "cleanup-zips":
        success = cleanup_zips(args.ip, args.port)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()