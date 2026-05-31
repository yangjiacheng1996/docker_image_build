"""
Whisper Server - 基于 FastAPI 的音频/视频转文字服务
"""

import os
import json
import hashlib
import shutil
import subprocess
import threading
import zipfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from fastapi import BackgroundTasks
from pydantic import BaseModel

from settings import (
    WORKSPACE,
    WHISPER_CMD,
    DEFAULT_MODEL,
    TRANSCRIPTION_TIMEOUT,
    ALLOWED_EXTENSIONS,
    FORBIDDEN_NAMES,
    FORBIDDEN_EXTENSIONS,
    WHISPER_RESOURCES_DIR,
    MAX_TRANSCRIPTION_DIRS,
    ALL_LANGUAGES,
)


app = FastAPI(title="Whisper Server", version="v0.0.1")

# 全局状态管理
class TranscriptionState:
    """转录状态管理"""
    def __init__(self):
        self.lock = threading.Lock()
        self.processing = False
        self.current_transcription_dir: Optional[str] = None
    
    def is_idle(self) -> bool:
        with self.lock:
            return not self.processing
    
    def start(self, transcription_dir: str) -> None:
        with self.lock:
            self.processing = True
            self.current_transcription_dir = transcription_dir
    
    def stop(self) -> None:
        with self.lock:
            self.processing = False
            self.current_transcription_dir = None
    
    def get_processing_dir(self) -> Optional[str]:
        with self.lock:
            return self.current_transcription_dir


state = TranscriptionState()

# 转录结果存储
transcription_results: dict = {}


def get_workspace() -> Path:
    """获取工作目录路径"""
    return Path(WORKSPACE)


def get_resources_dir() -> Path:
    """获取 whisper_resources 目录路径"""
    return get_workspace() / WHISPER_RESOURCES_DIR


def get_sha256(file_path: Path) -> str:
    """计算文件的 SHA256 值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_transcription_dir(filename: str) -> str:
    """将文件名转换为转录目录名（将 . 替换为 _）"""
    return filename.replace(".", "_")


def ensure_workspace_dirs() -> None:
    """确保工作目录和子目录存在"""
    workspace = get_workspace()
    resources_dir = get_resources_dir()
    workspace.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """服务启动时初始化目录"""
    ensure_workspace_dirs()


# ==================== 文件管理接口 ====================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传音视频文件
    """
    # 检查文件扩展名
    filename = file.filename
    if not filename:
        return JSONResponse({"success": False, "error": "no filename provided"}, status_code=400)
    
    ext = Path(filename).suffix.lower()
    
    # 禁止上传 .lock、.json 文件
    if ext in FORBIDDEN_EXTENSIONS:
        return JSONResponse({"success": False, "error": f"forbidden file extension: {ext}"}, status_code=400)
    
    # 禁止文件名为 whisper_resources
    if filename in FORBIDDEN_NAMES:
        return JSONResponse({"success": False, "error": "forbidden filename: whisper_resources"}, status_code=400)
    
    # 检查扩展名
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse({"success": False, "error": f"unsupported file extension: {ext}"}, status_code=400)
    
    resources_dir = get_resources_dir()
    file_path = resources_dir / filename
    
    # 检查文件是否已存在
    if file_path.exists():
        return JSONResponse({"success": False, "error": "file already exists"}, status_code=409)
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
    return {"success": True, "filename": filename}


@app.get("/files")
async def list_files():
    """
    返回 whisper_resources 目录下所有文件列表，并计算每个文件的 SHA256 值
    """
    resources_dir = get_resources_dir()
    sha256_json_path = get_workspace() / "sha256.json"
    files_data = []
    sha256_map = {}
    
    if resources_dir.exists():
        for file_path in resources_dir.iterdir():
            if file_path.is_file():
                sha256 = get_sha256(file_path)
                files_data.append({"name": file_path.name, "sha256": sha256})
                sha256_map[file_path.name] = sha256
    
    # 写入 sha256.json
    try:
        with open(sha256_json_path, "w") as f:
            json.dump(sha256_map, f, indent=2)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
    return {"files": files_data}


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """
    删除指定文件
    """
    resources_dir = get_resources_dir()
    file_path = resources_dir / filename
    
    if not file_path.exists():
        return JSONResponse({"success": False, "error": "file not found"}, status_code=404)
    
    try:
        file_path.unlink()
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
    return {"success": True}


