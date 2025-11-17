# tool/views/views_MP/views_MP_sql/schema_manager.py
import logging
import json
from django.db import connection

logger = logging.getLogger(__name__)

class SchemaManager:
    """数据库Schema管理模块 - 增强版，支持标签表"""
    
    def help_ai_understand_schema(self):
        """帮助AI理解数据库表结构 - 包含标签表"""
        try:
            # 获取所有相关表的schema信息
            tables_schema = self.get_all_tables_schema()
            
            # 获取每个表的1条样本数据
            sample_data = self.get_sample_data_from_tables()
            
            understanding_data = {
                'tables_schema': tables_schema,
                'sample_data': sample_data,
                'table_relationships': self.get_table_relationships(),
                'tag_hierarchy': self.get_tag_hierarchy_info()
            }
            
            logger.info(f"📊 数据库理解数据准备完成: {len(tables_schema)}个表结构, {len(sample_data)}个样本")
            return understanding_data
            
        except Exception as e:
            logger.error(f"❌ 获取数据库schema失败: {e}")
            return {}

    def get_all_tables_schema(self):
        """获取所有相关表的schema信息"""
        try:
            schema_query = """
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name IN (
                'base_procurement_info_new', 
                'procurement_notices', 
                'procurement_intention',
                'procurement_notices_tag',
                'procurement_intention_tag'
            )
            ORDER BY table_name, ordinal_position
            """
            
            with connection.cursor() as cursor:
                cursor.execute(schema_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # 按表名组织schema信息
                tables_schema = {}
                for row in rows:
                    table_name = row[0]
                    if table_name not in tables_schema:
                        tables_schema[table_name] = []
                    
                    tables_schema[table_name].append({
                        'column_name': row[1],
                        'data_type': row[2],
                        'is_nullable': row[3],
                        'column_default': row[4]
                    })
                
                logger.info(f"📋 获取到表结构: {list(tables_schema.keys())}")
                return tables_schema
                
        except Exception as e:
            logger.error(f"❌ 获取表schema失败: {e}")
            return {}

    def get_sample_data_from_tables(self):
        """从每个表获取1条样本数据"""
        try:
            sample_data = {}
            
            tables = [
                'base_procurement_info_new', 
                'procurement_notices', 
                'procurement_intention',
                'procurement_notices_tag',
                'procurement_intention_tag'
            ]
            
            with connection.cursor() as cursor:
                for table in tables:
                    if table == 'procurement_notices':
                        sample_query = """
                        SELECT url, info_type, title, jurisdiction, bid_type, 
                            publish_time, crawl_time, created_time
                        FROM procurement_notices 
                        LIMIT 1
                        """
                    elif table == 'procurement_notices_tag':
                        sample_query = """
                        SELECT notice_title, project_name, budget_amount, purchaser_name,
                            province, city, primary_tag, secondary_tag, tertiary_tags
                        FROM procurement_notices_tag 
                        LIMIT 1
                        """
                    elif table == 'procurement_intention_tag':
                        sample_query = """
                        SELECT title, intention_project_name, intention_budget_amount,
                            intention_procurement_unit, primary_tag, secondary_tag, tertiary_tags, confidence
                        FROM procurement_intention_tag 
                        LIMIT 1
                        """
                    else:
                        sample_query = f"SELECT * FROM {table} LIMIT 1"
                    
                    cursor.execute(sample_query)
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        # 处理JSON字段和特殊数据类型
                        row_data = {}
                        for i, col_name in enumerate(columns):
                            value = row[i]
                            # 特殊处理JSON字段
                            if value and isinstance(value, str) and value.strip().startswith('{'):
                                try:
                                    row_data[col_name] = json.loads(value)
                                except:
                                    row_data[col_name] = value
                            else:
                                row_data[col_name] = value
                        
                        sample_data[table] = {
                            'columns': columns,
                            'sample_row': row_data
                        }
                        logger.info(f"📄 获取表 {table} 的样本数据，列数: {len(columns)}")
            
            return sample_data
            
        except Exception as e:
            logger.error(f"❌ 获取样本数据失败: {e}")
            return {}

    def get_table_relationships(self):
        """获取表之间的关系 - 包含标签表关联"""
        relationships = {
            'relationships': [
                {
                    'table1': 'base_procurement_info_new',
                    'table2': 'procurement_notices', 
                    'join_key': 'url',
                    'relationship': '一对一或一对多，通过url字段关联'
                },
                {
                    'table1': 'base_procurement_info_new',
                    'table2': 'procurement_intention',
                    'join_key': 'url', 
                    'relationship': '一对一或一对多，通过url字段关联'
                },
                {
                    'table1': 'procurement_notices',
                    'table2': 'procurement_notices_tag',
                    'join_key': 'url',
                    'relationship': '一对一关系，通过url字段关联，标签表包含详细分类信息'
                },
                {
                    'table1': 'procurement_intention',
                    'table2': 'procurement_intention_tag',
                    'join_key': 'url',
                    'relationship': '一对一关系，通过url字段关联，标签表包含详细分类信息'
                }
            ],
            'key_fields': {
                'procurement_notices_tag': [
                    'notice_title', 'project_name', 'budget_amount', 'purchaser_name',
                    'province', 'city', 'publish_date', 'primary_tag', 'secondary_tag', 'tertiary_tags'
                ],
                'procurement_intention_tag': [
                    'title', 'intention_project_name', 'intention_budget_amount',
                    'intention_procurement_unit', 'primary_tag', 'secondary_tag', 'tertiary_tags', 'confidence'
                ]
            },
            'join_instructions': '''
            推荐使用LEFT JOIN关联标签表以获取详细分类信息：
            - 采购公告：LEFT JOIN procurement_notices_tag ON procurement_notices.url = procurement_notices_tag.url
            - 采购意向：LEFT JOIN procurement_intention_tag ON procurement_intention.url = procurement_intention_tag.url
            '''
        }
        return relationships

    def get_tag_hierarchy_info(self):
        """获取标签层次结构信息"""
        return {
            'tag_structure': {
                '一级标签': ['政务行政', '教育文化', '医疗卫生', '公共安全', '环保市政', '农业农村', '交通水利', '科技产业'],
                '二级标签': {
                    '政务行政': ['办公设备', '信息化建设', '后勤服务'],
                    '教育文化': ['学校建设', '教学设备', '文化保护'],
                    '医疗卫生': ['医疗设备', '医院服务', '公共卫生/设施'],
                    '公共安全': ['警务装备', '应急管理'],
                    '环保市政': ['环境治理', '市政工程', '园林绿化'],
                    '农业农村': ['农业工程', '农村基建'],
                    '交通水利': ['水利工程', '交通设施'],
                    '科技产业': ['科研设备', '产业服务']
                },
                '查询提示': '''
                标签查询建议：
                1. 可以按一级标签筛选：WHERE primary_tag = '教育文化'
                2. 可以按二级标签筛选：WHERE secondary_tag = '教学设备' 
                3. 可以组合查询：WHERE primary_tag = '医疗卫生' AND secondary_tag = '医疗设备'
                4. 三级标签存储在tertiary_tags JSON字段中，可以使用JSON查询
                '''
            }
        }
