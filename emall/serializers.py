from rest_framework import serializers
from .models import ProcurementEmall

class ProcurementEmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementEmall
        fields = '__all__'  # 或者显式列出所有需要的字段
