import struct
import re
from pathlib import Path
from config import DICT_FILES

class DictHandler:
    def __init__(self):
        self.dict_files = DICT_FILES
        self.dict_data = {}
        self.load_dict()
    
    def load_dict(self):
        """加载词典"""
        try:
            if not all(f.exists() for f in self.dict_files.values()):
                self.dict_data = {}
                return
            
            # 这是一个简化的词典加载实现
            # 实际使用时需要按照stardict格式解析
            pass
        except Exception as e:
            print(f'词典加载失败: {str(e)}')
            self.dict_data = {}
    
    def query_word(self, word):
        """查询单词"""
        word_lower = word.lower().strip()
        
        # 先尝试直接查询
        if word_lower in self.dict_data:
            meanings = self.dict_data[word_lower]
            return self._format_meanings(meanings)
        
        # 尝试变体形式
        variants = self._get_word_variants(word_lower)
        for variant in variants:
            if variant in self.dict_data:
                meanings = self.dict_data[variant]
                return self._format_meanings(meanings)
        
        # 如果本地词典为空，可以使用在线API
        return self._query_online(word_lower)
    
    def _get_word_variants(self, word):
        """获取单词变体"""
        variants = [word]
        
        # 去除ing, ed, s, es等
        if word.endswith('ing'):
            variants.append(word[:-3])
        if word.endswith('ed'):
            variants.append(word[:-2])
        if word.endswith('s'):
            variants.append(word[:-1])
        if word.endswith('es'):
            variants.append(word[:-2])
        
        return variants
    
    def _format_meanings(self, meanings):
        """格式化单词意思（最多4个）"""
        if isinstance(meanings, list):
            return '; '.join(meanings[:4])
        else:
            # 从字符串中提取前4个意思
            parts = str(meanings).split('|')
            return '; '.join([p.strip() for p in parts[:4] if p.strip()])
    
    def _query_online(self, word):
        """从在线API查询单词"""
        try:
            import requests
            # 使用自由词典API
            response = requests.get(
                f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()[0]
                meanings = []
                for meaning in data.get('meanings', [])[:2]:  # 最多2个词性
                    for definition in meaning.get('definitions', [])[:2]:  # 每个词性最多2个定义
                        meanings.append(definition.get('definition', ''))
                return '; '.join(meanings[:4])
            
            return None
        except:
            return None