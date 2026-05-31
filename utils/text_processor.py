import re
try:
    import langdetect
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
except ImportError:
    detect = None

class TextProcessor:
    def __init__(self):
        self.sentence_patterns = {
            'zh': r'[。！？\n]',
            'en': r'[.!?]\s+',
            'mixed': r'[。！？.!?]\s*'
        }
    
    def detect_language(self, text):
        """检测文本语言"""
        if detect is None:
            # 如果langdetect未安装，用简单方式检测
            if re.search(r'[\u4e00-\u9fff]', text):
                return 'zh'
            else:
                return 'en'
        
        try:
            lang = detect(text[:500])
            if lang == 'zh-cn':
                return 'zh'
            elif lang == 'zh-tw':
                return 'zh'
            elif lang.startswith('en'):
                return 'en'
            else:
                return lang
        except:
            return 'en'
    
    def segment_sentences(self, text):
        """分句"""
        # 清理文本
        text = self._clean_text(text)
        
        # 检测语言
        lang = self.detect_language(text)
        
        # 根据语言分句
        if lang == 'zh':
            sentences = self._segment_chinese(text)
        elif lang == 'en':
            sentences = self._segment_english(text)
        else:
            sentences = self._segment_mixed(text)
        
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _clean_text(self, text):
        """清理文本"""
        # 移除多余的空格和换行
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'  +', ' ', text)
        return text
    
    def _segment_chinese(self, text):
        """中文分句"""
        # 在标点符号后添加换行
        text = re.sub(r'([。！？；\n])', r'\1\n', text)
        sentences = text.split('\n')
        
        # 进一步分句
        result = []
        for sentence in sentences:
            # 如果句子过长，按逗号分句
            if len(sentence) > 100:
                parts = sentence.split('，')
                result.extend(parts)
            else:
                result.append(sentence)
        
        return result
    
    def _segment_english(self, text):
        """英文分句"""
        # 按句号、问号、感叹号分句
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 进一步分句
        result = []
        for sentence in sentences:
            # 如果句子过长，按逗号或分号分句
            if len(sentence) > 150:
                parts = re.split(r'[,;]', sentence)
                result.extend(parts)
            else:
                result.append(sentence)
        
        return result
    
    def _segment_mixed(self, text):
        """混合语言分句"""
        # 在各种标点符号后分句
        text = re.sub(r'([。！？；,;.!?\n])', r'\1\n', text)
        sentences = text.split('\n')
        
        return sentences
    
    def check_language_match(self, original_lang, target_lang):
        """检查原语言和目标语言是否相同"""
        if original_lang == 'zh' and target_lang == 'en':
            return False
        elif original_lang == 'en' and target_lang == 'zh':
            return False
        else:
            return True  # 相同或目标为'none'