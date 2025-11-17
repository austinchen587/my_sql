# tool/views/views_MP/views_MP_sql/result_analyzer.py
import logging
from decimal import Decimal
import datetime
import json

logger = logging.getLogger(__name__)

class ResultAnalyzer:
    """结果分析模块 - 增强版，支持标签数据分析"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    def analyze_query_results_with_ai(self, user_message, query_result, sql_query):
        """使用AI分析查询结果 - 增强标签分析"""
        try:
            if not self.ai_processor.ai_client:
                return self.generate_enhanced_analysis(query_result, user_message)
            
            formatted_results = self.format_results_for_analysis(query_result)
            tag_analysis = self.prepare_tag_analysis_context(query_result)
            
            prompt = f"""
# 分析任务：
请根据以下信息分析查询结果并回答用户的问题。

# 用户原始问题：
{user_message}

# 执行的SQL查询：
{sql_query}

# 查询结果概览：
- 总记录数: {len(query_result)} 条
- 包含标签信息: {'是' if self.has_tag_data(query_result) else '否'}
{tag_analysis}

# 详细查询结果（共{len(query_result)}条记录）：
{formatted_results}

# 分析要求：
1. **数据概况**: 总结查询结果的主要发现和统计信息
2. **标签分析**: 分析标签分布情况（如有一级、二级标签）
3. **趋势模式**: 分析金额、时间、地域等维度的趋势
4. **业务洞察**: 提供有价值的业务洞察和建议
5. **数据质量**: 评估数据完整性和质量
6. 用中文回复，专业且易懂
7. 如果无数据，说明原因并建议优化查询

