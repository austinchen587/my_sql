from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# =============================================================================
# HT电商平台反拍（Reverse Auction）数据模型
# =============================================================================

@dataclass
class HtEmallReverseRecord:
    """
    电商反拍记录数据模型
    用于映射 ht_emall 表中 transaction_type = '反拍' 的数据结构
    """
    status_category: Optional[str]  # 状态类别（源自 detail_status）
    project_id: str  # 项目ID（唯一标识）
    project_name: str  # 项目名称
    expected_total_price: Optional[str]  # 期望总价（元）
    response_total: Optional[str]  # 响应总额（元）
    bid_start_time: Optional[datetime]  # 竞价开始时间
    bid_end_time: Optional[datetime]  # 竞价结束时间

    @staticmethod
    def from_row(row: dict) -> "HtEmallReverseRecord":
        """
        从数据库行记录构造 HtEmallReverseRecord 实例
        参数:
            row: PostgreSQL 查询返回的行字典，包含以下键:
                 status_category, project_id, project_name, expected_total_price, response_total, bid_start_time, bid_end_time
        返回:
            HtEmallReverseRecord 实例
        """
        def parse_dt(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(str(val))
            except Exception:
                return None

        return HtEmallReverseRecord(
            status_category=row.get("status_category"),
            project_id=str(row.get("project_id", "")),
            project_name=str(row.get("project_name", "")),
            expected_total_price=row.get("expected_total_price"),
            response_total=row.get("response_total"),
            bid_start_time=parse_dt(row.get("bid_start_time")),
            bid_end_time=parse_dt(row.get("bid_end_time")),
        )
