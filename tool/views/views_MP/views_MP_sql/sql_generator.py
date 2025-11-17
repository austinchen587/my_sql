# tool/views/views_MP/views_MP_sql/sql_generator.py
import logging
import re
import traceback

logger = logging.getLogger(__name__)

class SQLGenerator:
    """SQL生成模块 - 基于实际表结构，精准理解用户意图"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
        # 基于标签说明.xlsx建立关键词到标签的映射
        self.tag_keyword_mapping = {
            # 医疗卫生相关关键词映射
            '医疗': '医疗卫生', '医院': '医疗卫生', '卫生': '医疗卫生', '医药': '医疗卫生',
            '药品': '医疗卫生', '医疗器械': '医疗设备', '诊疗': '医疗设备', '手术': '医疗设备',
            '疾控': '公共卫生/设施', '防疫': '公共卫生/设施', '体检': '医院服务', '康复': '医院服务',
            '护理': '医院服务', '门诊': '医院服务', '住院': '医院服务', '急诊': '医院服务',
            '卫生院': '医疗卫生', '疾控中心': '公共卫生/设施', '妇幼保健': '医疗卫生',
            
            # 教育文化相关关键词映射
            '教育': '教育文化', '学校': '教育文化', '教学': '教育文化', '校园': '教育文化',
            '教材': '教学设备', '培训': '教育文化', '学位': '教育文化', '学院': '教育文化',
            '大学': '教育文化', '中学': '教育文化', '小学': '教育文化', '幼儿园': '教育文化',
            
            # 政务行政相关关键词映射
            '政务': '政务行政', '行政': '政务行政', '政府': '政务行政', '机关': '政务行政',
            '公安': '政务行政', '司法': '政务行政', '财政': '政务行政', '税务': '政务行政',
            
            # 其他行业关键词映射...
            '环保': '环保市政', '市政': '环保市政', '农业': '农业农村', '农村': '农业农村',
            '交通': '交通水利', '水利': '交通水利', '科技': '科技产业', '产业': '科技产业',
            '公共安全': '公共安全', '安全': '公共安全'
        }
        
        # 基于实际表结构修正字段映射（只包含真实存在的字段）
        self.contact_field_mapping = {
            '联系人': ['purchaser_contact', 'agency_contact'],  # 移除不存在的contact_person
            '联系方式': ['purchaser_phone', 'agency_phone'],     # 移除不存在的contact_phone, contact_mobile
            '电话': ['purchaser_phone', 'agency_phone'],
            '地址': ['address']  # 保留实际存在的地址字段
        }
        
        # 采购意向表的联系人字段映射
        self.intention_contact_fields = {
            '联系人': [],  # 意向表没有联系人字段
            '联系方式': [], # 意向表没有联系方式字段
            '电话': [],
            '地址': []
        }

    def generate_intelligent_sql(self, user_message, schema_understanding, session_id):
        """使用AI智能生成SQL查询 - 基于实际表结构"""
        try:
            if not self.ai_processor.ai_client:
                return self.error_response_dict("AI服务不可用，无法生成智能SQL")
            
            # 深度分析用户意图，传入schema信息
            user_intent = self.analyze_user_intent(user_message, schema_understanding)
            logger.info(f"🎯 用户意图分析: {user_intent}")
            
            # 构建基于意图和实际表结构的精准提示词
            prompt = self.build_intent_based_prompt(user_message, schema_understanding, user_intent)
            
            logger.info("🤖 请求AI生成精准SQL查询...")
            
            response = self.ai_processor.ai_client.chat.completions.create(
                model=self.ai_processor.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            ai_content = response.choices[0].message.content
            logger.info(f"📝 AI原始响应: {ai_content[:200]}...")
            
            # 从AI响应中提取SQL语句
            sql_query = self.extract_sql_from_ai_response(ai_content)
            
            if not sql_query:
                logger.error("❌ AI未能生成有效的SQL语句")
                # 使用意图分析结果生成备用SQL（基于实际表结构）
                sql_query = self.generate_fallback_sql(user_intent)
                logger.info(f"🔄 使用备用SQL: {sql_query}")
            
            # 验证SQL安全性
            if not self.validate_sql_safety(sql_query):
                logger.error(f"❌ SQL安全验证失败: {sql_query}")
                return self.error_response_dict("生成的SQL语句不符合安全要求")
            
            # 验证SQL字段存在性
            if not self.validate_field_existence(sql_query, schema_understanding):
                logger.warning("⚠️ SQL包含不存在的字段，尝试修正...")
                sql_query = self.correct_missing_fields(sql_query, user_intent)
            
            logger.info(f"✅ 最终SQL: {sql_query}")
            
            return {
                'status': 'success',
                'sql_query': sql_query,
                'ai_explanation': ai_content,
                'tables_used': self.extract_tables_from_sql(sql_query),
                'user_intent': user_intent
            }
            
        except Exception as e:
            logger.error(f"❌ AI生成SQL失败: {e}")
            # 尝试使用意图分析生成基础SQL
            user_intent = self.analyze_user_intent(user_message, schema_understanding)
            fallback_sql = self.generate_fallback_sql(user_intent)
            return {
                'status': 'success',
                'sql_query': fallback_sql,
                'ai_explanation': 'AI服务异常，使用备用查询',
                'tables_used': ['procurement_notices_tag'],
                'user_intent': user_intent
            }

    def analyze_user_intent(self, user_message, schema_understanding=None):
        """深度分析用户查询意图 - 基于实际表结构"""
        user_message_lower = user_message.lower()
        
        intent_analysis = {
            'primary_industry': None,
            'secondary_category': None,
            'required_fields': [],
            'filters': {},
            'query_type': 'notices',  # 默认查询采购公告
            'keywords_found': [],
            'actual_contact_fields': []  # 实际可用的联系字段
        }
        
        # 分析行业关键词映射
        for keyword, tag_value in self.tag_keyword_mapping.items():
            if keyword in user_message_lower:
                intent_analysis['keywords_found'].append(keyword)
                
                # 判断是一级标签还是二级标签
                if '/' in tag_value:  # 二级标签，如"公共卫生/设施"
                    primary, secondary = tag_value.split('/')
                    intent_analysis['primary_industry'] = primary
                    intent_analysis['secondary_category'] = tag_value
                else:  # 一级标签
                    intent_analysis['primary_industry'] = tag_value
        
        # 判断查询类型并获取实际可用的联系字段
        if '意向' in user_message_lower:
            intent_analysis['query_type'] = 'intention'
            # 采购意向表没有联系人字段
            contact_mapping = self.intention_contact_fields
        else:
            intent_analysis['query_type'] = 'notices'
            contact_mapping = self.contact_field_mapping
        
        # 分析字段需求，只使用实际存在的字段
        for field_keyword, field_list in contact_mapping.items():
            if field_keyword in user_message_lower and field_list:
                intent_analysis['required_fields'].extend(field_list)
        
        # 去除重复字段
        intent_analysis['required_fields'] = list(set(intent_analysis['required_fields']))
        intent_analysis['actual_contact_fields'] = intent_analysis['required_fields'].copy()
        
        return intent_analysis

    def build_intent_based_prompt(self, user_message, schema_understanding, user_intent):
        """基于用户意图和实际表结构构建精准提示词"""
        schema_info = self.format_schema_for_ai(schema_understanding)
        
        # 基于意图生成针对性的说明
        intent_instructions = self.generate_intent_instructions(user_intent)
        
        # 根据查询类型确定可用字段
        if user_intent['query_type'] == 'intention':
            available_contact_fields = "采购意向表不包含联系人字段，请勿查询不存在的字段"
        else:
            available_contact_fields = ", ".join(user_intent['actual_contact_fields']) if user_intent['actual_contact_fields'] else "无联系人字段可用"
        
        prompt = f"""
