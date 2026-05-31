import os
import re
import uuid
import json
from pathlib import Path
from datetime import datetime
import PyPDF2
import ebooklib
from ebooklib import epub
from html.parser import HTMLParser
import hashlib

from config import (
    BASE_DIR, DATA_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE,
    LINES_PER_SEGMENT, CHARS_PER_SEGMENT, ITEMS_PER_PAGE
)
from .text_processor import TextProcessor

class FileHandler:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.text_processor = TextProcessor()
        self.file_list_path = self.data_dir / 'file_list.json'
        self.load_file_list()
    
    def load_file_list(self):
        """从本地浏览器存储加载文件列表"""
        if self.file_list_path.exists():
            with open(self.file_list_path, 'r', encoding='utf-8') as f:
                self.file_list = json.load(f)
        else:
            self.file_list = {}
    
    def save_file_list(self):
        """保存文件列表"""
        self.file_list_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_list_path, 'w', encoding='utf-8') as f:
            json.dump(self.file_list, f, ensure_ascii=False, indent=2)
    
    def handle_upload(self, file, target_lang):
        """处理文件上传"""
        if not file or file.filename == '':
            return {'status': 'error', 'message': '未选择文件'}
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return {'status': 'error', 'message': '文件超过10MB限制'}
        
        # 检查文件格式
        filename = file.filename
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if ext not in ALLOWED_EXTENSIONS:
            return {
                'status': 'error',
                'message': f'不支持的文件格式，支持: {", ".join(ALLOWED_EXTENSIONS)}'
            }
        
        # 读取文件内容
        try:
            if ext == 'txt':
                text = file.read().decode('utf-8', errors='ignore')
            elif ext == 'pdf':
                text = self._extract_pdf(file)
            elif ext == 'epub':
                text = self._extract_epub(file)
            elif ext in ['doc', 'docx']:
                text = self._extract_docx(file)
            else:
                return {'status': 'error', 'message': '文件解析失败'}
            
            if not text or len(text.strip()) == 0:
                return {'status': 'error', 'message': '文件为空或无法读取'}
            
            file_id = str(uuid.uuid4())
            
            return {
                'status': 'success',
                'file_id': file_id,
                'text': text,
                'original_filename': filename,
                'target_lang': target_lang
            }
        
        except Exception as e:
            return {'status': 'error', 'message': f'文件解析失败: {str(e)}'}
    
    def handle_text_input(self, text, target_lang):
        """处理直接输入的文本"""
        if not text or len(text.strip()) == 0:
            return {'status': 'error', 'message': '文本不能为空'}
        
        if len(text) > MAX_FILE_SIZE:
            return {'status': 'error', 'message': '文本超过10MB限制'}
        
        file_id = str(uuid.uuid4())
        
        return {
            'status': 'success',
            'file_id': file_id,
            'text': text,
            'original_filename': f'text_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'target_lang': target_lang
        }
    
    def _extract_pdf(self, file):
        """从PDF提取文本"""
        text = []
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        except Exception as e:
            raise Exception(f'PDF解析失败: {str(e)}')
        return '\n'.join(text)
    
    def _extract_epub(self, file):
        """从EPUB提取文本"""
        text = []
        try:
            book = epub.read_epub(file)
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    text.append(self._html_to_text(item.get_content()))
        except Exception as e:
            raise Exception(f'EPUB解析失败: {str(e)}')
        return '\n'.join(text)
    
    def _extract_docx(self, file):
        """从DOCX提取文本"""
        try:
            from docx import Document
            doc = Document(file)
            text = [para.text for para in doc.paragraphs]
            return '\n'.join(text)
        except Exception as e:
            raise Exception(f'DOCX解析失败: {str(e)}')
    
    def _html_to_text(self, html):
        """HTML转文本"""
        class HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
            
            def handle_data(self, data):
                self.text.append(data.strip())
        
        extractor = HTMLTextExtractor()
        extractor.feed(html.decode('utf-8', errors='ignore'))
        return ' '.join(extractor.text)
    
    def create_file_structure(self, file_id, text, target_lang):
        """创建文件结构：分句、分片、保存"""
        # 清理文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"file_{timestamp}"
        
        # 创建文件夹
        file_dir = self.data_dir / file_id
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # 分句
        sentences = self.text_processor.segment_sentences(text)
        
        # 分片并保存
        segments = []
        segment_index = 0
        line_count = 0
        current_lines = []
        
        for sentence in sentences:
            current_lines.append(sentence)
            line_count += 1
            
            if line_count >= LINES_PER_SEGMENT:
                segment_id = f"segment_{segment_index}"
                self._save_segment(file_dir, segment_id, current_lines)
                segments.append({
                    'id': segment_id,
                    'preview': self._get_segment_preview(current_lines),
                    'status': 'processed'
                })
                current_lines = []
                line_count = 0
                segment_index += 1
        
        # 保存最后一个片段
        if current_lines:
            segment_id = f"segment_{segment_index}"
            self._save_segment(file_dir, segment_id, current_lines)
            segments.append({
                'id': segment_id,
                'preview': self._get_segment_preview(current_lines),
                'status': 'processed'
            })
        
        # 保存文件信息
        file_info = {
            'file_id': file_id,
            'file_name': file_name,
            'target_lang': target_lang,
            'segments': segments,
            'total_segments': len(segments),
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        with open(file_dir / 'file_info.json', 'w', encoding='utf-8') as f:
            json.dump(file_info, f, ensure_ascii=False, indent=2)
        
        # 更新文件列表
        self.file_list[file_id] = {
            'file_id': file_id,
            'file_name': file_name,
            'target_lang': target_lang,
            'created_at': datetime.now().isoformat(),
            'status': 'completed',
            'total_segments': len(segments)
        }
        self.save_file_list()
        
        return file_info
    
    def _save_segment(self, file_dir, segment_id, lines):
        """保存单个文件片段"""
        segment_path = file_dir / f"{segment_id}.txt"
        with open(segment_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
    
    def _get_segment_preview(self, lines):
        """获取文件片段预览（前50个字符）"""
        text = ' '.join(lines)
        preview = text[:50]
        
        # 检测章节
        chapter_match = self._detect_chapter(text)
        if chapter_match:
            return chapter_match
        
        return preview
    
    def _detect_chapter(self, text):
        """检测章节标题"""
        # 支持中文、英文、数字等情况
        patterns = [
            r'^第[0-9零一二三四五六七八九十百千万]+章\s*(.*)$',
            r'^第[0-9]+章\s*(.*)$',
            r'^Chapter\s+[0-9IVXLC]+[\s:]*(.*)$',
            r'^Chapter\s+[0-9]+[\s:]*(.*)$',
            r'^第[0-9０-９]+节\s*(.*)$',
            r'^\[.+?\]\s*(.*)$',
        ]
        
        for line in text.split('\n')[:5]:
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    return line.strip()[:100]
        
        return None
    
    def get_file_list(self):
        """获取文件列表"""
        self.load_file_list()
        files = list(self.file_list.values())
        files.sort(key=lambda x: x['created_at'], reverse=True)
        return files
    
    def get_file_segments(self, file_id, page=1):
        """获取文件片段列表（带翻页）"""
        file_info_path = self.data_dir / file_id / 'file_info.json'
        
        if not file_info_path.exists():
            return {'segments': [], 'page': page, 'total_pages': 0, 'total_items': 0}
        
        with open(file_info_path, 'r', encoding='utf-8') as f:
            file_info = json.load(f)
        
        segments = file_info['segments']
        total = len(segments)
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        
        return {
            'segments': segments[start:end],
            'page': page,
            'total_pages': (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE,
            'total_items': total
        }
    
    def get_segment_content(self, file_id, segment_id):
        """获取文件片段内容"""
        segment_path = self.data_dir / file_id / f"{segment_id}.txt"
        
        if not segment_path.exists():
            return []
        
        with open(segment_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]
        
        return lines
    
    def delete_file(self, file_id):
        """删除文件"""
        file_dir = self.data_dir / file_id
        if file_dir.exists():
            import shutil
            shutil.rmtree(file_dir)
        
        if file_id in self.file_list:
            del self.file_list[file_id]
            self.save_file_list()