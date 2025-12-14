# my_sql/emall_purchasing/models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
import re  # 导入正则表达式模块
from emall.models import ProcurementEmall
from django.utils import timezone
from authentication.models import UserProfile  # 导入UserProfile模型

class Supplier(models.Model):
    """供应商模型"""
    name = models.CharField(max_length=255, verbose_name='供应商名称')
    source = models.CharField(max_length=255, null=True, blank=True,verbose_name='获取渠道')
    contact = models.CharField(max_length=255, null=True, blank=True, verbose_name='联系方式')
    store_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='店铺名称')
    
    # 新增供应商审计字段
    purchaser_created_by = models.CharField(max_length=100, verbose_name='采购创建人', default='未知用户')
    purchaser_created_role = models.CharField(max_length=20, verbose_name='采购创建人角色', default='unassigned')
    purchaser_created_at = models.DateTimeField(auto_now_add=True, verbose_name='采购创建时间')
    purchaser_updated_by = models.CharField(max_length=100, verbose_name='采购更新人', null=True, blank=True)
    purchaser_updated_role = models.CharField(max_length=20, verbose_name='采购更新人角色', null=True, blank=True)
    purchaser_updated_at = models.DateTimeField(auto_now=True, verbose_name='采购更新时间')
    
    class Meta:
        db_table = 'procurement_suppliers'  # 改为复数形式，避免冲突
        verbose_name = '供应商'
        verbose_name_plural = '供应商'

    def __str__(self):
        return self.name

class PaymentAuditLog(models.Model):
    commodity = models.ForeignKey('SupplierCommodity', on_delete=models.CASCADE, related_name='payment_audits')
    old_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    changed_by = models.CharField(max_length=100, verbose_name='操作人')
    changed_role = models.CharField(max_length=20, verbose_name='操作人角色')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_audit_log'
        verbose_name = '支付金额审计'
        verbose_name_plural = '支付金额审计'

class LogisticsAuditLog(models.Model):
    commodity = models.ForeignKey('SupplierCommodity', on_delete=models.CASCADE, related_name='logistics_audits')
    old_value = models.CharField(max_length=100, null=True, blank=True)
    new_value = models.CharField(max_length=100, null=True, blank=True)
    changed_by = models.CharField(max_length=100, verbose_name='操作人')
    changed_role = models.CharField(max_length=20, verbose_name='操作人角色')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'logistics_audit_log'
        verbose_name = '物流单号审计'
        verbose_name_plural = '物流单号审计'

