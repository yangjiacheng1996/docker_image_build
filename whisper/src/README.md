# Whisper Server

基于 FastAPI 的音频/视频转文字服务，提供 RESTful API 接口。

## 功能特性

- 支持多种音视频格式上传（mp3, wav, flac, m4a, mp4, mkv 等）
- 基于 OpenAI Whisper 的语音识别
- 异步转录处理，支持后台任务
- GPU 状态监控，确保资源独占
- 转录结果多格式导出（JSON, TXT, SRT, TSV, VTT）
- 完整的文件管理和转录目录管理接口

## 项目结构

```
whisper/src/
├── whisper_server.py    # FastAPI 服务主文件
├── settings.py         # 配置文件
├── client_cli.py       # 命令行客户端示例
└── requirements.txt   # Python 依赖
```

## 依赖安装

```bash
pip install -r requirements.txt
```

依赖列表：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `pydantic` - 数据验证
- `python-multipart` - 文件上传支持

## 启动服务

```bash
cd whisper/src
python whisper_server.py
```

服务默认运行在 `http://0.0.0.0:8000`

## API 接口

### 文件管理

| 接口 | 方法 | 描述 |
|------|------|------|
| `/upload` | POST | 上传音视频文件 |
| `/files` | GET | 获取已上传文件列表（含 SHA256） |
| `/files/{filename}` | DELETE | 删除指定文件 |
| `/files` | DELETE | 清空所有已上传文件 |

### 转录任务

| 接口 | 方法 | 描述 |
|------|------|------|
| `/idle` | GET | 检查 GPU 空闲状态 |
| `/whisper` | POST | 发起转录任务 |
| `/result` | GET | 获取所有转录任务状态 |
| `/result/{filename}` | GET | 获取指定文件的转录结果文件列表 |

### 结果下载

| 接口 | 方法 | 描述 |
|------|------|------|
| `/download/{filename}` | GET | 下载转录结果 zip 包 |

### 资源清理

| 接口 | 方法 | 描述 |
|------|------|------|
| `/transcriptions/{transcription_dir}` | DELETE | 删除指定转录目录 |
| `/transcriptions` | DELETE | 清空所有转录目录 |
| `/zips` | DELETE | 清理残留的 zip 文件 |

## 使用示例

### 1. 上传音视频文件

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/video.mp4"
```

响应：
```json
{"success": true, "filename": "video.mp4"}
```

### 2. 检查 GPU 空闲状态

```bash
curl "http://localhost:8000/idle"
```

响应：
```json
{"idle": true}
```

### 3. 发起转录任务

```bash
curl -X POST "http://localhost:8000/whisper" \
  -H "Content-Type: application/json" \
  -d '{"filename": "video.mp4", "language": "Chinese"}'
```

响应：
```json
{"success": true, "transcription_dir": "video_mp4", "message": "transcription started"}
```

### 4. 查询转录结果

```bash
# 查询所有任务状态
curl "http://localhost:8000/result"

# 查询指定文件的结果文件列表
curl "http://localhost:8000/result/video.mp4"
```

### 5. 下载转录结果

```bash
curl -O "http://localhost:8000/download/video.mp4"
```

### 6. 使用命令行客户端

```bash
# 上传文件
python client_cli.py upload /path/to/video.mp4

# 查看文件列表
python client_cli.py list

# 发起转录
python client_cli.py transcribe video.mp4 Chinese

# 下载结果
python client_cli.py download video.mp4
```

## 配置说明

配置文件 [`settings.py`](whisper/src/settings.py:1) 中可配置以下参数：

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `WORKSPACE` | `/opt/workspace` | 工作目录 |
| `WHISPER_CMD` | `/root/miniconda3/bin/whisper` | Whisper 命令路径 |
| `DEFAULT_MODEL` | `turbo` | 默认转录模型 |
| `TRANSCRIPTION_TIMEOUT` | `23 * 3600` | 转录超时时间（秒） |
| `MAX_TRANSCRIPTION_DIRS` | `10` | 最大转录目录数量 |
| `WHISPER_RESOURCES_DIR` | `whisper_resources` | 音视频文件存储子目录 |

## 支持的语言

支持 100+ 种语言，包括：
- 语言代码：`zh`, `en`, `ja`, `ko`, `fr`, `de`, `es` 等
- 语言名称：`Chinese`, `English`, `Japanese`, `Korean`, `French`, `German`, `Spanish` 等

完整列表见 [`settings.py`](whisper/src/settings.py:39) 中的 `ALL_LANGUAGES`。

## 支持的文件格式

### 音频格式
`.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.aac`, `.aiff`, `.aif`, `.opus`, `.wma`, `.ape`

### 视频格式
`.mp4`, `.mkv`, `.webm`, `.avi`, `.mov`, `.wmv`, `.mpg`, `.mpeg`, `.m4v`, `.f4v`, `.3gp`, `.ts`, `.mts`, `.m2ts`, `.vob`, `.divx`, `.rm`, `.rmvb`, `.asf`

## 注意事项

1. **GPU 独占**：Whisper 转录需要占用 GPU，同一时间只能处理一个任务
2. **目录上限**：最多同时存在 10 个转录目录，超出后需清理旧目录
3. **安全限制**：禁止上传 `.lock`、`.json` 文件，禁止文件名为 `whisper_resources`
4. **超时设置**：默认转录超时时间为 23 小时，超时后任务标记为 `timeout`
5. **自动清理**：下载完成后 zip 文件会自动删除