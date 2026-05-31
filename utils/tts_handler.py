import os
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import edge_tts

from config import TTS_CACHE_DIR, TTS_DEFAULT_VOICE, TTS_CACHE_DAYS

class TTSHandler:
    def __init__(self):
        self.cache_dir = TTS_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def synthesize(self, text, lang='en', file_id=''):
        """合成语音"""
        # 生成缓存键
        cache_key = self._get_cache_key(text, lang, file_id)
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        
        # 检查缓存
        if cache_path.exists():
            # 检查缓存是否过期
            if not self._is_cache_expired(cache_path):
                return open(cache_path, 'rb')
        
        # 合成语音
        try:
            audio_data = asyncio.run(self._synthesize_audio(text, lang))
            
            # 保存到缓存
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            
            return open(cache_path, 'rb')
        
        except Exception as e:
            raise Exception(f'语音合成失败: {str(e)}')
    
    async def _synthesize_audio(self, text, lang='en'):
        """使用Edge TTS合成音频"""
        # 选择语音
        if lang == 'zh':
            voice = 'zh-CN-XiaoxiaoNeural'
        elif lang == 'en':
            voice = 'en-US-AriaNeural'
        elif lang == 'ja':
            voice = 'ja-JP-NanamisNeural'
        else:
            voice = 'en-US-AriaNeural'
        
        # 生成语音
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b''
        
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                audio_data += chunk['data']
        
        return audio_data
    
    def _get_cache_key(self, text, lang, file_id):
        """生成缓存键"""
        cache_str = f"{text}_{lang}_{file_id}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _is_cache_expired(self, cache_path):
        """检查缓存是否过期"""
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_mtime > timedelta(days=TTS_CACHE_DAYS):
            return True
        return False