# 请直接回复分析结果：
"""
            
            try:
                response = self.ai_processor.ai_client.chat.completions.create(
                    model=self.ai_processor.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.3,
                    timeout=60
                )
                
                return response.choices[0].message.content
                
            except Exception as ai_error:
                logger.warning(f"⚠️ AI分析超时或失败，使用增强分析: {ai_error}")
                return self.generate_enhanced_analysis(query_result, user_message)
                
        except Exception as e:
            logger.error(f"❌ AI分析结果失败: {e}")
            return self.generate_enhanced_analysis(query_result, user_message)

    def prepare_tag_analysis_context(self, query_result):
        """准备标签分析上下文"""
        if not query_result:
            return ""
        
        tag_stats = self.calculate_tag_statistics(query_result)
        
        analysis_context = "\n# 标签统计分析:\n"
        
        # 一级标签分析
        if tag_stats['primary_tags']:
            analysis_context += "## 一级标签分布:\n"
            for tag, count in tag_stats['primary_tags'].items():
                percentage = (count / len(query_result)) * 100
                analysis_context += f"- {tag}: {count}条 ({percentage:.1f}%)\n"
        
        # 二级标签分析
        if tag_stats['secondary_tags']:
            analysis_context += "\n## 二级标签分布:\n"
            for tag, count in tag_stats['secondary_tags'].items():
                percentage = (count / len(query_result)) * 100
                analysis_context += f"- {tag}: {count}条 ({percentage:.1f}%)\n"
        
        # 金额分析
        if tag_stats['amount_stats']:
            analysis_context += f"\n## 金额统计:\n"
            analysis_context += f"- 总金额: {tag_stats['amount_stats']['total']:,.2f}元\n"
            analysis_context += f"- 平均金额: {tag_stats['amount_stats']['avg']:,.2f}元\n"
            analysis_context += f"- 最高金额: {tag_stats['amount_stats']['max']:,.2f}元\n"
            analysis_context += f"- 最低金额: {tag_stats['amount_stats']['min']:,.2f}元\n"
        
        return analysis_context

    def calculate_tag_statistics(self, query_result):
        """计算标签统计信息"""
        stats = {
            'primary_tags': {},
            'secondary_tags': {},
            'amount_stats': None
        }
        
        if not query_result:
            return stats
        
        # 统计标签
        amounts = []
        for record in query_result:
            # 一级标签统计
            primary_tag = record.get('primary_tag')
            if primary_tag:
                stats['primary_tags'][primary_tag] = stats['primary_tags'].get(primary_tag, 0) + 1
            
            # 二级标签统计
            secondary_tag = record.get('secondary_tag')
            if secondary_tag:
                stats['secondary_tags'][secondary_tag] = stats['secondary_tags'].get(secondary_tag, 0) + 1
            
            # 金额统计
            amount = record.get('budget_amount') or record.get('intention_budget_amount')
            if amount and isinstance(amount, (int, float, Decimal)):
                amounts.append(float(amount))
        
        # 金额统计
        if amounts:
            stats['amount_stats'] = {
                'total': sum(amounts),
                'avg': sum(amounts) / len(amounts),
                'max': max(amounts),
                'min': min(amounts),
                'count': len(amounts)
            }
        
        return stats

    def has_tag_data(self, query_result):
        """检查是否包含标签数据"""
        if not query_result:
            return False
        
        sample_record = query_result[0]
        tag_fields = ['primary_tag', 'secondary_tag', 'tertiary_tags']
        return any(field in sample_record for field in tag_fields)

    def format_results_for_analysis(self, query_result, max_records=30):
        """格式化查询结果用于AI分析 - 优化显示"""
        if not query_result:
            return "无查询结果"
        
        # 显示关键字段，避免信息过载
        display_results = query_result[:max_records]
        
        result_text = f"共找到 {len(query_result)} 条记录\n\n"
        
        for i, record in enumerate(display_results, 1):
            result_text += f"记录{i}:\n"
            
            # 优先显示关键字段
            key_fields = self.get_key_fields_for_display(record)
            
            for key in key_fields:
                if key in record:
                    value = record[key]
                    # 处理特殊数据类型
                    value = self.format_value_for_display(value)
                    result_text += f"  {key}: {value}\n"
            
            result_text += "\n"
        
        if len(query_result) > len(display_results):
            remaining = len(query_result) - len(display_results)
            result_text += f"... 还有 {remaining} 条记录未显示\n"
        
        return result_text

    def get_key_fields_for_display(self, record):
        """获取需要显示的关键字段"""
        base_fields = ['primary_tag', 'secondary_tag', 'budget_amount', 'intention_budget_amount']
        
        # 根据记录类型添加特定字段
        if 'notice_title' in record:
            # 采购公告字段
            base_fields = ['notice_title', 'project_name', 'purchaser_name', 'province', 'city', 'publish_date'] + base_fields
        elif 'intention_project_name' in record:
            # 采购意向字段
            base_fields = ['title', 'intention_project_name', 'intention_procurement_unit', 'jurisdiction', 'publish_time'] + base_fields
        
        return base_fields

    def format_value_for_display(self, value):
        """格式化值用于显示"""
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        elif isinstance(value, datetime.date):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return f"{float(value):,.2f}"
        elif isinstance(value, (int, float)):
            if value > 1000:  # 金额格式化
                return f"{value:,.2f}"
            return str(value)
        elif value is None:
            return "NULL"
        elif isinstance(value, str) and len(value) > 100:
            return value[:100] + "..."
        else:
            return str(value)

    def generate_enhanced_analysis(self, query_result, user_message=""):
        """生成增强的基础分析"""
        if not query_result:
            return "❌ 未找到相关数据。请检查查询条件或尝试其他关键词。"
        
        stats = self.calculate_tag_statistics(query_result)
        analysis = f"## 查询结果概览\n\n"
        analysis += f"- **总记录数**: {len(query_result)} 条\n"
        
        # 标签分析
        if stats['primary_tags']:
            analysis += f"- **一级标签分布**: {', '.join([f'{k}({v})' for k, v in stats['primary_tags'].items()])}\n"
        
        if stats['secondary_tags']:
            analysis += f"- **二级标签分布**: {', '.join([f'{k}({v})' for k, v in list(stats['secondary_tags'].items())[:5]])}\n"
        
        # 金额分析
        if stats['amount_stats']:
            amt = stats['amount_stats']
            analysis += f"- **金额统计**: 总额{amt['total']:,.0f}元, 平均{amt['avg']:,.0f}元, 最高{amt['max']:,.0f}元\n"
        
        analysis += f"\n## 建议\n"
        analysis += "建议使用标签筛选功能进一步细化查询结果，或按金额、时间等维度进行深入分析。"
        
        return analysis

    def generate_basic_analysis(self, query_result):
        """兼容旧版本的基础分析"""
        return self.generate_enhanced_analysis(query_result)
