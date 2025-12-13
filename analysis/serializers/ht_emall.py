from rest_framework import serializers
from ..models.ht_emall import HtEmallRecord

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

