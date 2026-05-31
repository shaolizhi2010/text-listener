import requests
from config import TRANSLATION_API, TRANSLATION_MODEL

class TranslationService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_base = TRANSLATION_API
        self.model = TRANSLATION_MODEL
    
    def translate(self, text, source_lang='auto', target_lang='zh'):
        """翻译文本"""
        if not self.api_key:
            return {
                'status': 'error',
                'error': 'no_api_key',
                'message': '未配置API密钥'
            }
        
        try:
            # 调用硅基流动翻译API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 构建翻译提示词
            if source_lang == 'auto':
                prompt = f"Please translate the following text to {target_lang}: {text}"
            else:
                prompt = f"Please translate the following {source_lang} text to {target_lang}: {text}"
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 500
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 429:
                return {
                    'status': 'error',
                    'error': 'rate_limit',
                    'message': '触发限流'
                }
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'error': 'api_error',
                    'message': f'API错误: {response.status_code}'
                }
            
            result = response.json()
            translation = result['choices'][0]['message']['content'].strip()
            
            # 检查翻译结果
            if not translation or len(translation) < 3:
                return {
                    'status': 'error',
                    'error': 'invalid_result',
                    'message': '翻译结果无效'
                }
            
            return {
                'status': 'success',
                'translation': translation
            }
        
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error': 'timeout',
                'message': '请求超时'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': 'exception',
                'message': str(e)
            }