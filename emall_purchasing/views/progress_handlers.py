# emall_purchasing/views/progress_handlers.py
import logging
import urllib.parse
from ..models import ClientContact, ProcurementSupplier, ProcurementRemark
from .username_utils import decode_username_from_header, get_username_from_request, get_user_role_from_request

logger = logging.getLogger(__name__)

class ContactHandler:
    """联系人处理器"""
    
    def update_contacts(self, purchasing_info, contacts_data, request):
        """更新联系人信息 - 添加审计记录"""
        if not isinstance(contacts_data, list):
            logger.warning("联系人数据格式不正确，跳过更新")
            return
        
        logger.info(f"开始更新联系人信息，数量: {len(contacts_data)}")
        
        # 获取当前用户信息
        current_user = get_username_from_request(request)
        current_role = get_user_role_from_request(request)
        
        # 删除现有联系人
        purchasing_info.client_contacts.all().delete()
        
        # 添加新联系人并记录审计
        contact_count = 0
        for contact_data in contacts_data:
            if contact_data.get('name') or contact_data.get('contact_info'):
                ClientContact.objects.create(
                    purchasing=purchasing_info,
                    name=contact_data.get('name', ''),
                    contact_info=contact_data.get('contact_info', ''),
                    # 审计字段
                    purchaser_created_by=current_user,
                    purchaser_created_role=current_role,
                    purchaser_updated_by=current_user,
                    purchaser_updated_role=current_role
                )
                contact_count += 1
                logger.info(f"添加联系人: {contact_data.get('name')} - {contact_data.get('contact_info')}")
        
        logger.info(f"联系人更新完成，成功添加: {contact_count} 个联系人")



class SupplierHandler:
    """供应商处理器"""
    
    def update_supplier_selection(self, purchasing_info, supplier_selection_data, request):
        """更新供应商选择状态"""
        if not isinstance(supplier_selection_data, list):
            logger.warning("供应商选择数据格式不正确，跳过更新")
            return
        
        logger.info(f"开始更新供应商选择状态，数量: {len(supplier_selection_data)}")
        
        # 获取当前用户信息
        current_user = get_username_from_request(request)
        current_role = get_user_role_from_request(request)
        
        updated_count = 0
        for supplier_data in supplier_selection_data:
            try:
                supplier_id = supplier_data.get('supplier_id')
                is_selected = supplier_data.get('is_selected', False)
                
                if supplier_id is not None:
                    procurement_supplier = ProcurementSupplier.objects.get(
                        procurement=purchasing_info,
                        supplier_id=supplier_id
                    )
                    procurement_supplier.is_selected = bool(is_selected)
                    procurement_supplier.purchaser_updated_by = current_user
                    procurement_supplier.purchaser_updated_role = current_role
                    procurement_supplier.save()
                    updated_count += 1
                    logger.info(f"供应商 {supplier_id} 选择状态更新为: {is_selected}")
                else:
                    logger.warning("供应商ID为空，跳过")
            except ProcurementSupplier.DoesNotExist:
                logger.warning(f"供应商关系不存在，supplier_id: {supplier_id}")
                continue
            except Exception as e:
                logger.error(f"更新供应商选择状态失败，supplier_id: {supplier_id}, 错误: {str(e)}")
                continue
        
        logger.info(f"供应商选择状态更新完成，成功更新: {updated_count} 个")

class RemarkHandler:
    """备注处理器"""
    
    def add_new_remark(self, purchasing_info, remark_data, request):
        """添加新备注"""
        if not remark_data or not remark_data.get('remark_content'):
            logger.warning("备注内容为空，跳过创建备注")
            return
        
        remark_content = remark_data.get('remark_content')
        
        if remark_content and remark_content.strip():
            created_by = self._get_username_from_request(request)
            
            try:
                new_remark = ProcurementRemark.objects.create(
                    purchasing=purchasing_info,
                    remark_content=remark_content.strip(),
                    created_by=created_by
                )
                logger.info(f"成功添加新备注，备注ID: {new_remark.id}, 创建人: {created_by}")
            except Exception as e:
                logger.error(f"创建备注失败: {str(e)}")
                raise e
    
    def _get_username_from_request(self, request):
        """从请求中获取用户名"""
        created_by = "未知用户"
        
        # 1. 首先尝试从cookies获取username并解码
        username_from_cookie = request.COOKIES.get('username')
        if username_from_cookie:
            created_by = urllib.parse.unquote(username_from_cookie)
            logger.info(f"从cookie获取并解码用户名: {created_by}")
        
        # 2. 如果cookie中没有，尝试从session获取
        elif request.session.get('username'):
            created_by = request.session['username']
            logger.info(f"从session获取用户名: {created_by}")
        
        # 3. 如果session中没有，尝试从认证用户获取
        elif hasattr(request, 'user') and request.user.is_authenticated:
            created_by = request.user.username
            logger.info(f"从认证用户获取用户名: {created_by}")
        
        # 4. 如果都没有，尝试从请求头获取并解码
        elif request.META.get('HTTP_X_USERNAME'):
            encoded_username = request.META.get('HTTP_X_USERNAME')
            created_by = decode_username_from_header(encoded_username)
            logger.info(f"从请求头获取并解码用户名: {created_by}")
        
        else:
            logger.warning("无法获取用户信息，使用'未知用户'")
        
        return created_by
