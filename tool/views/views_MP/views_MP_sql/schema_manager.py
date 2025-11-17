# tool/views/views_MP/views_MP_sql/schema_manager.py
import logging
import json
from django.db import connection

logger = logging.getLogger(__name__)

class SchemaManager:
    """数据库Schema管理模块"""
    
    def help_ai_understand_schema(self):
        """帮助AI理解数据库表结构 - 提供3个表的schema和1条样本数据"""
        try:
            # 获取三个核心表的schema信息
            tables_schema = self.get_tables_schema()
            
            # 获取每个表的1条样本数据
            sample_data = self.get_sample_data_from_tables()
            
            understanding_data = {
                'tables_schema': tables_schema,
                'sample_data': sample_data,
                'table_relationships': self.get_table_relationships()
            }
            
            logger.info(f"📊 数据库理解数据准备完成: {len(tables_schema)}个表结构, {len(sample_data)}个样本")
            return understanding_data
            
        except Exception as e:
            logger.error(f"❌ 获取数据库schema失败: {e}")
            return {}

    def get_tables_schema(self):
        """获取三个核心表的schema信息"""
        try:
            schema_query = """
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name IN ('base_procurement_info_new', 'procurement_notices', 'procurement_intention')
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
            
            tables = ['base_procurement_info_new', 'procurement_notices', 'procurement_intention']
            
            with connection.cursor() as cursor:
                for table in tables:
                    if table == 'procurement_notices':
                        # 显式指定需要的字段，排除content字段
                        sample_query = """
                        SELECT url, info_type, title, jurisdiction, bid_type, 
                            publish_time, crawl_time, created_time
                        FROM procurement_notices 
                        LIMIT 1
                        """
                    else:
                        sample_query = f"SELECT * FROM {table} LIMIT 1"
                    
                    cursor.execute(sample_query)
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        # 处理JSON字段
                        row_data = {}
                        for i, col_name in enumerate(columns):
                            value = row[i]
                            # 特殊处理可能的JSON字段
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
        """获取表之间的关系"""
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
                }
            ],
            'key_fields': {
                'base_procurement_info_new': ['url', 'title', 'jurisdiction', 'info_type', 'publish_time'],
                'procurement_notices': ['url', 'title', 'publish_time', 'procurement_method', 'budget_amount'],
                'procurement_intention': ['url', 'intention_budget_amount', 'intention_procurement_unit', 'intention_project_name']
            },
            'join_instructions': '所有表通过url字段进行LEFT JOIN关联，base_procurement_info_new是主表'
        }
        return relationships
