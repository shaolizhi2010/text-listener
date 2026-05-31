import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from config import CACHE_DIR, TTS_CACHE_DIR, TRANS_CACHE_DIR, TTS_CACHE_DAYS, TRANSLATION_CACHE_DAYS

class CacheManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.tts_cache_dir = TTS_CACHE_DIR
        self.trans_cache_dir = TRANS_CACHE_DIR
        self.tts_cache_days = TTS_CACHE_DAYS
        self.trans_cache_days = TRANSLATION_CACHE_DAYS
        
        # 创建缓存目录
        self.tts_cache_dir.mkdir(parents=True, exist_ok=True)
        self.trans_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_old_cache(self):
        """清理过期缓存"""
        self._cleanup_dir(self.tts_cache_dir, self.tts_cache_days)
        self._cleanup_dir(self.trans_cache_dir, self.trans_cache_days)
    
    def _cleanup_dir(self, cache_dir, days):
        """清理指定目录的过期文件"""
        if not cache_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for file_path in cache_dir.glob('*'):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f'删除缓存文件失败: {str(e)}')
    
    def get_translation(self, cache_key):
        """获取翻译缓存"""
        cache_file = self.trans_cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('translation')
            except:
                return None
        
        return None
    
    def save_translation(self, cache_key, translation):
        """保存翻译缓存"""
        cache_file = self.trans_cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'translation': translation,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False)
        except Exception as e:
            print(f'保存翻译缓存失败: {str(e)}')