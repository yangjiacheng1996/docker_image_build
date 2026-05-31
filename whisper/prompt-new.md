# Whisper Server 接口设计

## 概述

本服务基于 PyTorch 2.12 (CUDA 13.0.3, Python 3.11, Ubuntu 24.04) 容器镜像构建，提供音频/视频转文字的 RESTful 接口。
使用fastAPI框架进行接口开发
whisper 命令路径：`/root/miniconda3/bin/whisper`

转录命令格式：
```
/root/miniconda3/bin/whisper /opt/workspace/whisper_resources/<filename> \
    --output_dir /opt/workspace/<transcription_dir> \
    --model turbo --language <language>
```

工作目录：`/opt/workspace`，其下创建 `whisper_resources` 子目录存放用户上传的音视频文件。

---

## 接口清单

### 1. POST /upload

上传音视频文件。

**请求**
- Content-Type: `multipart/form-data`
- 字段名: `file`

**响应**
- 成功: `{"success": true, "filename": "xxx.mp4"}`
- 失败: `{"success": false, "error": "error message"}`

**约束**
- 禁止上传 `.lock`、`.json` 文件
- 禁止文件名为 `whisper_resources`
- 单次上传超时 10 分钟

---

### 2. GET /files

返回 `whisper_resources` 目录下所有文件列表，并计算每个文件的 SHA256 值。

**响应**
```json
{
  "files": [
    {"name": "file1.mp4", "sha256": "abc123..."},
    {"name": "file2.wav", "sha256": "def456..."}
  ]
}
```

**说明**
- 每个文件的 SHA256 值由服务器计算后附加在响应中
- 同时在工作目录生成 `sha256.json`，记录文件名与 SHA256 值的对应关系（每次调用覆盖）

---

### 3. DELETE /files/<filename>

删除指定文件。

**响应**
- 成功: `{"success": true}`
- 失败: `{"success": false, "error": "file not found"}`

---

### 4. DELETE /files

清空 `whisper_resources` 目录下所有文件。

**响应**
- 成功: `{"success": true, "deleted": 3}`

---

### 5. GET /idle

检查 GPU 空闲状态（whisper 命令独占 GPU，一次只能处理一个任务）。

**响应**
- 空闲: `{"idle": true}`
- 占用中: `{"idle": false, "processing": "<transcription_dir>"}`

---

### 6. POST /whisper

发起转录任务。

**请求**
```json
{
  "filename": "xxx.mp4",
  "language": "Chinese"
}
```

**language 可选值**: `af`, `am`, `ar`, `as`, `az`, `ba`, `be`, `bg`, `bn`, `bo`, `br`, `bs`, `ca`, `cs`, `cy`, `da`, `de`, `el`, `en`, `es`, `et`, `eu`, `fa`, `fi`, `fo`, `fr`, `gl`, `gu`, `ha`, `haw`, `he`, `hi`, `hr`, `ht`, `hu`, `hy`, `id`, `is`, `it`, `ja`, `jw`, `ka`, `kk`, `km`, `kn`, `ko`, `la`, `lb`, `ln`, `lo`, `lt`, `lv`, `mg`, `mi`, `mk`, `ml`, `mn`, `mr`, `ms`, `mt`, `my`, `ne`, `nl`, `nn`, `no`, `oc`, `pa`, `pl`, `ps`, `pt`, `ro`, `ru`, `sa`, `sd`, `si`, `sk`, `sl`, `sn`, `so`, `sq`, `sr`, `su`, `sv`, `sw`, `ta`, `te`, `tg`, `th`, `tk`, `tl`, `tr`, `tt`, `uk`, `ur`, `uz`, `vi`, `yi`, `yo`, `yue`, `zh`, `Afrikaans`, `Albanian`, `Amharic`, `Arabic`, `Armenian`, `Assamese`, `Azerbaijani`, `Bashkir`, `Basque`, `Belarusian`, `Bengali`, `Bosnian`, `Breton`, `Bulgarian`, `Burmese`, `Cantonese`, `Castilian`, `Catalan`, `Chinese`, `Croatian`, `Czech`, `Danish`, `Dutch`, `English`, `Estonian`, `Faroese`, `Finnish`, `Flemish`, `French`, `Galician`, `Georgian`, `German`, `Greek`, `Gujarati`, `Haitian`, `Haitian Creole`, `Hausa`, `Hawaiian`, `Hebrew`, `Hindi`, `Hungarian`, `Icelandic`, `Indonesian`, `Italian`, `Japanese`, `Javanese`, `Kannada`, `Kazakh`, `Khmer`, `Korean`, `Lao`, `Latin`, `Latvian`, `Letzeburgesch`, `Lingala`, `Lithuanian`, `Luxembourgish`, `Macedonian`, `Malagasy`, `Malay`, `Malayalam`, `Maltese`, `Mandarin`, `Maori`, `Marathi`, `Moldavian`, `Moldovan`, `Mongolian`, `Myanmar`, `Nepali`, `Norwegian`, `Nynorsk`, `Occitan`, `Panjabi`, `Pashto`, `Persian`, `Polish`, `Portuguese`, `Punjabi`, `Pushto`, `Romanian`, `Russian`, `Sanskrit`, `Serbian`, `Shona`, `Sindhi`, `Sinhala`, `Sinhalese`, `Slovak`, `Slovenian`, `Somali`, `Spanish`, `Sundanese`, `Swahili`, `Swedish`, `Tagalog`, `Tajik`, `Tamil`, `Tatar`, `Telugu`, `Thai`, `Tibetan`, `Turkish`, `Turkmen`, `Ukrainian`, `Urdu`, `Uzbek`, `Valencian`, `Vietnamese`, `Welsh`, `Yiddish`, `Yoruba`

