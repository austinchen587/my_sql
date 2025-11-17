# tool/views/markdown_formatter.py
import re
from typing import Dict, Any

class MarkdownFormatter:
    """
    纯Markdown格式美化处理器
    功能：
    1. 自动识别并优化表格
    2. 规范化列表格式
    3. 保证代码块封装
    4. 添加适当的换行和标题层级
    """

    @classmethod
    def beautify(cls, content: str) -> str:
        """主美化入口"""
        if not content:
            return content
            
        processors = [
            cls._process_tables,     
            cls._process_lists,
            cls._process_code_blocks,
            cls._process_headings,
            cls._add_line_breaks
        ]
        
        for processor in processors:
            content = processor(content)
            
        return content.strip()
    
    @staticmethod
    def _process_tables(text: str) -> str:
        """优化Markdown表格格式"""
        def _format_table(match):
            table = match.group(0)
            # 确保表头分隔线
            lines = table.split('\n')
            if len(lines) >= 2 and not any(re.match(r'^\|?\s*:?-+:?\s*\|', line) for line in lines):
                sep_line = '|' + '|'.join(['---'] * lines[0].count('|')) + '|'
                lines.insert(1, sep_line)
            return '\n'.join(lines)
            
        return re.sub(r'(\n\|.+\|\n)(?:(?:\|.+\|(?:\n|$))+)', _format_table, text)

    @staticmethod
    def _process_lists(text: str) -> str:
        """统一列表格式为GitHub风格"""
        # 统一无序列表符号为-
        text = re.sub(r'^(\s*)[\*\+](\s+)', r'\1-\2', text, flags=re.MULTILINE)
        
        # 修复多级列表缩进
        return re.sub(r'^(\s*-\s+)', r'\g<1>', text, flags=re.MULTILINE)

    @staticmethod
    def _process_code_blocks(text: str) -> str:
        """确保代码块有封装"""
        if '```' not in text and ('\n    ' in text or '\n\t' in text):
            return f'```\n{text}\n```'
        return text

    @staticmethod
    def _process_headings(text: str) -> str:
        """优化标题层级"""
        return re.sub(r'^(#+)([^#\n]+)$', r'\1 \2', text, flags=re.MULTILINE)

    @staticmethod
    def _add_line_breaks(text: str) -> str:
        """在段落间添加适当换行"""
        return re.sub(r'(\n[^\n])(?=\n[^#\s\-*])', r'\1\n', text)
