import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
CACHE_DIR = BASE_DIR / 'cache'
TTS_CACHE_DIR = CACHE_DIR / 'tts'
TRANS_CACHE_DIR = CACHE_DIR / 'trans'
DICT_DIR = BASE_DIR / 'dict_with_variants'

# 创建目录
for directory in [DATA_DIR, CACHE_DIR, TTS_CACHE_DIR, TRANS_CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 文件限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'epub', 'doc', 'docx'}

# 文本处理
LINES_PER_SEGMENT = 50
CHARS_PER_SEGMENT = 500

# TTS配置
TTS_CACHE_DAYS = 3
TTS_DEFAULT_VOICE = {
    'zh': 'xiaoxiao',
    'en': 'en-US-AriaNeural',
    'ja': 'ja-JP-NanamisNeural'
}

# 翻译配置
TRANSLATION_CACHE_DAYS = 3
TRANSLATION_MODEL = 'tencent/Hunyuan-MT-7B'
TRANSLATION_API = 'https://api.siliconflow.cn/v1'

# 词典配置
DICT_FILES = {
    'dict': DICT_DIR / 'new.dict',
    'idx': DICT_DIR / 'new.idx',
    'ifo': DICT_DIR / 'new.ifo'
}

# 页面配置
ITEMS_PER_PAGE = 50