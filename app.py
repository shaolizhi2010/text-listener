import os
import sys
import json
import argparse
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
from pathlib import Path

from utils.file_handler import FileHandler
from utils.text_processor import TextProcessor
from utils.tts_handler import TTSHandler
from utils.translation import TranslationService
from utils.dict_handler import DictHandler
from utils.cache_manager import CacheManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB限制

# 全局变量
api_key = None
file_handler = None
text_processor = None
tts_handler = None
translation_service = None
dict_handler = None
cache_manager = None

@app.before_request
def init_services():
    global file_handler, text_processor, tts_handler, translation_service, dict_handler, cache_manager
    if file_handler is None:
        file_handler = FileHandler()
        text_processor = TextProcessor()
        tts_handler = TTSHandler()
        translation_service = TranslationService(api_key)
        dict_handler = DictHandler()
        cache_manager = CacheManager()
        cache_manager.cleanup_old_cache()

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 文件上传接口
@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        # 获取上传的文件或文本
        file = request.files.get('file')
        text = request.form.get('text', '')
        target_lang = request.form.get('target_lang', 'none')
        
        if not file and not text:
            return jsonify({'status': 'error', 'message': '请提供文件或文本'}), 400
        
        # 处理文件
        if file:
            result = file_handler.handle_upload(file, target_lang)
            if result['status'] != 'success':
                return jsonify(result), 400
        else:
            result = file_handler.handle_text_input(text, target_lang)
            if result['status'] != 'success':
                return jsonify(result), 400
        
        file_id = result['file_id']
        
        # 处理文件：解析为纯文本、分句、分片
        text_content = result['text']
        file_info = file_handler.create_file_structure(file_id, text_content, target_lang)
        
        return jsonify({
            'status': 'success',
            'file_id': file_id,
            'file_name': file_info['file_name'],
            'message': '文件上传成功，正在处理...'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取文件列表接口
@app.route('/api/files', methods=['GET'])
def get_files():
    try:
        files = file_handler.get_file_list()
        return jsonify({'status': 'success', 'files': files}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取文件片段列表（目录页）
@app.route('/api/files/<file_id>/segments', methods=['GET'])
def get_segments(file_id):
    try:
        page = request.args.get('page', 1, type=int)
        segments = file_handler.get_file_segments(file_id, page)
        return jsonify({'status': 'success', **segments}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 打开列表页
@app.route('/list/<file_id>')
def list_page(file_id):
    return render_template('list.html', file_id=file_id)

# 获取文件片段内容（阅读页）
@app.route('/api/files/<file_id>/segments/<segment_id>', methods=['GET'])
def get_segment_content(file_id, segment_id):
    try:
        content = file_handler.get_segment_content(file_id, segment_id)
        return jsonify({'status': 'success', 'content': content}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 打开阅读页
@app.route('/reader/<file_id>/<segment_id>')
def reader_page(file_id, segment_id):
    return render_template('reader.html', file_id=file_id, segment_id=segment_id)

# TTS接口 - 获取音频
@app.route('/api/tts', methods=['POST'])
def get_tts():
    try:
        data = request.json
        text = data.get('text', '')
        lang = data.get('lang', 'en')
        file_id = data.get('file_id', '')
        
        # 获取音频
        audio_data = tts_handler.synthesize(text, lang, file_id)
        
        return send_file(
            audio_data,
            mimetype='audio/mpeg',
            as_attachment=False
        ), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 翻译接口
@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'zh')
        file_id = data.get('file_id', '')
        
        # 检查缓存
        cache_key = f"{file_id}_{source_lang}_{target_lang}_{text}"
        cached = cache_manager.get_translation(cache_key)
        if cached:
            return jsonify({'status': 'success', 'translation': cached}), 200
        
        # 调用翻译服务
        result = translation_service.translate(text, source_lang, target_lang)
        
        if result['status'] == 'error':
            if 'rate_limit' in result.get('error', ''):
                return jsonify({
                    'status': 'error',
                    'error': 'rate_limit',
                    'message': '翻译系统繁忙，请稍后再试'
                }), 429
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'translation_error',
                    'message': '翻译出错，请稍后再试'
                }), 500
        
        translation_text = result['translation']
        
        # 缓存翻译结果
        cache_manager.save_translation(cache_key, translation_text)
        
        return jsonify({'status': 'success', 'translation': translation_text}), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': 'system_error',
            'message': str(e)
        }), 500

# 单词查询接口
@app.route('/api/word/<word>', methods=['GET'])
def query_word(word):
    try:
        meaning = dict_handler.query_word(word)
        if meaning:
            return jsonify({'status': 'success', 'word': word, 'meaning': meaning}), 200
        else:
            return jsonify({'status': 'not_found', 'word': word}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 删除文件接口
@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        file_handler.delete_file(file_id)
        return jsonify({'status': 'success', 'message': '文件已删除'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'status': 'error', 'message': '文件超过10MB限制'}), 413

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text Listener Server')
    parser.add_argument('--api_key', type=str, help='Silicon Flow API Key')
    args = parser.parse_args()
    
    api_key = args.api_key
    
    app.run(host='0.0.0.0', port=80, debug=False)