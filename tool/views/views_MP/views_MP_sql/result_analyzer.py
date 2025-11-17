# tool/views/views_MP/views_MP_sql/result_analyzer.py
import logging
from decimal import Decimal
import datetime

logger = logging.getLogger(__name__)

class ResultAnalyzer:
    """结果分析模块"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    def analyze_query_results_with_ai(self, user_message, query_result, sql_query):
        """使用AI分析查询结果 - 增加超时处理"""
        try:
            if not self.ai_processor.ai_client:
                return self.generate_basic_analysis(query_result)
            
            formatted_results = self.format_results_for_analysis(query_result)
            
            prompt = f"""
    # 分析任务：
    请根据以下信息分析查询结果并回答用户的问题。
    # 用户原始问题：
    {user_message}
    # 执行的SQL查询：
    {sql_query}
    # 查询结果（共{len(query_result)}条记录）：
    {formatted_results}
    # 分析要求：
    1. 总结查询结果的主要发现
    2. 分析数据趋势和模式（如有）
    3. 用中文回复，专业且易懂
    4. 如果无数据，说明原因并建议
    请直接回复分析结果：
    """
            
            try:
                response = self.ai_processor.ai_client.chat.completions.create(
                    model=self.ai_processor.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3,
                    timeout=60  # 增加超时时间到60秒
                )
                
                return response.choices[0].message.content
                
            except Exception as ai_error:
                logger.warning(f"⚠️ AI分析超时或失败，使用基础分析: {ai_error}")
                return self.generate_basic_analysis(query_result)
                
        except Exception as e:
            logger.error(f"❌ AI分析结果失败: {e}")
            return self.generate_basic_analysis(query_result)

    def format_results_for_analysis(self, query_result, max_records=50):
        """格式化查询结果用于AI分析"""
        if not query_result:
            return "无查询结果"
        
        # 显示所有记录，或者设置一个较大的上限
        display_results = query_result[:max_records]
        
        result_text = f"共找到 {len(query_result)} 条记录\n\n"
        
        for i, record in enumerate(display_results, 1):
            result_text += f"记录{i}:\n"
            for key, value in record.items():
                # 处理特殊数据类型
                if isinstance(value, datetime.datetime):
                    value = value.isoformat()
                elif isinstance(value, datetime.date):
                    value = value.isoformat()
                elif isinstance(value, Decimal):
                    value = float(value)
                elif value is None:
                    value = "NULL"
                
                # 完整显示所有内容，不进行截断
                result_text += f"  {key}: {value}\n"
            result_text += "\n"
        
        # 如果记录总数超过显示数量，提示还有多少条未显示
        if len(query_result) > len(display_results):
            remaining = len(query_result) - len(display_results)
            result_text += f"... 还有 {remaining} 条记录未显示\n"
        
        return result_text

    def generate_basic_analysis(self, query_result):
        """生成基础分析"""
        if not query_result:
            return "未找到相关数据。"
        
        return f"找到 {len(query_result)} 条相关记录。建议使用更具体的查询条件来缩小范围。"
