from rest_framework import serializers
from .models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing

class ProcurementEmallSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    purchasing_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcurementEmall
        fields = '__all__'
    
    def get_is_selected(self, obj):
        try:
            return obj.purchasing_info.is_selected
        except:
            return False
    
    def get_purchasing_info(self, obj):
        try:
            from emall_purchasing.serializers import ProcurementPurchasingSerializer
            purchasing_info = ProcurementPurchasing.objects.get(procurement=obj)
            return ProcurementPurchasingSerializer(purchasing_info).data
        except:
            return None
