# tool/views/views_MP/views_MP_sql/response_formatter.py
import logging
import re
import json

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """响应格式化模块"""
    
    def format_final_response(self, user_message, sql_generation, query_result, analysis_result):
        """格式化最终响应 - 美化显示格式"""
        preview_table = self.generate_preview_table(query_result)
        
        # 美化分析结果显示
        formatted_analysis = self.beautify_analysis_output(analysis_result)
        
        response_data = {
            'status': 'success',
            'response_type': 'intelligent_sql_analysis',
            'message': f"""
    <div class="intelligent-analysis-result">
        <div class="analysis-header bg-primary text-white p-3 rounded-top">
            <div class="d-flex align-items-center">
                <i class="bi bi-robot fs-4 me-2"></i>
                <h4 class="mb-0">🤖 智能分析结果</h4>
            </div>
            <small>基于您的查询条件，已找到 {len(query_result)} 条相关记录</small>
        </div>
        
        <div class="analysis-body p-4">
            {formatted_analysis}
        </div>
        
        <div class="analysis-technical bg-light p-3 border-top">
            <div class="sql-info mb-3">
                <h5 class="d-flex align-items-center">
                    <i class="bi bi-database me-2"></i>执行的SQL查询
                </h5>
                <div class="sql-code-container">
                    <button class="btn btn-sm btn-outline-secondary mb-2 copy-sql-btn" 
                            onclick="copyToClipboard(this)">
                        <i class="bi bi-clipboard"></i> 复制SQL
                    </button>
                    <pre class="bg-light p-3 border rounded"><code>{sql_generation['sql_query']}</code></pre>
                </div>
            </div>
            
            <div class="data-preview">
                <h5 class="d-flex align-items-center">
                    <i class="bi bi-table me-2"></i>数据预览（共 {len(query_result)} 条记录）
                </h5>
                {preview_table}
            </div>
        </div>
    </div>
            """,
            'data_count': len(query_result),
            'sql_query': sql_generation['sql_query'],
            'tables_used': sql_generation['tables_used']
        }
        
        return response_data

    def beautify_analysis_output(self, analysis_text):
        """美化AI分析结果的显示"""
        if not analysis_text:
            return '<div class="alert alert-warning">暂无分析结果</div>'
        
        # 处理Markdown格式为HTML
        formatted_html = self.markdown_to_html(analysis_text)
        
        return f"""
        <div class="analysis-content">
            <div class="analysis-text">
                {formatted_html}
            </div>
        </div>
        """

    def markdown_to_html(self, markdown_text):
        """将Markdown格式转换为美化HTML"""
        # 替换标题
        markdown_text = re.sub(r'### (.*?)(?=\n|$)', r'<h5 class="text-primary mt-4">\1</h5>', markdown_text)
        markdown_text = re.sub(r'## (.*?)(?=\n|$)', r'<h4 class="text-primary mt-4 border-bottom pb-2">\1</h4>', markdown_text)
        markdown_text = re.sub(r'# (.*?)(?=\n|$)', r'<h3 class="text-primary mt-4 border-bottom pb-2">\1</h3>', markdown_text)
        
        # 替换列表项
        markdown_text = re.sub(r'\* (.*?)(?=\n|$)', r'<li class="mb-1">\1</li>', markdown_text)
        markdown_text = re.sub(r'(<li.*?</li>\s*)+', r'<ul class="list-unstyled ms-3">\g<0></ul>', markdown_text, flags=re.DOTALL)
        
        # 替换粗体
        markdown_text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="text-dark">\1</strong>', markdown_text)
        
        # 替换段落
        paragraphs = re.split(r'\n\s*\n', markdown_text)
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 如果已经是HTML标签，不处理
            if para.startswith('<') and para.endswith('>'):
                formatted_paragraphs.append(para)
            else:
                # 检查是否是列表
                if para.startswith('<ul>'):
                    formatted_paragraphs.append(para)
                else:
                    formatted_paragraphs.append(f'<p class="mb-3">{para}</p>')
        
        return '\n'.join(formatted_paragraphs)

    def generate_preview_table(self, query_result, max_display=None):
        """生成数据预览表格 - 显示完整内容，不加省略号"""
        if not query_result:
            return "<p>无数据</p>"
        
        display_data = query_result  # 显示所有数据
        
        if not display_data:
            return "<p>无数据</p>"
        
        # 获取列名
        columns = list(display_data[0].keys())
        
        table_html = f'<div class="table-responsive" style="max-height: 600px; overflow-y: auto;"><table class="table table-sm table-bordered table-striped">'
        table_html += '<thead><tr class="table-primary">'
        for col in columns:
            table_html += f'<th class="text-nowrap">{col}</th>'
        table_html += '</tr></thead><tbody>'
        
        for row in display_data:
            table_html += '<tr>'
            for col in columns:
                value = row.get(col, '')
                # 处理特殊数据类型
                if isinstance(value, (dict, list)):
                    try:
                        value = f'<pre style="margin:0; white-space:pre-wrap;">{json.dumps(value, ensure_ascii=False, indent=2)}</pre>'
                    except:
                        value = f'<pre style="margin:0; white-space:pre-wrap;">{str(value)}</pre>'
                elif value is None:
                    value = '<span class="text-muted"><em>NULL</em></span>'
                elif isinstance(value, str) and value.strip().startswith(('{', '[')):
                    value = f'<pre style="margin:0; white-space:pre-wrap;">{value}</pre>'
                else:
                    # 普通文本，确保换行符等正确显示
                    value = f'<div style="white-space: pre-wrap;">{value}</div>'
                
                table_html += f'<td style="max-width: 400px; overflow: auto;">{value}</td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        table_html += f'<div class="text-end mt-2"><small class="text-muted badge bg-secondary">共 {len(query_result)} 条记录</small></div>'
        table_html += '</div>'
        
        return table_html
