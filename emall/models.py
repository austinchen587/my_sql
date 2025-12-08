#my_sql/emall/models.py
from django.contrib.postgres.fields import ArrayField  # 关键
from django.db import models

class ProcurementEmall(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 字符型字段
    total_price_control = models.CharField(max_length=255, null=True, blank=True)
    publish_date = models.CharField(max_length=255, null=True, blank=True)
    purchasing_unit = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    project_title = models.CharField(max_length=255, null=True, blank=True)
    project_number = models.CharField(max_length=255, null=True, blank=True)
    quote_start_time = models.CharField(max_length=255, null=True, blank=True)
    quote_end_time = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    
    # 数组字段（全部使用 ArrayField）
    commodity_names = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    parameter_requirements = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    purchase_quantities = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    control_amounts = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    suggested_brands = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    business_items = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    business_requirements = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    related_links = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)
    download_files = ArrayField(models.CharField(max_length=255, blank=True), null=True, blank=True)

    class Meta:
        managed = False  # 保持False，因为表已存在
        db_table = 'procurement_emall'
