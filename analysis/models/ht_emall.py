from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# ============================================================================
# HT电商平台竞价数据模型
# ============================================================================

@dataclass
class HtEmallRecord:
    """
    电商竞价记录数据模型
    用于映射 ht_emall 表的完整数据结构
    """
    status_category: Optional[str]  # 状态类别（源自 detail_status）
    project_id: str  # 项目ID（唯一标识）
    project_name: str  # 项目名称
    expected_total_price: Optional[str]  # 期望总价（元）
    response_total: Optional[str]  # 响应总额（元）
    bid_start_time: Optional[datetime]  # 竞价开始时间
    bid_end_time: Optional[datetime]  # 竞价结束时间

    @staticmethod
    def from_row(row: dict) -> "HtEmallRecord":
        """
        从数据库行记录构造 HtEmallRecord 实例
        
        参数:
            row: PostgreSQL 查询返回的行字典，包含以下键:
                 project_id, project_name, expected_total_price, response_total,
                 bid_start_time, bid_end_time, transaction_type, detail_status
        
        返回:
            HtEmallRecord 实例
        """
        def parse_dt(val):
            """解析时间戳字符串为 datetime 对象"""
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            try:
                # 尝试通用的 ISO 8601 格式
                return datetime.fromisoformat(str(val))
            except Exception:
                return None

        return HtEmallRecord(
            status_category=row.get("status_category"),
            project_id=str(row.get("project_id", "")),
            project_name=str(row.get("project_name", "")),
            expected_total_price=row.get("expected_total_price"),
            response_total=row.get("response_total"),
            bid_start_time=parse_dt(row.get("bid_start_time")),
            bid_end_time=parse_dt(row.get("bid_end_time")),
        )

@dataclass
class HtEmallStatusView:
    """
    竞价状态统计视图模型
    
    针对状态分类查询优化的轻量级视图，包含:
    - 状态类别（从 detail_status 映射）
    - 项目核心字段（ID、名称）
    - 价格和时间字段
    
    适用于按详细状态分组统计的场景
    """
    status_category: Optional[str]  # 状态类别（源自 detail_status）
    project_id: str  # 项目ID
    project_name: str  # 项目名称
    expected_total_price: Optional[str]  # 期望总价（元）
    response_total: Optional[str]  # 响应总额（元）
    bid_start_time: Optional[datetime]  # 竞价开始时间
    bid_end_time: Optional[datetime]  # 竞价结束时间

    @staticmethod
    def from_row(row: dict) -> "HtEmallStatusView":
        """
        从数据库行记录构造 HtEmallStatusView 实例
        
        参数:
            row: PostgreSQL 查询返回的行字典
        
        返回:
            HtEmallStatusView 实例，detail_status 映射为 status_category
        """
        def parse_dt(val):
            """解析时间戳字符串为 datetime 对象"""
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(str(val))
            except Exception:
                return None

        return HtEmallStatusView(
            status_category=row.get("status_category"),
            project_id=str(row.get("project_id", "")),
            project_name=str(row.get("project_name", "")),
            expected_total_price=row.get("expected_total_price"),
            response_total=row.get("response_total"),
            bid_start_time=parse_dt(row.get("bid_start_time")),
            bid_end_time=parse_dt(row.get("bid_end_time")),
        )
