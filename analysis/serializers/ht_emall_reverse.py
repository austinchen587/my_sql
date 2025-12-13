from rest_framework import serializers
from ..models.ht_emall_reverse import HtEmallReverseRecord

class HtEmallReverseRecordSerializer(serializers.Serializer):
    """
    HT电商平台反拍记录序列化器
    用于序列化 HtEmallReverseRecord 数据模型
    """
    status_category = serializers.CharField(allow_null=True, required=False, help_text="状态类别（源自 detail_status）")
    project_id = serializers.CharField(help_text="项目ID（唯一标识）")
    project_name = serializers.CharField(help_text="项目名称")
    expected_total_price = serializers.CharField(allow_null=True, required=False, help_text="期望总价（元）")
    response_total = serializers.CharField(allow_null=True, required=False, help_text="响应总额（元）")
    bid_start_time = serializers.DateTimeField(allow_null=True, required=False, help_text="竞价开始时间")
    bid_end_time = serializers.DateTimeField(allow_null=True, required=False, help_text="竞价结束时间")