**响应**
- 成功: `{"success": true, "transcription_dir": "xxx", "message": "transcription started"}`
- 文件不存在: `{"success": false, "error": "file not found"}`
- GPU 占用: `{"success": false, "error": "GPU busy, try again later"}`

**转录目录命名**: `filename` 中的 `.` 替换为 `_`

**result.json 格式**:
- 成功: `{"result": "success"}`
- 超时: `{"result": "timeout"}`
- 失败: `{"result": "failed", "error": "<error message>"}`

---

### 7. GET /result

获取所有转录任务状态。

**响应**
```json
{
  "results": {
    "hello_mp4": {"result": "success"},
    "video_mp4": {"result": "failed", "error": "..."}
  }
}
```

---

### 8. GET /result/<filename>

获取指定文件的转录结果文件列表。

**响应**
```json
{
  "filename": "hello.mp4",
  "transcription_dir": "hello_mp4",
  "files": ["hello_mp4.json", "hello_mp4.srt", "hello_mp4.txt", "hello_mp4.tsv", "hello_mp4.vtt"]
}
```

---

### 9. GET /download/<filename>

下载指定转录目录的 zip 包。

**响应**
- 成功: zip 文件二进制流
- 失败: `{"success": false, "error": "transcription not found"}`

**zip 包清理**: 下载完成后服务器端自动删除该 zip 包。

---

### 10. DELETE /transcriptions/<transcription_dir>

删除指定的转录目录及其所有文件。

**响应**
- 成功: `{"success": true}`
- 失败: `{"success": false, "error": "transcription not found"}`

---

### 11. DELETE /transcriptions

清空所有转录目录。

**响应**
- 成功: `{"success": true, "deleted": 5}`

---

### 12. DELETE /zips

清理 workspace 目录下所有残留的 zip 文件（用于处理 download 接口中断导致的残留包）。

**响应**
- 成功: `{"success": true, "deleted": 3}`

---

## 转录目录管理

转录目录存放在工作目录下，数量上限为 **10 个**。

当 `/whisper 接口调用时，如果已存在的转录目录数量达到 10 个，则返回错误：
```
{"success": false, "error": "too many transcriptions, please delete some first"}
```

用户需调用 `DELETE /transcriptions/<transcription_dir>` 或 `DELETE /transcriptions` 删除不需要的转录目录后再发起新任务。

---

## 配置 (settings.py)

```python
# 工作目录
WORKSPACE = "/opt/workspace"

# whisper 命令路径
WHISPER_CMD = "/root/miniconda3/bin/whisper"

# 默认模型
DEFAULT_MODEL = "turbo"

# 转录超时时间（秒）
TRANSCRIPTION_TIMEOUT = 23 * 3600

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    # 常见音频格式
    ".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".aiff", ".aif",
    ".opus", ".wma", ".ape",
    # 常见视频格式
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".mpg", ".mpeg",
    ".m4v", ".f4v", ".3gp", ".ts", ".mts", ".m2ts", ".vob", ".divx",
    ".rm", ".rmvb", ".asf"
}

# 禁止的文件名/扩展名
FORBIDDEN_NAMES = {"whisper_resources"}
FORBIDDEN_EXTENSIONS = {".lock", ".json"}

# whisper_resources 子目录
WHISPER_RESOURCES_DIR = "whisper_resources"

# 转录目录数量上限
MAX_TRANSCRIPTION_DIRS = 10

# 所有支持的语言（语言代码 + 语言名称）
ALL_LANGUAGES = LANGUAGE_CODES | LANGUAGE_NAMES