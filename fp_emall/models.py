# my_sql/emall/models.py
from django.contrib.postgres.fields import ArrayField
from django.db import models

class ProcurementEmall(models.Model):
    fp_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 字符型字段（添加fp_前缀）
    fp_total_price_control = models.CharField(max_length=255, null=True, blank=True)
    fp_publish_date = models.CharField(max_length=255, null=True, blank=True)
    fp_purchasing_unit = models.CharField(max_length=255, null=True, blank=True)
    fp_url = models.CharField(max_length=255, null=True, blank=True)
    fp_project_title = models.CharField(max_length=255, null=True, blank=True)
    fp_project_number = models.CharField(max_length=255, null=True, blank=True)
    fp_quote_start_time = models.CharField(max_length=255, null=True, blank=True)
    fp_quote_end_time = models.CharField(max_length=255, null=True, blank=True)
    fp_region = models.CharField(max_length=255, null=True, blank=True)
    fp_project_name = models.CharField(max_length=255, null=True, blank=True)
    
    # 数组字段（添加fp_前缀）
    fp_commodity_names = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_parameter_requirements = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_purchase_quantities = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_control_amounts = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_suggested_brands = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_business_items = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_business_requirements = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_related_links = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    fp_download_files = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)

    class Meta:
        managed = False  # 保持False，因为表已存在
        db_table = 'procurement_fp_emall'  # 确保表名正确