您是一个专业的PostgreSQL专家。请根据用户的问题、明确的意图分析和数据库结构，生成精确的SQL查询。

# 用户的明确需求：
原始问题："{user_message}"

# 意图分析结果（重要）：
{intent_instructions}

# 关键约束条件（必须严格遵守）：
1. **表结构限制**：只能使用实际存在的字段，严禁使用不存在的字段
2. **联系人字段限制**：{available_contact_fields}
3. **查询类型**：{user_intent['query_type']}
4. **标签筛选**：必须包含 WHERE primary_tag = '{user_intent.get('primary_industry', '')}'

# 数据库实际表结构信息：
{schema_info}

# 字段存在性验证（重要）：
- procurement_notices_tag表实际联系人字段：purchaser_contact, purchaser_phone, agency_contact, agency_phone, address
- procurement_intention_tag表没有联系人相关字段

# 请直接返回精确的SQL查询语句（用```sql```包裹），必须确保所有字段都存在：
"""
        return prompt

    def generate_intent_instructions(self, user_intent):
        """生成意图分析说明"""
        instructions = []
        
        if user_intent['primary_industry']:
            instructions.append(f"- **行业标签**：查询应筛选 primary_tag = '{user_intent['primary_industry']}'")
        
        if user_intent['secondary_category']:
            instructions.append(f"- **二级分类**：查询应筛选 secondary_tag = '{user_intent['secondary_category']}'")
        
        if user_intent['actual_contact_fields']:
            fields_str = ", ".join(user_intent['actual_contact_fields'])
            instructions.append(f"- **可用联系字段**：SELECT应包含：{fields_str}")
        else:
            instructions.append("- **联系字段**：当前查询类型没有可用的联系人字段")
        
        if user_intent['query_type'] == 'notices':
            instructions.append("- **查询类型**：采购公告 (procurement_notices_tag)")
        elif user_intent['query_type'] == 'intention':
            instructions.append("- **查询类型**：采购意向 (procurement_intention_tag)")
        
        if user_intent['keywords_found']:
            instructions.append(f"- **识别关键词**：{', '.join(user_intent['keywords_found'])}")
        
        return "\n".join(instructions) if instructions else "未识别到明确的行业意图"

    def generate_fallback_sql(self, user_intent):
        """基于意图分析生成备用SQL - 使用实际存在的字段"""
        if user_intent['query_type'] == 'intention':
            # 采购意向表SQL
            base_table = "procurement_intention_tag"
            select_fields = [
                "title", "intention_project_name", "intention_budget_amount", 
                "intention_procurement_unit", "province", "city", "publish_time", 
                "primary_tag", "secondary_tag"
            ]
        else:
            # 采购公告表SQL
            base_table = "procurement_notices_tag"
            select_fields = [
                "notice_title", "project_name", "budget_amount", "purchaser_name",
                "province", "city", "publish_date", "primary_tag", "secondary_tag"
            ]
            # 添加实际存在的联系字段
            select_fields.extend(user_intent['actual_contact_fields'])
        
        # 构建WHERE条件
        where_conditions = []
        if user_intent['primary_industry']:
            where_conditions.append(f"primary_tag = '{user_intent['primary_industry']}'")
        
        if user_intent['secondary_category']:
            where_conditions.append(f"secondary_tag = '{user_intent['secondary_category']}'")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        sql = f"""
        SELECT {', '.join(select_fields)} 
        FROM {base_table} 
        {where_clause}
        ORDER BY publish_date DESC 
        LIMIT 100
        """
        
        return sql

    def validate_field_existence(self, sql_query, schema_understanding):
        """验证SQL中使用的字段是否实际存在"""
        tables_schema = schema_understanding.get('tables_schema', {})
        
        # 提取SQL中的字段名
        field_pattern = r'SELECT\s+(.*?)\s+FROM'
        field_match = re.search(field_pattern, sql_query, re.IGNORECASE | re.DOTALL)
        if not field_match:
            return True
        
        selected_fields = field_match.group(1)
        # 简单的字段提取逻辑
        fields = re.findall(r'(\w+)(?=\s*,|\s+FROM)', selected_fields)
        
        # 提取表名
        table_match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        if not table_match:
            return True
        
        table_name = table_match.group(1)
        if table_name not in tables_schema:
            return True
        
        # 获取表中实际存在的字段
        actual_fields = [col['column_name'] for col in tables_schema[table_name]]
        
        # 验证每个字段是否存在
        for field in fields:
            if field not in actual_fields:
                logger.warning(f"⚠️ 字段 '{field}' 在表 '{table_name}' 中不存在")
                return False
        
        return True

    def correct_missing_fields(self, sql_query, user_intent):
        """修正SQL中不存在的字段"""
        # 简单的字段替换修正
        corrections = {
            'contact_person': 'purchaser_contact',
            'contact_phone': 'purchaser_phone', 
            'contact_mobile': 'purchaser_phone'
        }
        
        for wrong_field, correct_field in corrections.items():
            if wrong_field in sql_query and correct_field not in sql_query:
                sql_query = sql_query.replace(wrong_field, correct_field)
                logger.info(f"🔄 修正字段: {wrong_field} -> {correct_field}")
        
        return sql_query

    def format_schema_for_ai(self, schema_understanding):
        """格式化schema信息供AI理解 - 突出关键字段"""
        tables_schema = schema_understanding.get('tables_schema', {})
        
        schema_text = "## 数据库表结构（关键字段）\n\n"
        
        # 重点显示标签表结构，突出联系人字段
        tag_tables = ['procurement_notices_tag', 'procurement_intention_tag']
        
        for table_name in tag_tables:
            if table_name in tables_schema:
                columns = tables_schema[table_name]
                schema_text += f"### 表: {table_name}\n"
                
                # 分类显示字段
                contact_fields = []
                basic_fields = []
                tag_fields = []
                
                for col in columns:
                    col_name = col['column_name']
                    if any(keyword in col_name for keyword in ['contact', 'phone', 'address']):
                        contact_fields.append(col_name)
                    elif any(keyword in col_name for keyword in ['tag']):
                        tag_fields.append(col_name)
                    else:
                        basic_fields.append(col_name)
                
                if contact_fields:
                    schema_text += f"- **联系人字段**: {', '.join(contact_fields)}\n"
                if basic_fields:
                    schema_text += f"- **基本信息字段**: {', '.join(basic_fields[:10])}...\n"
                if tag_fields:
                    schema_text += f"- **标签字段**: {', '.join(tag_fields)}\n"
                
                schema_text += "\n"
        
        return schema_text

    def extract_sql_from_ai_response(self, ai_content):
        """从AI响应中提取SQL语句"""
        # 尝试从代码块中提取SQL
        sql_match = re.search(r'```sql\n(.*?)\n```', ai_content, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        # 如果没有代码块，尝试直接提取SELECT语句
        select_match = re.search(r'(SELECT.*?)(?=;|$)', ai_content, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        return None

    def validate_sql_safety(self, sql_query):
        """验证SQL安全性"""
        sql_upper = sql_query.upper().strip()
        forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        
        if not sql_upper.startswith('SELECT'):
            return False
        
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False
        
        return True

    def extract_tables_from_sql(self, sql_query):
        """从SQL中提取使用的表"""
        tables = re.findall(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        tables.extend(re.findall(r'JOIN\s+(\w+)', sql_query, re.IGNORECASE))
        return list(set(tables))

    def error_response_dict(self, message):
        """错误响应"""
        return {
            'status': 'error',
            'message': f'<div class="alert alert-danger">{message}</div>'
        }