class SupplierCommodity(models.Model):
    """供应商商品信息"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='commodities')
    name = models.CharField(max_length=255, verbose_name='商品名稱')
    specification = models.TextField(null=True, blank=True, verbose_name='商品规格')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='价格')
    quantity = models.IntegerField(verbose_name='数量')
    product_url = models.URLField(max_length=500, null=True, blank=True, verbose_name='产品链接')
    
    # 新增支付和物流字段
    payment_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='支付金额'
    )
    tracking_number = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name='物流单号'
    )
    
    # 新增供应商商品审计字段
    purchaser_created_by = models.CharField(max_length=100, verbose_name='采购创建人', default='未知用户')
    purchaser_created_role = models.CharField(max_length=20, verbose_name='采购创建人角色', default='unassigned')
    purchaser_created_at = models.DateTimeField(auto_now_add=True, verbose_name='采购创建时间')
    
    class Meta:
        db_table = 'supplier_commodities'  # 改为复数形式
        verbose_name = '供应商商品'
        verbose_name_plural = '供应商商品'

    def __str__(self):
        return f"{self.supplier.name} - {self.name}"

# 假设你的模型类似如下
# BIDDING_STATUS_CHOICES = [
#     ('not_started', '未开始'),
#     ('in_progress', '进行中'),
#     ('successful', '竞标成功'),
#     ('failed', '竞标失败'),
#     ('cancelled', '已取消'),
# ]

class ProcurementPurchasing(models.Model):
    # 竞标状态选项
    BIDDING_STATUS_CHOICES = [
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('successful', '竞标成功'),
        ('failed', '竞标失败'),
        ('cancelled', '已取消'),
    ]
    # 添加项目归属人字段
    project_owner = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='项目归属人',
        default='未分配'
    )
    
    procurement = models.OneToOneField(
        ProcurementEmall, 
        on_delete=models.CASCADE, 
        related_name='purchasing_info'
    )
    is_selected = models.BooleanField(default=False, verbose_name='是否选择采购')
    selected_at = models.DateTimeField(null=True, blank=True, verbose_name='选择时间')
    unselected_at = models.DateTimeField(null=True,blank=True, verbose_name='取消选择时间')
    
    # 竞标状态
    bidding_status = models.CharField(
        max_length=20, 
        choices=BIDDING_STATUS_CHOICES, 
        default='not_started',
        verbose_name='竞标状态'
    )
    
    # 关联供应商（支持多个供应商）
    suppliers = models.ManyToManyField(Supplier, through='ProcurementSupplier', related_name='procurements')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchasing'
        verbose_name = '采购进度管理'
        verbose_name_plural = '采购进度管理'

    def __str__(self):
        return f"{self.procurement.project_title} - 采购信息"
    
    def save(self, *args, **kwargs):
        """重写save方法自动记录选择状态变化时间"""
        if self.pk:  # 只对已存在的实例
            try:
                old_instance = ProcurementPurchasing.objects.get(pk=self.pk)
                if old_instance.is_selected != self.is_selected:
                    if self.is_selected:  # 从 False → True
                        self.selected_at = timezone.now()
                        self.unselected_at = None
                    else:  # 从 True → False
                        self.unselected_at = timezone.now()
                        self.selected_at = None
            except ProcurementPurchasing.DoesNotExist:
                pass
        elif self.is_selected:  # 新实例且为True
            self.selected_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_total_budget(self):
        """获取项目总预算"""
        if self.procurement.total_price_control:
            # 使用之前的金额转换逻辑
            return self.convert_price_to_number(self.procurement.total_price_control)
        return 0
    
    def convert_price_to_number(self, price_str):
        """金额转换方法 - 修正版本"""
        if not price_str or price_str == '-': 
            return 0
        try:
            # 使用Python的字符串替换方法
            clean_str = price_str.replace(' ', '').replace(',', '')
            
            # 使用Python的正则表达式
            if '万元' in clean_str and '元万元' not in clean_str:
                match = re.search(r'(\d+\.?\d*)\s*万元', price_str)
                if match:
                    return float(match.group(1)) * 10000
            
            if '元万元' in clean_str:
                match = re.search(r'(\d+\.?\d*)', clean_str)
                if match:
                    return float(match.group(1))
            
            if '元' in clean_str and '万元' not in clean_str:
                match = re.search(r'(\d+\.?\d*)\s*元', price_str)
                if match:
                    return float(match.group(1))
            
            # 如果没有单位，尝试直接解析为数字
            try:
                return float(clean_str)
            except ValueError:
                return 0
                
        except Exception as e:
            print(f"金额转换错误: {e}")
            return 0
    
    def get_suppliers_info(self):
        """获取供应商信息（基于所有被选中供应商的总报价计算利润）"""
        suppliers_info = []
        
        # 计算所有被选中供应商的总报价
        total_selected_quote = 0
        selected_suppliers = []
        
        # 先遍历所有供应商关系，计算总报价
        for procurement_supplier in self.procurementsupplier_set.all():
            supplier = procurement_supplier.supplier
            total_quote = procurement_supplier.get_total_quote()
            
            if procurement_supplier.is_selected:
                total_selected_quote += total_quote
                selected_suppliers.append(supplier.id)
        
        # 计算总利润
        budget = self.get_total_budget()
        total_profit = budget - total_selected_quote if budget > 0 else 0
        
        # 再次遍历，构建供应商信息
        for procurement_supplier in self.procurementsupplier_set.all():
            supplier = procurement_supplier.supplier
            supplier_quote = procurement_supplier.get_total_quote()
            
            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'total_quote': float(supplier_quote) if supplier_quote else 0,
                'is_selected': procurement_supplier.is_selected,
                'commodities': [
                    {
                        'name': commodity.name,
                        'specification': commodity.specification or '',
                        'price': float(commodity.price) if commodity.price else 0,
                        'quantity': commodity.quantity or 0,
                        'payment_amount': float(commodity.payment_amount) if commodity.payment_amount else 0,
                        'tracking_number': commodity.tracking_number or ''
                    }
                    for commodity in supplier.commodities.all()
                ]
            }
            
            # 利润计算：如果是被选中的供应商，显示总利润；否则利润为0
            if procurement_supplier.is_selected:
                supplier_data['profit'] = float(total_profit) if total_profit > 0 else 0
            else:
                supplier_data['profit'] = 0
                
            suppliers_info.append(supplier_data)
        
        return suppliers_info

class ProcurementSupplier(models.Model):
    """采购项目与供应商关联表"""
    procurement = models.ForeignKey(ProcurementPurchasing, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False, verbose_name='是否选择该供应商')
    
    # 新增最终报价字段及专属审计字段
    final_negotiated_quote = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='最终协商报价'
    )
    final_quote_modified_by = models.CharField(
        max_length=100, 
        verbose_name='最终报价修改人', 
        null=True, 
        blank=True
    )
    final_quote_modified_role = models.CharField(
        max_length=20, 
        verbose_name='最终报价修改人角色', 
        null=True, 
        blank=True
    )
    final_quote_modified_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='最终报价修改时间'
    )
    
    # 新增供应商关系审计字段
    purchaser_created_by = models.CharField(max_length=100, verbose_name='采购创建人', default='未知用户')
    purchaser_created_role = models.CharField(max_length=20, verbose_name='采购创建人角色', default='unassigned')
    purchaser_created_at = models.DateTimeField(auto_now_add=True, verbose_name='采购创建时间')
    purchaser_updated_by = models.CharField(max_length=100, verbose_name='采购更新人', null=True, blank=True)
    purchaser_updated_role = models.CharField(max_length=20, verbose_name='采购更新人角色', null=True, blank=True)
    purchaser_updated_at = models.DateTimeField(auto_now=True, verbose_name='采购更新时间')
    
    class Meta:
        db_table = 'procurement_supplier_relation'  # 改为不同的表名
        unique_together = ('procurement', 'supplier')
        verbose_name = '采购供应商关系'
        verbose_name_plural = '采购供应商关系'
    
    def get_total_quote(self):
        """获取该供应商的总报价"""
        total = 0
        for commodity in self.supplier.commodities.all():
            if commodity.price and commodity.quantity:
                total += commodity.price * commodity.quantity
        return total

class ProcurementRemark(models.Model):
    """采购备注历史记录"""
    purchasing = models.ForeignKey(
        ProcurementPurchasing, 
        on_delete=models.CASCADE, 
        related_name='remarks_history'
    )
    remark_content = models.TextField(verbose_name='备注内容')
    created_by = models.CharField(max_length=100, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # 添加 auto_now=True
    
    class Meta:
        db_table = 'procurement_purchasing_remarks'
        verbose_name = '采购备注记录'
        verbose_name_plural = '采购备注记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.purchasing.procurement.project_title} - 备注"

class ClientContact(models.Model):
    """甲方联系人模型"""
    purchasing = models.ForeignKey(
        ProcurementPurchasing, 
        on_delete=models.CASCADE, 
        related_name='client_contacts'
    )
    name = models.CharField(max_length=255, verbose_name='联系人姓名')
    contact_info = models.CharField(max_length=255, verbose_name='联系方式')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'procurement_client_contacts'
        verbose_name = '甲方联系人'
        verbose_name_plural = '甲方联系人'
    
    def __str__(self):
        return f"{self.name} - {self.contact_info}"

class UnifiedProcurementRemark(models.Model):
    """统一的采购项目备注系统"""
    procurement = models.ForeignKey(
        'emall.ProcurementEmall',
        on_delete=models.CASCADE,
        related_name='unified_remarks'
    )
    remark_content = models.TextField(verbose_name='备注内容')
    created_by = models.CharField(max_length=100, verbose_name='创建人')
    
    # 可选：关联采购进度（如果存在）
    purchasing = models.ForeignKey(
        'ProcurementPurchasing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchasing_remarks'
    )
    
    remark_type = models.CharField(
        max_length=20,
        choices=[
            ('general', '普通备注'),
            ('purchasing', '采购进度备注'),
            ('client', '客户沟通备注')
        ],
        default='general',
        verbose_name='备注类型'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'unified_procurement_remarks'
        verbose_name = '统一采购备注'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.procurement.project_title} - {self.get_remark_type_display()} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @classmethod
    def get_latest_remark(cls, procurement_id):
        """获取项目的最新备注"""
        try:
            return cls.objects.filter(procurement_id=procurement_id).first()
        except cls.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        # 获取操作人和角色（需通过上下文传递，伪代码如下）
        user = getattr(self, '_current_user', None)
        role = getattr(self, '_current_role', None)
        # 获取项目状态和is_selected
        purchasing = None
        if hasattr(self, 'supplier') and hasattr(self.supplier, 'procurements'):
            purchasing = self.supplier.procurements.filter(bidding_status='successful', procurementsupplier__is_selected=True).first()
        # 仅在项目竞标成功且供应商被选中时允许填写/变更
        if purchasing:
            # 检查支付金额变动
            if self.pk:
                old = SupplierCommodity.objects.get(pk=self.pk)
                if old.payment_amount != self.payment_amount:
                    if user and role:
                        PaymentAuditLog.objects.create(
                            commodity=self,
                            old_value=old.payment_amount,
                            new_value=self.payment_amount,
                            changed_by=user,
                            changed_role=role
                        )
                if old.tracking_number != self.tracking_number:
                    if user and role:
                        LogisticsAuditLog.objects.create(
                            commodity=self,
                            old_value=old.tracking_number,
                            new_value=self.tracking_number,
                            changed_by=user,
                            changed_role=role
                        )
            else:
                # 首次填写，仅允许特定角色
                if user and role and role in ['supplier_manager', 'admin']:
                    if self.payment_amount is not None:
                        PaymentAuditLog.objects.create(
                            commodity=self,
                            old_value=None,
                            new_value=self.payment_amount,
                            changed_by=user,
                            changed_role=role
                        )
                    if self.tracking_number:
                        LogisticsAuditLog.objects.create(
                            commodity=self,
                            old_value=None,
                            new_value=self.tracking_number,
                            changed_by=user,
                            changed_role=role
                        )
                elif (self.payment_amount or self.tracking_number):
                    raise PermissionError("只有供应商经理或管理员可以首次填写支付和物流字段")
        else:
            # 非竞标成功或未选中供应商时，不允许填写
            if self.payment_amount or self.tracking_number:
                raise PermissionError("只有竞标成功且被选中的供应商才能填写支付和物流字段")
        super().save(*args, **kwargs)