@app.delete("/files")
async def delete_all_files():
    """
    清空 whisper_resources 目录下所有文件
    """
    resources_dir = get_resources_dir()
    deleted = 0
    
    if resources_dir.exists():
        for file_path in resources_dir.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted += 1
                except Exception:
                    pass
    
    return {"success": True, "deleted": deleted}


# ==================== GPU 状态接口 ====================

@app.get("/idle")
async def check_idle():
    """
    检查 GPU 空闲状态
    """
    if state.is_idle():
        return {"idle": True}
    else:
        processing_dir = state.get_processing_dir()
        return {"idle": False, "processing": processing_dir}


# ==================== 转录接口 ====================

class WhisperRequest(BaseModel):
    filename: str
    language: str = "Chinese"


def run_transcription(transcription_dir: str, file_path: Path, language: str):
    """在线程中运行转录任务"""
    workspace = get_workspace()
    output_dir = workspace / transcription_dir
    
    # 创建转录输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入初始状态
    result_file = output_dir / "result.json"
    with open(result_file, "w") as f:
        json.dump({"result": "processing"}, f)
    
    # 构建 whisper 命令
    cmd = [
        WHISPER_CMD,
        str(file_path),
        "--output_dir", str(output_dir),
        "--model", DEFAULT_MODEL,
        "--language", language,
    ]
    
    try:
        # 执行转录命令
        process = subprocess.run(
            cmd,
            timeout=TRANSCRIPTION_TIMEOUT,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            with open(result_file, "w") as f:
                json.dump({"result": "success"}, f)
        else:
            error_msg = process.stderr or "unknown error"
            with open(result_file, "w") as f:
                json.dump({"result": "failed", "error": error_msg}, f)
    
    except subprocess.TimeoutExpired:
        with open(result_file, "w") as f:
            json.dump({"result": "timeout"}, f)
    except Exception as e:
        with open(result_file, "w") as f:
            json.dump({"result": "failed", "error": str(e)}, f)
    finally:
        state.stop()


def count_transcription_dirs() -> int:
    """计算当前转录目录数量"""
    workspace = get_workspace()
    count = 0
    if workspace.exists():
        for item in workspace.iterdir():
            if item.is_dir() and item.name != WHISPER_RESOURCES_DIR:
                # 检查是否是转录目录（包含 result.json）
                if (item / "result.json").exists():
                    count += 1
    return count


@app.post("/whisper")
async def start_transcription(request: WhisperRequest):
    """
    发起转录任务
    """
    # 检查 GPU 是否空闲
    if not state.is_idle():
        return JSONResponse(
            {"success": False, "error": "GPU busy, try again later"},
            status_code=409
        )
    
    # 检查文件是否存在
    filename = request.filename
    resources_dir = get_resources_dir()
    file_path = resources_dir / filename
    
    if not file_path.exists():
        return JSONResponse({"success": False, "error": "file not found"}, status_code=404)
    
    # 验证语言
    if request.language not in ALL_LANGUAGES:
        return JSONResponse(
            {"success": False, "error": f"unsupported language: {request.language}"},
            status_code=400
        )
    
    # 检查转录目录数量
    if count_transcription_dirs() >= MAX_TRANSCRIPTION_DIRS:
        return JSONResponse(
            {"success": False, "error": "too many transcriptions, please delete some first"},
            status_code=409
        )
    
    # 生成转录目录名
    transcription_dir = get_transcription_dir(filename)
    
    # 保存结果到全局状态
    transcription_results[transcription_dir] = {"result": "processing"}
    
    # 启动转录线程
    state.start(transcription_dir)
    thread = threading.Thread(
        target=run_transcription,
        args=(transcription_dir, file_path, request.language)
    )
    thread.daemon = True
    thread.start()
    
    return {
        "success": True,
        "transcription_dir": transcription_dir,
        "message": "transcription started"
    }


# ==================== 结果查询接口 ====================

@app.get("/result")
async def get_all_results():
    """
    获取所有转录任务状态
    """
    workspace = get_workspace()
    results = {}
    
    if workspace.exists():
        for item in workspace.iterdir():
            if item.is_dir() and item.name != WHISPER_RESOURCES_DIR:
                result_file = item / "result.json"
                if result_file.exists():
                    try:
                        with open(result_file, "r") as f:
                            results[item.name] = json.load(f)
                    except Exception:
                        results[item.name] = {"result": "unknown"}
    
    return {"results": results}


@app.get("/result/{filename}")
async def get_transcription_result(filename: str):
    """
    获取指定文件的转录结果文件列表
    """
    transcription_dir = get_transcription_dir(filename)
    dir_path = get_workspace() / transcription_dir
    
    if not dir_path.exists():
        return JSONResponse({"success": False, "error": "transcription not found"}, status_code=404)
    
    files = []
    if dir_path.exists():
        for f in dir_path.iterdir():
            if f.is_file():
                files.append(f.name)
    
    return {
        "filename": filename,
        "transcription_dir": transcription_dir,
        "files": sorted(files)
    }


# ==================== 下载接口 ====================

@app.get("/download/{filename}")
async def download_transcription(filename: str):
    """
    下载指定转录目录的 zip 包
    """
    transcription_dir = get_transcription_dir(filename)
    dir_path = get_workspace() / transcription_dir
    zip_path = get_workspace() / f"{transcription_dir}.zip"
    
    if not dir_path.exists():
        return JSONResponse({"success": False, "error": "transcription not found"}, status_code=404)
    
    # 如果 zip 文件已存在，先删除
    if zip_path.exists():
        try:
            zip_path.unlink()
        except Exception:
            pass
    
    # 创建 zip 包
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
    # 返回文件流
    def read_file():
        with open(zip_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    async def iterfile():
        for chunk in await run_in_threadpool(read_file):
            yield chunk
    
    def cleanup_zip():
        try:
            if zip_path.exists():
                zip_path.unlink()
        except Exception:
            pass
    
    return StreamingResponse(
        iterfile(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={transcription_dir}.zip"},
        background=BackgroundTasks([cleanup_zip])
    )


# ==================== 转录目录管理接口 ====================

@app.delete("/transcriptions/{transcription_dir}")
async def delete_transcription_dir(transcription_dir: str):
    """
    删除指定的转录目录及其所有文件
    """
    dir_path = get_workspace() / transcription_dir
    
    if not dir_path.exists():
        return JSONResponse({"success": False, "error": "transcription not found"}, status_code=404)
    
    try:
        shutil.rmtree(dir_path)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
    # 从全局状态中移除
    if transcription_dir in transcription_results:
        del transcription_results[transcription_dir]
    
    return {"success": True}


@app.delete("/transcriptions")
async def delete_all_transcriptions():
    """
    清空所有转录目录
    """
    workspace = get_workspace()
    deleted = 0
    
    if workspace.exists():
        for item in workspace.iterdir():
            if item.is_dir() and item.name != WHISPER_RESOURCES_DIR:
                # 检查是否是转录目录
                if (item / "result.json").exists():
                    try:
                        shutil.rmtree(item)
                        deleted += 1
                    except Exception:
                        pass
    
    # 清空全局状态
    transcription_results.clear()
    
    return {"success": True, "deleted": deleted}


@app.delete("/zips")
async def cleanup_zips():
    """
    清理 workspace 目录下所有残留的 zip 文件
    """
    workspace = get_workspace()
    deleted = 0
    
    if workspace.exists():
        for file_path in workspace.glob("*.zip"):
            try:
                file_path.unlink()
                deleted += 1
            except Exception:
                pass
    
    return {"success": True, "deleted": deleted}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)