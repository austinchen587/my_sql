# emall_purchasing/views/progress_services.py
import logging
import traceback
from django.conf import settings
from ..models import ProcurementPurchasing, ProcurementSupplier, ProcurementRemark, ClientContact, Supplier, SupplierCommodity # 👉 补充导入 Supplier 等
from .utils import build_client_contacts, build_suppliers_info, build_remarks_history, safe_json_loads
from .progress_handlers import ContactHandler, SupplierHandler, RemarkHandler
from .progress_handlers import get_username_from_request, get_user_role_from_request
import psycopg2  # 👉 [新增]
import json      # 👉 [新增]
from django.db import transaction # 👉 [新增]
from bidding.models import ProcurementCommodityResult

logger = logging.getLogger(__name__)


# 👉 [新增] 云端中央数据库配置
DB_CONFIG = {
    'host': '121.43.77.214',
    'port': 5432,
    'dbname': 'austinchen587_db',
    'user': 'austinchen587',
    'password': 'austinchen587'
}

class ProcurementProgressService:
    """采购进度管理服务"""

    # 👉 [新增核心方法] 从云端中央库把 AI 结果拉回本地变成真实的供应商！
    def _sync_ai_results_from_central(self, procurement_id, request):
        # 🛡️ 使用强力穿透函数获取发起刷新的真实 IP
        referer = request.META.get('HTTP_REFERER', '')
        # 👇 补上这 4 行！把 referer 变成 current_server
        if referer:
            current_server = referer.split('://')[-1].split(':')[0].split('/')[0]
        else:
            current_server = request.get_host().split(':')[0]
            
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # 👉 [修改] 查询增加了 brand_id, specifications, model_used
            cur.execute("""
                SELECT id, brand_id, item_name, specifications, selected_suppliers, selection_reason, model_used 
                FROM procurement_commodity_result 
                WHERE procurement_id = %s AND server_ip = %s AND status = 'completed'
            """, (str(procurement_id), current_server))
            
            rows = cur.fetchall()
            if not rows:
                return # 没有新结果，直接返回
                
            purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
            
            for row in rows:
                # 👉 [修改] 变量解包对应增加的字段
                result_id, brand_id, item_name, specifications, suppliers_json, reason, model_used = row
                
                if not suppliers_json: continue
                suppliers_data = json.loads(suppliers_json) if isinstance(suppliers_json, str) else suppliers_json
                
                with transaction.atomic():
                    # =========================================================
                    # 🌟 [新增] 同步底层 Result 表！这是给前端蓝框 (candidates) 供货的关键！
                    # =========================================================
                    ProcurementCommodityResult.objects.update_or_create(
                        brand_id=brand_id,
                        # 👉 [删除这一行] server_ip=current_server,
                        defaults={
                            'item_name': item_name,
                            'specifications': specifications or '',
                            'selected_suppliers': suppliers_json if isinstance(suppliers_json, str) else json.dumps(suppliers_json),
                            'selection_reason': reason or '',
                            'model_used': model_used or 'qwen3:8b',
                            'status': 'completed'
                        }
                    )

                    # 1. 遍历 AI 选出的 Top3 供应商，写入本地 Django 数据库 (这部分保持你原来的代码不变)
                    for idx, item in enumerate(suppliers_data):
                        # 创建供应商
                        supplier = Supplier.objects.create(
                            name=item.get('shop', '未知店铺'),
                            source=item.get('platform', 'AI智能寻源'),
                            contact="AI全网寻源推荐",
                            store_name=item.get('shop', '未知店铺'),
                            purchaser_created_by="AI_Auto",
                            purchaser_created_role="系统智能引擎"
                        )
                        # 创建商品明细
                        SupplierCommodity.objects.create(
                            supplier=supplier,
                            name=item_name, # 使用需求商品名
                            specification=item.get('reason', '')[:200], # 把 AI 的匹配证据写进规格里
                            price=item.get('price', 0),
                            quantity=1, 
                            product_url=item.get('detail_url', ''),
                            purchaser_created_by="AI_Auto",
                            purchaser_created_role="系统智能引擎"
                        )
                        # 关联到采购单 (默认不勾选，让人类来决定用不用)
                        ProcurementSupplier.objects.create(
                            procurement=purchasing_info,
                            supplier=supplier,
                            is_selected=False, 
                            purchaser_created_by="AI_Auto",
                            purchaser_created_role="系统智能引擎"
                        )
                    
                    # 2. 把 AI 的整体决策总结写进备注里！
                    if reason:
                        ProcurementRemark.objects.create(
                            purchasing=purchasing_info,
                            remark_content=f"🤖 [AI 寻源总结] {item_name}: {reason}",
                            created_by="AI_Auto",
                            created_role="系统智能引擎"
                        )
                        
                    # 3. 标记云端数据为已同步 (防止下次刷新重复拉取)
                    cur.execute("UPDATE procurement_commodity_result SET status = 'synced' WHERE id = %s", (result_id,))
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"☁️ [云端同步] 成功将 AI 寻源结果拉取并转化为本地供应商！")
        except Exception as e:
            logger.error(f"❌ [云端同步] 拉取 AI 结果失败: {e}")

    def update_procurement_info(self, procurement_id, request):
        """更新采购进度信息"""
        # 调试：打印所有可用的用户信息
        self._log_user_info(request)
        
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        
        data = safe_json_loads(request)
        if not data:
            raise ValueError('无效的JSON数据')
        
        logger.info(f"接收到的数据: {data}")
        
        # 更新基础信息
        self._update_basic_info(purchasing_info, data)
        
        # 更新联系人信息
        contact_handler = ContactHandler()
        contact_handler.update_contacts(purchasing_info, data.get('client_contacts', []), request)
        
        # 更新供应商选择状态
        supplier_handler = SupplierHandler()
        supplier_handler.update_supplier_selection(purchasing_info,data.get('supplier_selection', []), request)
        
        # 更新支付金额和物流单号
        self._update_payment_and_logistics(purchasing_info, data.get('suppliers_info', []), request)
        
        # 添加新备注
        remark_handler = RemarkHandler()
        remark_handler.add_new_remark(purchasing_info, data.get('new_remark'), request)
        
        current_remarks_count = purchasing_info.remarks_history.count()
        logger.info(f"当前采购项目的备注总数: {current_remarks_count}")
        
        return {
            'success': True, 
            'message': '采购信息更新成功',
            'remarks_count': current_remarks_count
        }
    
    def _update_payment_and_logistics(self, purchasing_info, suppliers_info, request):
        """更新支付金额和物流单号"""
        if not isinstance(suppliers_info, list):
            return
        
        # 获取当前用户信息
        current_user = get_username_from_request(request)
        current_role = get_user_role_from_request(request)
        
        updated_count = 0
        for supplier_data in suppliers_info:
            supplier_id = supplier_data.get('id')
            commodities = supplier_data.get('commodities', [])
            
            try:
                supplier = purchasing_info.suppliers.get(id=supplier_id)
                for commodity_data in commodities:
                    commodity_id = commodity_data.get('id')
                    payment_amount = commodity_data.get('payment_amount')
                    tracking_number = commodity_data.get('tracking_number')
                    
                    if commodity_id and (payment_amount is not None or tracking_number is not None):
                        commodity = supplier.commodities.get(id=commodity_id)
                        
                        # 设置用户信息用于审计
                        commodity._current_user = current_user
                        commodity._current_role = current_role
                        
                        # 更新字段
                        if payment_amount is not None:
                            commodity.payment_amount = payment_amount
                        if tracking_number is not None:
                            commodity.tracking_number = tracking_number
                        
                        commodity.save()  # 这会触发审计记录
                        updated_count += 1
                        
            except Exception as e:
                logger.error(f"更新商品支付/物流信息失败，supplier_id: {supplier_id}, 错误: {str(e)}")
                continue
        
        if updated_count > 0:
            logger.info(f"支付金额和物流单号更新完成，成功更新: {updated_count} 个商品")
    
    def get_procurement_progress(self, procurement_id, request=None):
        """获取采购进度信息"""
        
        # 🔥 在去本地库查之前，先去云端看一眼有没有 AI 刚做完的作业！
        if request:
            self._sync_ai_results_from_central(procurement_id, request)
            
        purchasing_info = ProcurementPurchasing.objects.select_related(
            'procurement'
        ).prefetch_related(
            'suppliers',
            'suppliers__commodities',
            'remarks_history',
            'client_contacts'
        ).get(procurement_id=procurement_id)
        
        total_budget = purchasing_info.get_total_budget()
        budget_total = float(total_budget) if total_budget else 0
        
        return {
            'procurement_id': procurement_id,
            'procurement_title': purchasing_info.procurement.project_title,
            'procurement_number': purchasing_info.procurement.project_number,
            'bidding_status': purchasing_info.bidding_status,
            'bidding_status_display': purchasing_info.get_bidding_status_display(),
            'client_contacts': build_client_contacts(purchasing_info),
            'total_budget': budget_total,
            'suppliers_info': build_suppliers_info(purchasing_info),
            'remarks_history': build_remarks_history(purchasing_info),
            'created_at': purchasing_info.created_at.isoformat() if purchasing_info.created_at else None,
            'updated_at': purchasing_info.updated_at.isoformat() if purchasing_info.updated_at else None,
            # 新增结算相关字段
            'winning_date': purchasing_info.winning_date.isoformat() if purchasing_info.winning_date else None,
            'settlement_date': purchasing_info.settlement_date.isoformat() if purchasing_info.settlement_date else None,
            'settlement_amount': float(purchasing_info.settlement_amount) if purchasing_info.settlement_amount else None,
        }
    
    def update_procurement_info(self, procurement_id, request):
        """更新采购进度信息"""
        # 调试：打印所有可用的用户信息
        self._log_user_info(request)
        
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        
        data = safe_json_loads(request)
        if not data:
            raise ValueError('无效的JSON数据')
        
        logger.info(f"接收到的数据: {data}")
        
        # 更新基础信息
        self._update_basic_info(purchasing_info, data)
        
        # 更新联系人信息
        contact_handler = ContactHandler()
        contact_handler.update_contacts(purchasing_info, data.get('client_contacts', []), request)
        
        # 更新供应商选择状态
        supplier_handler = SupplierHandler()
        supplier_handler.update_supplier_selection(purchasing_info, data.get('supplier_selection', []), request)
        
        # 添加新备注
        remark_handler = RemarkHandler()
        remark_handler.add_new_remark(purchasing_info, data.get('new_remark'), request)
        
        current_remarks_count = purchasing_info.remarks_history.count()
        logger.info(f"当前采购项目的备注总数: {current_remarks_count}")
        
        return {
            'success': True, 
            'message': '采购信息更新成功',
            'remarks_count': current_remarks_count
        }
    
    def _update_basic_info(self, purchasing_info, data):
        """更新基础信息"""
        if 'bidding_status' in data:
            purchasing_info.bidding_status = data['bidding_status']
            logger.info(f"更新竞标状态: {data['bidding_status']}")
        
        # 新增结算相关字段更新
        if 'winning_date' in data:
            purchasing_info.winning_date = data['winning_date'] or None
            logger.info(f"更新中标日期: {data['winning_date']}")
        
        if 'settlement_date' in data:
            purchasing_info.settlement_date = data['settlement_date'] or None
            logger.info(f"更新结算日期: {data['settlement_date']}")
        
        if 'settlement_amount' in data:
            purchasing_info.settlement_amount = data['settlement_amount'] or None
            logger.info(f"更新结算金额: {data['settlement_amount']}")
        
        purchasing_info.save()
        logger.info("基础信息更新成功")
    
    def _log_user_info(self, request):
        """记录用户信息用于调试"""
        logger.info(f"请求cookies: {dict(request.COOKIES)}")
        logger.info(f"session数据: {dict(request.session)}")
        if hasattr(request, 'user'):
            logger.info(f"用户对象: {request.user} (认证: {request.user.is_authenticated})")
            if request.user.is_authenticated:
                logger.info(f"认证用户: {request.user.username} ({request.user.id})")
