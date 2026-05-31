"""
Whisper Server Settings
"""

# 工作目录
WORKSPACE = "/opt/workspace"

# whisper 命令路径
WHISPER_CMD = "/root/miniconda3/bin/whisper"

# 默认模型
DEFAULT_MODEL = "turbo"

# 转录超时时间（秒）
TRANSCRIPTION_TIMEOUT = 23 * 3600

# 允许的文件扩展名（Whisper 基于 ffmpeg，支持更多音频视频格式）
ALLOWED_EXTENSIONS = {
    # 常见音频格式
    ".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".aiff", ".aif",
    ".opus", ".wma", ".ape", ".opus",
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

# 语言代码集合
LANGUAGE_CODES = {
    "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy",
    "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw",
    "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn",
    "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt",
    "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si",
    "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl",
    "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "yue", "zh"
}

# 支持的完整语言名称
LANGUAGE_NAMES = {
    "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani",
    "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese",
    "Cantonese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch",
    "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian",
    "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew",
    "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese",
    "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch",
    "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam",
    "Maltese", "Mandarin", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar",
    "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish",
    "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona",
    "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese",
    "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan",
    "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh",
    "Yiddish", "Yoruba"
}

# 所有支持的语言（代码和名称）
ALL_LANGUAGES = LANGUAGE_CODES | LANGUAGE_NAMES