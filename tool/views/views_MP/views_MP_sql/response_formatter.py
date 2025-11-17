# tool/views/views_MP/views_MP_sql/response_formatter.py
import logging
import re
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """响应格式化模块 - 增强版，支持标签数据展示"""
    
    def format_final_response(self, user_message, sql_generation, query_result, analysis_result):
        """格式化最终响应 - 增强标签信息展示"""
        preview_table = self.generate_preview_table(query_result)
        tag_summary = self.generate_tag_summary(query_result)
        
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
        
        <!-- 标签概览 -->
        {tag_summary}
        
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

    def generate_tag_summary(self, query_result):
        """生成标签概览信息"""
        if not query_result or len(query_result) == 0:
            return ""
        
        # 提取标签统计
        primary_tags = {}
        secondary_tags = {}
        total_amount = 0
        amount_count = 0
        
        for record in query_result:
            # 一级标签统计
            primary_tag = record.get('primary_tag')
            if primary_tag:
                primary_tags[primary_tag] = primary_tags.get(primary_tag, 0) + 1
            
            # 二级标签统计
            secondary_tag = record.get('secondary_tag')
            if secondary_tag:
                secondary_tags[secondary_tag] = secondary_tags.get(secondary_tag, 0) + 1
            
            # 金额统计
            amount = record.get('budget_amount') or record.get('intention_budget_amount')
            if amount and isinstance(amount, (int, float, Decimal)):
                total_amount += float(amount)
                amount_count += 1
        
        # 构建标签概览HTML
        tag_html = '<div class="tag-summary bg-info bg-opacity-10 p-3 border-bottom">\n'
        tag_html += '<h6 class="mb-2"><i class="bi bi-tags me-1"></i>标签概览</h6>\n'
        tag_html += '<div class="row">\n'
        
        # 一级标签
        if primary_tags:
            tag_html += '<div class="col-md-6">\n'
            tag_html += '<strong>一级标签:</strong><br>\n'
            for tag, count in list(primary_tags.items())[:5]:  # 最多显示5个
                percentage = (count / len(query_result)) * 100
                tag_html += f'<span class="badge bg-primary me-1 mb-1">{tag} ({count}, {percentage:.1f}%)</span>\n'
            tag_html += '</div>\n'
        
        # 二级标签
        if secondary_tags:
            tag_html += '<div class="col-md-6">\n'
            tag_html += '<strong>二级标签:</strong><br>\n'
            for tag, count in list(secondary_tags.items())[:5]:  # 最多显示5个
                percentage = (count / len(query_result)) * 100
                tag_html += f'<span class="badge bg-secondary me-1 mb-1">{tag} ({count}, {percentage:.1f}%)</span>\n'
            tag_html += '</div>\n'
        
        tag_html += '</div>\n'
        
        # 金额统计
        if amount_count > 0:
            avg_amount = total_amount / amount_count if amount_count > 0 else 0
            tag_html += f'<div class="mt-2"><strong>金额统计:</strong> 总金额 {total_amount:,.0f}元，平均 {avg_amount:,.0f}元 ({amount_count}条记录有金额信息)</div>\n'
        
        tag_html += '</div>\n'
        
        return tag_html

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
        
        # 替换表格（简单支持）
        markdown_text = self.convert_markdown_tables(markdown_text)
        
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
                # 检查是否是列表或表格
                if para.startswith(('<ul>', '<table>')):
                    formatted_paragraphs.append(para)
                else:
                    formatted_paragraphs.append(f'<p class="mb-3">{para}</p>')
        
        return '\n'.join(formatted_paragraphs)

    def convert_markdown_tables(self, text):
        """转换Markdown表格为HTML表格"""
        lines = text.split('\n')
        in_table = False
        table_lines = []
        result_lines = []
        
        for line in lines:
            if '|' in line and ('---' in line or '--' in line):
                # 表格分隔行
                in_table = True
                continue
            elif '|' in line and in_table:
                table_lines.append(line)
            else:
                if in_table and table_lines:
                    # 处理积累的表格行
                    result_lines.append(self.build_html_table(table_lines))
                    table_lines = []
                    in_table = False
                result_lines.append(line)
        
        if in_table and table_lines:
            result_lines.append(self.build_html_table(table_lines))
        
        return '\n'.join(result_lines)

    def build_html_table(self, table_lines):
        """构建HTML表格"""
        if not table_lines:
            return ""
        
        html = '<div class="table-responsive mt-3"><table class="table table-sm table-bordered">\n'
        
        # 表头
        headers = [h.strip() for h in table_lines[0].split('|') if h.strip()]
        html += '<thead class="table-light"><tr>\n'
        for header in headers:
            html += f'<th>{header}</th>\n'
        html += '</tr></thead>\n'
        
        # 表体
        html += '<tbody>\n'
        for line in table_lines[1:]:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) == len(headers):
                html += '<tr>\n'
                for cell in cells:
                    html += f'<td>{cell}</td>\n'
                html += '</tr>\n'
        html += '</tbody>\n'
        html += '</table></div>\n'
        
        return html

    def generate_preview_table(self, query_result, max_display=50):
        """生成数据预览表格 - 优化标签显示"""
        if not query_result:
            return "<p>无数据</p>"
        
        display_data = query_result[:max_display]
        
        if not display_data:
            return "<p>无数据</p>"
        
        # 智能选择显示的列（优先显示标签和关键字段）
        columns = self.select_display_columns(display_data[0])
        
        table_html = f'<div class="table-responsive" style="max-height: 600px; overflow-y: auto;"><table class="table table-sm table-bordered table-striped">'
        table_html += '<thead><tr class="table-primary">'
        for col in columns:
            table_html += f'<th class="text-nowrap">{col}</th>'
        table_html += '</tr></thead><tbody>'
        
        for row in display_data:
            table_html += '<tr>'
            for col in columns:
                value = row.get(col, '')
                value = self.format_table_value(value, col)
                table_html += f'<td style="max-width: 300px; overflow: auto;">{value}</td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        table_html += f'<div class="text-end mt-2"><small class="text-muted badge bg-secondary">共 {len(query_result)} 条记录，显示前 {len(display_data)} 条</small></div>'
        table_html += '</div>'
        
        return table_html

    def select_display_columns(self, sample_record):
        """智能选择要显示的列"""
        # 优先级字段（标签和关键信息）
        priority_fields = [
            'primary_tag', 'secondary_tag', 'budget_amount', 'intention_budget_amount',
            'notice_title', 'project_name', 'title', 'intention_project_name',
            'purchaser_name', 'intention_procurement_unit', 'province', 'city'
        ]
        
        all_fields = list(sample_record.keys())
        
        # 优先显示标签相关字段
        display_fields = []
        for field in priority_fields:
            if field in all_fields:
                display_fields.append(field)
                all_fields.remove(field)
        
        # 添加其他字段（最多总共15列）
        remaining_slots = 15 - len(display_fields)
        if remaining_slots > 0:
            display_fields.extend(all_fields[:remaining_slots])
        
        return display_fields

    def format_table_value(self, value, column_name):
        """格式化表格中的值"""
        if value is None:
            return '<span class="text-muted"><em>NULL</em></span>'
        
        # 金额字段格式化
        if 'amount' in column_name.lower() and isinstance(value, (int, float, Decimal)):
            return f'<span class="text-end">{float(value):,.2f}</span>'
        
        # 标签字段特殊样式
        if 'tag' in column_name.lower():
            if value:
                badge_class = 'bg-primary' if 'primary' in column_name else 'bg-secondary'
                return f'<span class="badge {badge_class}">{value}</span>'
        
        # JSON字段处理
        if isinstance(value, (dict, list)):
            try:
                json_str = json.dumps(value, ensure_ascii=False, indent=2)
                return f'<pre style="margin:0; white-space:pre-wrap; font-size:0.8em;">{json_str}</pre>'
            except:
                return f'<pre style="margin:0; white-space:pre-wrap;">{str(value)}</pre>'
        
        # 长文本截断
        if isinstance(value, str) and len(value) > 100:
            return f'<span title="{value}">{value[:100]}...</span>'
        
        # 普通文本
        return f'<div style="white-space: pre-wrap;">{value}</div>'
