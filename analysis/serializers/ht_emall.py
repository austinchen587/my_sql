from rest_framework import serializers
from ..models.ht_emall import HtEmallRecord
from datetime import datetime, date

class HtEmallRecordSerializer(serializers.Serializer):
    """
    HT电商平台竞价记录序列化器
    用于序列化 HtEmallRecord 数据模型
    """
    status_category = serializers.CharField(allow_null=True, required=False, help_text="状态类别（源自 detail_status）")
    project_id = serializers.CharField(help_text="项目ID（唯一标识）")
    procurement_emall_id = serializers.CharField(allow_null=True, required=False, help_text="采购平台ID（pe.id）")
    procurement_project_name = serializers.CharField(allow_null=True, required=False, help_text="采购平台项目名称（pe.project_name）")
    expected_total_price = serializers.CharField(allow_null=True, required=False, help_text="期望总价（元）")
    response_total = serializers.CharField(allow_null=True, required=False, help_text="响应总额（元）")
    bid_start_time = serializers.DateTimeField(allow_null=True, required=False, help_text="竞价开始时间")
    bid_end_time = serializers.DateTimeField(allow_null=True, required=False, help_text="竞价结束时间")
    project_owner = serializers.CharField(allow_null=True, required=False, help_text="项目归属人")
    bidding_status = serializers.CharField(allow_null=True, required=False, help_text="竞标状态")
    
    # 修改这些字段为DateField
    winning_date = serializers.DateField(allow_null=True, required=False, help_text="中标日期")
    settlement_date = serializers.DateField(allow_null=True, required=False, help_text="结算日期")
    settlement_amount = serializers.FloatField(allow_null=True, required=False, help_text="结算金额")

    def to_representation(self, instance):
        """
        将数据模型转换为JSON可序列化的字典
        主要处理日期和时间字段
        """
        ret = super().to_representation(instance)
        
        # 确保所有datetime和date字段都被正确格式化
        for field in ['bid_start_time', 'bid_end_time', 'winning_date', 'settlement_date']:
            if field in ret and ret[field] is not None:
                if isinstance(ret[field], (datetime, date)):
                    ret[field] = ret[field].isoformat()
        return ret
